
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
MEASURE_DAYS = 7*24*60*60*1000


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
    print '\nthe top N(6) recommend reviwer:{}'.format(TopNName)
    
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
def getAlias(reviewers):
    alias = []
    for reviewer in reviewers:
        name = reviewer.split('-')[-1]
        name = name.lower()
        alias.append(name)
    return alias
def recommendMeasure(PRchoseReviewer,TopNName,db,collName_result,engineerNumber):

    nowTime = int(time.time())
    PRr=set(getAlias(PRchoseReviewer))
    RCr=set(getAlias(TopNName))

    precision = float(len(PRr&RCr))/len(RCr)
    recall = float(len(PRr&RCr))/len(PRr)
        
    findCondition ={'time':{'$gte':nowTime-MEASURE_DAYS}}   
    docs = db.findInfo(collName_result,findCondition)
    allrecommendReviewer = set()
    missNumber = 0.0
    allPRRNumber = 0.0
    if docs: 
        for doc in docs:

            greatOnes = doc['greatOnes']
            PRReviewer = doc['PRReviewer']
            recommendReviewer = doc['recommendReviewer']

            missNumber+=len(set(greatOnes)-set(PRReviewer))
      
            allPRRNumber+=len(PRReviewer)
            allrecommendReviewer = set(recommendReviewer)| allrecommendReviewer
    coverage = float(len(allrecommendReviewer))/engineerNumber

    degree = missNumber/allPRRNumber
    return precision,recall,coverage,degree
    
def savePredictResult(db,collName_result,review_id,PRchoseReviewer,author,TopNName,greatOnes):
    PRReviewer = PRchoseReviewer
    PRReviewer.append(author)
 
    condition = {"id": review_id};
    docs = db.findInfo(collName_result,condition)
    authorlist=[]
    authorlist.append(author)
    predictresult={'id':review_id,'time':nowTime,'PRReviewer':getAlias(PRReviewer),'author':getAlias(authorlist),'recommendReviewer':getAlias(TopNName),'greatOnes':getAlias(greatOnes)}

    if docs:
        db.updateOne(collName_result,condition,predictresult)
    else:
        db.insertOne(collName_result,predictresult)
    

if __name__=="__main__":
    
    import os
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
    nameList = [engineer['name']+'-'+engineer['alias'] for engineer in engineerList]

    frameClassification = DataFrame(0, columns=nameList, index=PRfileList)
    frameFeatures = DataFrame(0, columns=nameList, index=PRfileList)
    for filename in PRfileList:
        for engineer in engineerList:
            para_features = fparser.get_features(str(nowTime),filename, engineer)
            predicted_LogisticRegression, predicted_DTC, predicted_SVM, \
            predicted_Random_Forest, predicted_AdaBoost, predicted_Bayes = ML_model.reviwerPredict(para_features)
            frameFeatures[engineer['name']+'-'+engineer['alias']][filename] =  str(para_features)[1:-1]
            frameClassification[engineer['name']+'-'+engineer['alias']][filename] = predicted_LogisticRegression[0]+predicted_DTC[0]+predicted_SVM[0]+predicted_Random_Forest[0]+predicted_AdaBoost[0]+predicted_Bayes[0]
    
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
    greatOnes=[]
    for engineerName in TopNName:
        isgreatOne = False
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
                        isgreatOne = True
                        print level
        if isgreatOne:
            greatOnes.append(engineerName)
    # save predict result to db:
    savePredictResult(db,database['collName_result'],args.review_id,PRchoseReviewer,author,TopNName,greatOnes)

    precision,recall,coverage,degree = recommendMeasure(PRchoseReviewer,TopNName,db,database['collName_result'],len(engineerList))
    
    print '\nRecommend Metrics:'
    print "Precision:{}%".format(precision*100)
    print "Recall:{}%".format(recall*100)
    print "Novelty per 7 days::{}%".format(degree*100)
    print "Coverage per 7 days:{}%".format(coverage*100)
    