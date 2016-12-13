#ReviewerRecommend
ReviewerRecommend is to give the recommended reviewer list, from the file changes of a certain review request. 

#Design Principles
The purpose of recommendation system is, to recommend items for a certain user.  
The general concepts are:    
1. Item based recommendation:  
User Mike likes item A, and item A & B are similar, so that to recommend item B to the user Mike.  
2. User based recommendation:  
User Mike and user Jim are similar, and Jim likes item C, so that to recommend item C to user Mike.  
3. Feature based recommendation:  
User Mike, Jim, Kevin have features Xa, Xb, Xc and liked items A, B, C.   
We can train the model Y=f(X), where Xa, Xb, Xc are X and A, B, C are Y.   
So that, for user Tom with feature Xd, we can use the model f to give the item recommendation.  

ReviewerRecommend is the recommendation based on features.  
Here,  
(1) "User" is the "File changes of a certain review request";  
(2) "Item" is the "Recommended reviewer list";   
(3) "Features" are X1, X2, ..., X6, where:  
 X1 -> reciprocal of interval of the last code change;  
 X2 -> times of changes;  
 X3 -> average code size for each change;  
 X4 -> reciprocal of interval of the last code review;  
 X5 -> times of review;  
 X6 -> average number of comments raised for each review.  
  
6 typical machine learning algorithms are used to train the model, including Logistic Regression, Decision Tree, Support Vector Machine, Random Forest, AdaBoost, and Naive Bayes.   

#Getting started
1. Software needed to install:  
(1) Anaconda: Python machine learning environment  
Anaconda2-4.2.0-Windows-x86_64  
(2) mongoDB: Data base to store code change and review data  
mongodb-win32-x86_64  

2. Data source  
(1) The code change base is a local Git repo from GitHub or BitBucket.  
(2) The review base is Pull Requests (PR) records in BitBucket.  
  
3. Settings  
(1) Configurate config.ini with your specialized settings.   
  
#How the project is run
1. Capture review and code change data from Butbucket and Git repo.  
python bitbucket_api.py  
python git_api.py  

2. Generate training and test data set with feature vectors, and train model with the typical 6 machine learning algorithms.  
python ML_model.py  

3. For the review with id xxx, use the model generated in step 2 to recommend reviewers with top N priority and recommendation reasons.  
python predict_reviewer.py -id xxx  

#Output 
1. The top N recommended reviewer list:  
E.g. ['Jerry', 'Jim', 'Mike']  

2. Recommend reason:  
For each recommended reviewer with file, the reason would be given.  
If the person's code change or review contribution is more than average, a "great" word would be given.   

3. Recommend Metrics:  
Precision:  true true num / predicted num (N)  
Recall:  true true num / really chosen num  
Novelty: Num of "great" that was not chosen by review author originally / total number of reviewers.  
Coverage per 7 days:  Within the latest 7 days, num of recommended reviewers / total number of reviewers in the pool.   

#Authors
Github id ZhangJifei with zhangxiaofancd@163.com  
Github id huangrurong with huangrurong0124@163.com  
