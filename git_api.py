import re,os
import subprocess

#---------------------------------------------------------------------------------------------------------------
# define fileParser class 
#----------------------------------------------------------------------------------------------------------------
class gitCommitParser(object):
    def __init__(self,db,collName_git,tagPattern='',submodule='',ignoreAuthor=''):
        self.db = db
        self.collName_git = collName_git
        self.tagPattern=tagPattern
        log_pattern= r'''commit\s(?P<commit_id>\w{40})\nAuthor:.*<(?P<author_email>.+)>\nDate:\s*(?P<commit_date>\d+)\s'''
        size_pattern = r".+\|\s(?P<size>\d+).+"
        self.log_pattern = re.compile(log_pattern, re.IGNORECASE|re.MULTILINE)
        self.size_pattern = re.compile(size_pattern, re.IGNORECASE|re.MULTILINE)
        self.submoduleFile = submodule
        self.commitID = "NULL"
        self.date = "NULL"
        self.author = "NULL"
        self.ignoreAuthor = ignoreAuthor
        
    def set_ignore_author(self,author):
        self.ignoreAuthor.append(author)
        
    def remove_ignore_author(self,author):
        self.ignoreAuthor.remove(author)
        
    def getTagList(self,pattern):
        gitCmd = "git tag --list {}".format(pattern)
        print gitCmd
        tagList = subprocess.check_output(gitCmd.split(), stderr=subprocess.STDOUT)
        return tagList.split()
    
    def checkTagExistInDB(self,tag):
        isExist = False;
        condition = {"releaseTag": tag};
        docs = self.db.findInfo(self.collName_git,condition)
        if docs:
            isExist = True;
        return isExist
    def parserTagList(self):
        
        for pattern in self.tagPattern:
            tagList = self.getTagList(pattern)
            for index in range(len(tagList)-1):
                tag = tagList[index+1];
                if self.checkTagExistInDB(tag):
                    continue;
                print tag
                self.getCommitInfo(tag)
                if self.commitID == "NULL":
                    continue;
                fileList = self.getChangeFiles(tag,tagList[index])
                self.getChangeSize(tag,tagList[index],fileList)
                
    def getChangeSize(self,tag,lasttag,fileList):
        
        #changes=[];
        for filename in fileList:
            cSize = 0
            gitCmd = "git diff --stat {} {} {}".format(tag,lasttag,filename)
            print gitCmd
            try:
                output = subprocess.check_output(gitCmd.split(), stderr=subprocess.STDOUT)
                if not output:
                    continue;
                cSize = int(self.size_pattern.search(output).group(1))
            except Exception, e:
                continue
            #change = {"filename":filename,'changeSize':cSize}
            #changes.append(change)
            dbData = {"releaseTag":tag,'commit_id':self.commitID,'date': self.date,'author':self.author,'changeSize':cSize,"filename":filename}
            print dbData
            self.db.insertOne(self.collName_git, dbData)        
                #changeSizeInfo =
    def getChangeFiles(self,tag,lastTag):
        gitCmd = "git diff --name-only {} {}".format(tag,lastTag)
        print gitCmd
        fileList=[]
        fileLists = subprocess.check_output(gitCmd.split(), stderr=subprocess.STDOUT)
        for filename in fileLists.split():
            filename=filename.replace('\\','/')
            name = filename.split('/')[0]
            if name in self.submoduleFile:
                continue;
            fileList.append(filename)
        return fileList
    def getCommitInfo(self,tag):
        commitid = "NULL"
        date = "NULL"
        author = "NULL"
        gitCmd = "git log --date=raw --max-count=10 --skip=1 {}".format(tag)
        print gitCmd
        loghistory = subprocess.check_output(gitCmd.split(), stderr=subprocess.STDOUT)
        matches = [m for m in self.log_pattern.finditer(loghistory)]
        lastDate = 0 
        for match in matches:
            try:
                tempMail = match.groupdict()['author_email']
                tempDate = match.groupdict()['commit_date']
                author = tempMail.split('@')[0].lower()
                if tempDate > lastDate and not (author in self.ignoreAuthor) :
                    commitid = match.groupdict()['commit_id']
           
                    date = tempDate
                    lastDate = tempDate
            except Exception, e:
                continue
        
        self.commitID=commitid
        self.date = date
        self.author = author
        
if __name__=="__main__":
    
    from mongodb import mongodb
    from configReader import configReader     
        
    cReader = configReader('config.ini')
    gitConfig = cReader.get_git()
    database = cReader.get_db()
    
    os.chdir(gitConfig['path'])
    
    gitCmd = "git fetch"
    print gitCmd
    try:
        output = subprocess.check_output(gitCmd.split(), stderr=subprocess.STDOUT)
    except Exception, e:
        print "fetch fail!!"
        
    db = mongodb(database['dbName'])
    gitParser = gitCommitParser(db,database['collName_git'],gitConfig['tagpattern'],gitConfig['submodule'],gitConfig['ignoreauthor'])
    gitParser.parserTagList();
    
    
    
    
    
    