
import ConfigParser

class configReader(object):
    def __init__(self,path):
        self.path = path
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(self.path)
    def get_bitbucket(self):
        bitbucket={};
        bitbucket['password'] = self.cf.get('BITBUCKET','PASSWORD')
        bitbucket['username'] = self.cf.get('BITBUCKET','USERNAME')
        bitbucket['url'] = self.cf.get('BITBUCKET','URL')
        bitbucket['project'] = self.cf.get('BITBUCKET','PROJ')
        bitbucket['repo'] = self.cf.get('BITBUCKET','REPO')
        return bitbucket
        
    def get_db(self):
        database={}
        database['dbName'] = self.cf.get('DATABASE','DB_NAME')
        database['collName_PR'] = self.cf.get('DATABASE','collName_PR')
        database['collName_PR2'] = self.cf.get('DATABASE','collName_PR2')
        database['collName_git'] = self.cf.get('DATABASE','collName_git')
        
        return database
    def get_git(self):
        gitconfig={}
        gitconfig['submodule'] = self.cf.get('GIT','SUBMODULE').split(',')
        gitconfig['tagpattern'] = self.cf.get('GIT','TAGPATTERN').split(',')
        gitconfig['ignoreauthor'] = self.cf.get('GIT','IGNOREAUTHOR').split(',')
        gitconfig['path'] = self.cf.get('GIT','PATH')
        return gitconfig

    def get_engineerList(self):
        engineerList =[];
        nameList = self.cf.options("ENGINEERLIST")
        for name in nameList:
            alias = self.cf.get('ENGINEERLIST',name) 
            engineer = {'name':name,'alias':alias}
            engineerList.append(engineer)
        return engineerList
