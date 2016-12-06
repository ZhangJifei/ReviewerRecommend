
import argparse
import sys
import StringIO
import time
from pandas import Series, DataFrame
import pandas as pd

from bitbucket_api import Bitbucket
from configReader import configReader
from mongodb import mongodb
from featuresParser import featuresParser
from ML_model import machineLearn

MAX_REVIEWER_NUM = 6


def process_argument():
    parser = argparse.ArgumentParser(description="description:predict reviewer", epilog=" %(prog)s description end")
    parser.add_argument('-id',dest="review_id")
    args = parser.parse_args()
    return args

def printrawData(review_id,PRfileList,TopNName,PRchoseReviewer,author):
    print 'PR id :{}'.format(review_id)
    print '\nfile change list:'
    for filename in PRfileList: 
        print filename
    print '\nPR author:{}'.format(author)
    print '\nPR reviewer:'
    for name in PRchoseReviewer:
        print name
    print ' '
    print 'the top N recommend reviewer:{}'.format(TopNName)
def recommendLevel(frameFeatures,code_average,reviwer_average):
    code_level =''
    reviwer_level = ''
    code_temp = float(frameFeatures[0])*float(frameFeatures[1])*float(frameFeatures[2]) if float(frameFeatures[0])>0 else 0
    reviwer_temp = float(frameFeatures[3])*float(frameFeatures[4]) if float(frameFeatures[3])>0 else 0
    if code_temp:
        code_level = "great coder" if code_temp >code_average else "good coder"
    if reviwer_temp: 
        reviwer_level = "great reviewer" if reviwer_temp >reviwer_average else "good reviewer"
    return [code_level,reviwer_level]

if __name__=="__main__":
    
    import os
    emailpath=os.path.abspath(sys.path[0]+'/utilities')
    sys.path.append(emailpath)

    args = process_argument()

    #--------------------
    #load config
    #--------------------
    cReader = configReader('config.ini')
    bitbucket = cReader.get_bitbucket()
    database = cReader.get_db()
    engineerList = cReader.get_engineerList()
    
    #--------------------
    #init db,bitbucket,featureparser
    #--------------------
    db = mongodb(database['dbName'])
    bitbucketapi = Bitbucket(bitbucket['url'],bitbucket['username'],bitbucket['password'],bitbucket['project'],bitbucket['repo'],db)
    PRfileList = bitbucketapi.get_file_changes(args.review_id)
    
    nowTime = int(time.time())
    print nowTime
    fparser = featuresParser(db,collName_git=database['collName_git'],collName_PR2=database['collName_PR2'])
    #--------------------
    #load machine learning model
    #--------------------
    ML_model = machineLearn()
    ML_model.load_model()

    #--------------------
    #predict
    #--------------------
    nameList = [engineer['name'] for engineer in engineerList]

    frameClassification = DataFrame(0, columns=nameList, index=PRfileList)
    frameFeatures = DataFrame(0, columns=nameList, index=PRfileList)
    for filename in PRfileList:
        for engineer in engineerList:
            para_features = fparser.get_features(str(nowTime),filename, engineer)
            predicted_LogisticRegression, predicted_DTC, predicted_SVM, \
            predicted_Random_Forest, predicted_AdaBoost, predicted_Bayes = ML_model.reviwerPredict(para_features)
            frameFeatures[engineer['name']][filename] =  str(para_features)[1:-1]
            frameClassification[engineer['name']][filename] = predicted_LogisticRegression[0]+predicted_DTC[0]+predicted_SVM[0]+predicted_Random_Forest[0]+predicted_AdaBoost[0]+predicted_Bayes[0]
    
    #--------------------
    #get top N
    #--------------------
    v1 = frameClassification.sum()
    TopN = v1.sort_values(ascending = False).head(MAX_REVIEWER_NUM)

    # remove engineers with 0 score
    TopNName = []
    for i in range(0, len(TopN)):
        if TopN[i] > 0:
            TopNName += [TopN.index[i]]
    print TopNName
    
    #stdout = sys.stdout
    #sys.stdout = stdOutfile = StringIO.StringIO()
    PRchoseReviewer = bitbucketapi.get_reviewers(args.review_id)
    author = bitbucketapi.get_author(args.review_id)

    printrawData(args.review_id,PRfileList,TopNName,PRchoseReviewer,author)
 
    
    # print recommendation reason
    for engineerName in TopNName:
        print "\nWe recommend reviewer: ", engineerName
        print "It's the right person for below files:"
        for i in range(0,len(frameFeatures.index)):
            if (frameClassification[engineerName][i] != 0):
                print frameFeatures.index[i]
                print frameFeatures[engineerName][i]
                fF = frameFeatures[engineerName][i].split(',')
        
                levels=recommendLevel(fF,127.36,1.59)
        
                for level in levels:
                    if level:
                        print level

						
