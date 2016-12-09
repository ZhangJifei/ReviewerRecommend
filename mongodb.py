from pymongo import MongoClient

#---------------------------------------------------------------------------------------------------------------
# define database class 
#----------------------------------------------------------------------------------------------------------------  
class mongodb():
    def __init__(self,dbName):
        self.dbClient = MongoClient()
        self.db = self.dbClient[dbName]
        #self.fs = gridfs.GridFS(self.db)

    def insertOne(self, collName, data):
        (self.db)[collName].insert_one(data)

        return True
    def updateOne(self,collName,condition,updateData):
         (self.db)[collName].update_one(condition,{'$set': updateData}, upsert=False)
    def getLastCommit(self, collName,key):
        if collName not in self.db.collection_names() or 0 == (self.db)[collName].count:
            return None

        return (self.db)[collName].find_one(sort=[(key, -1)])
    
    def findInfo(self, collName,*query):
        docs = []
      
        if collName not in self.db.collection_names() or 0 == (self.db)[collName].count:
            return None
        if len(query) == 0:
            docs=(self.db)[collName].find()
        elif len(query) == 1:
            docs=(self.db)[collName].find(query[0])
        elif len(query) ==2:
            docs=(self.db)[collName].find(query[0],sort=[query[1]])
        return [doc for doc in docs]
    
    def updatePR(self,collName,commit,PRinfo):
        (self.db)[collName].update_one({'commitId': commit},{'$set': {'PR': PRinfo}}, upsert=False)