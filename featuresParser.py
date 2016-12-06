
import datetime
from mongodb import mongodb

class featuresParser(object):
    def __init__(self,db='',collName_git='',collName_PR='',collName_PR2=''):
        self.db = db
        self.collName_git=collName_git
        self.collName_PR=collName_PR
        self.collName_PR2=collName_PR2
        
    def get_features(self,createTime,filename,engineer):
        #X1: last time modify the file
        X1 =0;
        X2 =0;
        X3 =0;
        X4 =0;
        X5 =0;
        X6 =0;
        condition = {'date': {'$lte': createTime},'$or': [{'author': engineer['name'].lower()}, {'author': engineer['alias'].lower()}],'filename':filename};
        sortType=('date',-1)
        
        #print condition
        changes = self.db.findInfo(self.collName_git,condition,sortType)

        if changes:
            #print changes
            lastTime = changes[0]['date']
            #print datetime.datetime.fromtimestamp(int(createTime))
            modifydays = (datetime.datetime.fromtimestamp(int(createTime))-datetime.datetime.fromtimestamp(int(lastTime))).days
            #print modifydays
            X1 = 1 if modifydays < 90 else 90.0/modifydays
            #X2: times of modify
            X2 = len(changes)
            #X3: sum(csize)*X2/X2
            sumSize =0
            for change in changes:
                sumSize = sumSize + change['changeSize']
            X3 = float(sumSize)/X2

        condition = {'createDate': {'$lte': createTime},'$or': [{'reviewer': engineer['name'].lower()}, {'reviewer': engineer['alias'].lower()}],'changes':{'$in':[filename]}};
        sortType=('createDate',-1)
        changes = self.db.findInfo(self.collName_PR2,condition,sortType)
        if changes:   
            lastTime = changes[0]['createDate']
            #print datetime.datetime.fromtimestamp(int(createTime))
            modifydays = (datetime.datetime.fromtimestamp(int(createTime))-datetime.datetime.fromtimestamp(int(lastTime))).days
            X4 = 1 if modifydays < 90 else 90.0/modifydays
            #X5: times of as reviwer
            X5 = len(changes)
            #X6: sum(csize)*X2/X2
            sumComments =0
            for change in changes:
                sumComments = sumComments + len(change['comments'])
            X6 = float(sumComments)/X5
        para = [X1,X2,X3,X4,X5,X6]
        return para
        
    def PRgitSetData(self,engineerList):
        #get PR info
        Yset =[]
        Xset=[]
        mPRs = self.db.findInfo(self.collName_PR)
        for PR in mPRs:
            reviwerList = []
            fileList=[]
            targetList=[]
            XnList = []
            createTime = str(PR['createDate'])
            commitID = PR['commit_id']
            print PR['id'],PR['commit_id'],createTime
            #reviwer List
            for reviwer in PR['reviewers']:
                name = reviwer['name'].split('@')[0].lower()
                reviwerList.append(name)
            author = PR['author'].split('@')[0].lower()
            reviwerList.append(author)
            #file List
            #condition = {'commit_id': commitID};
            #changes = self.db.findInfo(collName_git,condition)
            #for change in changes:
                #fileList.append(change['filename'])
            fileList=PR['changes']

            for engineer in engineerList:
                choose =0 
                #print engineer['name']
                #Y
                if (engineer['name'].lower() in reviwerList) or (engineer['alias'] in reviwerList):
                    choose =1 
                
                #X1,X2,X3
                for filename in fileList:                   
                    para = self.get_features(createTime,filename,engineer)
                    Yset.append(choose)
                    Xset.append(para)
                    #trainingData.append(onetrainingData)
        #self.saveTrainSet(Yset,Xset)
        return Yset,Xset 