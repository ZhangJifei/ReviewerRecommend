import httplib,urllib,json
from base64 import b64encode

EXCLUDE_ID_BITBUCKETCOMMENT_1 = ''
EXCLUDE_ID_BITBUCKETCOMMENT_2 = ''

#  ======== 
#  = URLs = 
#  ======== 

URLS = { 
    'POST_COMMENTS':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests/%(PRid)s/comments',
    'GET_PULLREQUESTS':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests/%(PRid)s',
    'GET_ACTIVITIES':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests/%(PRid)s/activities',
    'GET_CHANGES':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests/%(PRid)s/changes',
    'GET_MERGEDPR':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests?state=MERGED&limit=100&start=%(start)s',
    'GET_PARTICIPANTS':'/rest/api/1.0/projects/%(projects)s/repos/%(repo_slug)s/pull-requests/%(PRid)s/participants'
}





class Bitbucket(object):
    """ This class lets you interact with the bitbucket public API. """ 
    def __init__(self, baseUrl,username='', password='',project='', repo_name_or_slug='',db='',collName_PR='',collName_PR2=''): 
        self.baseurl = baseUrl
        self.username = username 
        self.password = password 
        self.repo_slug = repo_name_or_slug 
        self.project = project
        self.URLS = URLS 
        self.db = db
        self.db
        userAndPass = "%s:%s" % (username,password)
        self.userAndPass = b64encode(userAndPass).decode("ascii")
        self.collName_PR = collName_PR
        self.collName_PR2 = collName_PR2
        
    def urlPath(self, action, **kwargs): 
        """ Construct and return the URL for a specific API service. """ 
        return self.URLS[action] % kwargs 
    def urlRequest(self,action,path,body=''):
        """action is POST or GET""" 
        if body:
            payload = json.dumps({'text': body})
        else:
            payload=json.dumps({})
        headers = { 'Authorization' : 'Basic %s' %  self.userAndPass,'Content-type': 'application/json'} 
        conn = httplib.HTTPConnection(self.baseurl)
        conn.request(action, path, payload, headers)
        res = conn.getresponse()
        #conn.close() 
        return json.loads(res.read())
        
    def postComment(self,PRId,text):
        path = self.urlPath('POST_COMMENTS',projects=self.project,repo_slug=self.repo_slug,PRid=PRId)
        self.urlRequest('POST',path,text)
        
    def get_PRInfo(self,PRId):
        
        path = self.urlPath('GET_PULLREQUESTS',projects=self.project,repo_slug=self.repo_slug,PRid=PRId)
        res = self.urlRequest('GET',path)
        
        return res
    
    def get_PRActivities(self,PRId):
        
        path = self.urlPath('GET_ACTIVITIES',projects=self.project,repo_slug=self.repo_slug,PRid=PRId)
        res = self.urlRequest('GET',path)
        return res
    
    def get_Changes(self,PRId):
        
        path = self.urlPath('GET_CHANGES',projects=self.project,repo_slug=self.repo_slug,PRid=PRId)
        res = self.urlRequest('GET',path)
        return res
    
    def get_MergedPR(self,start=0):
        
        path = self.urlPath('GET_MERGEDPR',projects=self.project,repo_slug=self.repo_slug,start=start)
        res = self.urlRequest('GET',path)
        return res
        
    def get_AllMergedPR(self):
    
        start = 0
        isLastPage = 'false'
        allMPR=[];
        while isLastPage == 'false':
            mPRs=self.get_MergedPR(start)
            allMPR.extend(mPRs['values'])
            isLastPage = mPRs['isLastPage']
            start = mPRs["start"]+mPRs["size"]
        return allMPR
    
    def get_PRpartici(self,PRId):
        
        path = self.urlPath('GET_PARTICIPANTS',projects=self.project,repo_slug=self.repo_slug,PRid=PRId)
        res = self.urlRequest('GET',path)
        return res
    
    def get_file_changes(self,PRId):
        
        PRfileList=[]
        changes = self.get_Changes(PRId)

        for change in changes['values']:
            filename = change['path']['toString']
            PRfileList.append(filename)
        return PRfileList
    def get_reviewers(self,PRId):
        
        participants = self.get_PRpartici(PRId)

        PRReviewersList = []
        for partici in participants["values"]:
            if partici['role'] == "REVIEWER":
                PRReviewersList.append(partici["user"]["displayName"]) 
        return PRReviewersList
    def get_author(self,PRId):
        
        participants = self.get_PRpartici(PRId)

        author = ''
        for partici in participants["values"]:
            if partici['role'] == "AUTHOR":
                author=partici["user"]["displayName"]
        return author

    def get_createdDate(self,PRId):
        PRinfo = self.get_PRInfo(PRId)    
        PRCreatedDate = str(PRinfo['createdDate']/1000)
        return PRCreatedDate
    
    def update_PRinfo_todb(self,mPR):
   
        PRId = mPR['id']
        if self.checkPRExistInDB(PRId):
            return
        print "PR:{}".format(PRId)
        latestCommit = mPR["fromRef"]['latestCommit'] 
        createDate = str(mPR['createdDate']/1000)
        reviewers=[]
        temp={}
        
        for reviewer in mPR['reviewers']:
            if  reviewer['role']!="REVIEWER":
                continue;
            temp[reviewer['user']['emailAddress']]=[];
            
        activities = self.get_PRActivities(PRId)
        for active in activities['values']:
            user = active['user']
            name = active['user']['name']
            if name!=EXCLUDE_ID_BITBUCKETCOMMENT_1 and name!=EXCLUDE_ID_BITBUCKETCOMMENT_2 and active['action'] == "COMMENTED":
                comment = active['comment']
                tempComents = {'text':comment['text'],'file':''}
                if comment.has_key('commentAnchor'):
                    tempComents['file']= comment['commentAnchor']['path']
           
                #try:
                print user['emailAddress']
                try:
                    temp[user['emailAddress']].append(tempComents)
                except Exception, e:
                    print "this reviwer not exist:"+user['emailAddress']
                    continue
        #changes
        fileList=[]
        author = mPR["author"]["user"]["emailAddress"]
        changes = self.get_Changes(PRId)
        for change in changes['values']:
            fileList.append(change['path']['toString'])
        #update the DB
        for key in temp:
            tempreviewer={'name':key,'comments':temp[key]}
            reviewers.append(tempreviewer)
            PRdata={'id':PRId,'commit_id':latestCommit,'createDate':createDate,'author':author,'reviewer':key.split('@')[0].lower(),'comments':temp[key],'changes':fileList}
            self.db.insertOne(self.collName_PR2,PRdata)
        author = mPR["author"]["user"]["emailAddress"]
        PRdata= {'id':PRId,'commit_id':latestCommit,'createDate':createDate,'author':author,'reviewer':author.split('@')[0].lower(),'comments':[],'changes':fileList}
        self.db.insertOne(self.collName_PR2,PRdata)
        #reviewers.append(author)
        PRdata={'id':PRId,'commit_id':latestCommit,'createDate':createDate,'author':author,'reviewers':reviewers,'changes':fileList}
        print PRdata
        db.insertOne(self.collName_PR,PRdata)
        
    def checkPRExistInDB(self,PRId):
        isExist = False;

        condition = {'id':PRId};
        docs = self.db.findInfo(self.collName_PR,condition)
        if docs:
            isExist = True;
        return isExist
    
if __name__=="__main__":
    
    from mongodb import mongodb
    from configReader import configReader
    
    cReader = configReader('config.ini')
    bitbucket = cReader.get_bitbucket()
    database = cReader.get_db()
    engineerList = cReader.get_engineerList()
    
    
    db = mongodb(database['dbName'])
    bitbucketapi = Bitbucket(bitbucket['url'],bitbucket['username'],bitbucket['password'],bitbucket['project'],bitbucket['repo'],db,database['collName_PR'],database['collName_PR2'])
    
    AllmPR=bitbucketapi.get_AllMergedPR()
    #go through every PR
    for mPR in AllmPR:                           
        bitbucketapi.update_PRinfo_todb(mPR)
    




 
    

    

    

    
