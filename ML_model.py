
from sklearn import metrics
from sklearn.naive_bayes import GaussianNB
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn import linear_model
from sklearn.cross_validation import train_test_split
from sklearn import linear_model
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn import decomposition
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.externals import joblib
import os,re,sys
import subprocess
from pymongo import MongoClient
import datetime
import math

import StringIO

# ---------------------------------------------------------------------------------------------------------------
# feature_matrix_PRGIT: features vector
# class_list_PRGIT: Classification vector for the features vector
# ----------------------------------------------------------------------------------------------------------------
#from ML_data import feature_matrix_PRGIT,class_list_PRGIT
#from featuresParser import featuresParser
#from feature_classification import get_features_for_train, get_classification_for_train


# ---------------------------------------------------------------------------------------------------------------
# machine Learn class
# ----------------------------------------------------------------------------------------------------------------
class machineLearn(object):
    def __init__(self, x='', y=''):
        self.x = x;
        self.y = y;
        self.split_size = 0.1
        self.model_LogisticRegression = "NULL"
        self.model_DTC = "NULL"
        self.model_SVM = "NULL"
        self.model_Random_Forest = "NULL"
        self.model_AdaBoost = "NULL"
        self.model_Bayes = "NULL"

    def setSplitSize(self, size):
        self.split_size = size

    def classifyModelTrain(self, model):
        # Cross-validation
        X_train, X_test, y_train, y_test = train_test_split(self.x, self.y, test_size=self.split_size, random_state=0)

        tmp_time_1 = datetime.datetime.now().microsecond / 1000
        f = model.fit(X_train, y_train)
        tmp_time_2 = datetime.datetime.now().microsecond / 1000
        print "Model train consume", (tmp_time_2 - tmp_time_1), "millisecond"

        s = model.score(X_train, y_train)
        print model
        print 'model score : {}'.format(s)
        # results = model.predict_proba(X_test)
        # print results
        # Predict Output

        tmp_time_1 = datetime.datetime.now().microsecond / 1000
        predicted = model.predict(X_test)
        tmp_time_2 = datetime.datetime.now().microsecond / 1000
        print "Model predict consume", (tmp_time_2 - tmp_time_1), "millisecond"

        # print metrics.matthews_corrcoef(y_test, predicted)
        print metrics.classification_report(y_test, predicted)
        # print metrics.confusion_matrix(y_test, predicted)
        return model

    def train(self):
        print "(1).Logistic Regression Classifier:"
        model = LogisticRegression()
        self.model_LogisticRegression = self.classifyModelTrain(model)

        print "(2).Decision Tree Classifier:"
        model = tree.DecisionTreeClassifier(
            criterion='gini')  # for classification, here you can change the algorithm as gini or entropy (information gain) by default it is gini
        self.model_DTC = self.classifyModelTrain(model)

        print "(3).support vector machine:"
        model = svm.SVC(kernel='rbf', probability=True, gamma=0.4)
        self.model_SVM = self.classifyModelTrain(model)

        print "(4).Random Forest Classifier: "
        model = RandomForestClassifier()
        self.model_Random_Forest = self.classifyModelTrain(model)

        print "(5).AdaBoost Classifier:"
        model = GradientBoostingClassifier(n_estimators=100, max_depth=1, random_state=0)
        self.model_AdaBoost = self.classifyModelTrain(model)

        print "(6).Naive Bayes Classifier:"
        model = GaussianNB()
        self.model_Bayes = self.classifyModelTrain(model)
    def save_model(self):
        if self.model_LogisticRegression:
            joblib.dump(self.model_LogisticRegression, "LogisticRegression_model.m")
        if self.model_DTC :
            joblib.dump(self.model_DTC, "DTC_model.m")
        if self.model_SVM :
            joblib.dump(self.model_SVM, "SVM_model.m")
        if self.model_Random_Forest:
            joblib.dump(self.model_Random_Forest, "Random_Forest_model.m")
        if self.model_AdaBoost:
            joblib.dump(self.model_AdaBoost, "AdaBoost_model.m")
        if self.model_Bayes:
            joblib.dump(self.model_Bayes, "Bayes_model.m")
    def load_model(self):
        if os.path.exists("LogisticRegression_model.m"):
            self.model_LogisticRegression = joblib.load("LogisticRegression_model.m")
        if os.path.exists("DTC_model.m"):
            self.model_DTC = joblib.load("DTC_model.m")
        if os.path.exists("SVM_model.m"):
            self.model_SVM = joblib.load("SVM_model.m")
        if os.path.exists("Random_Forest_model.m"):
            self.model_Random_Forest = joblib.load("Random_Forest_model.m")
        if os.path.exists("AdaBoost_model.m"):
            self.model_AdaBoost = joblib.load("AdaBoost_model.m")
        if os.path.exists("Bayes_model.m"):
            self.model_Bayes = joblib.load("Bayes_model.m")
        

    def reviwerPredict(self, predict_x):
        predicted_LogisticRegression = self.model_LogisticRegression.predict(predict_x)
        predicted_DTC = self.model_DTC.predict(predict_x)
        predicted_SVM = self.model_SVM.predict(predict_x)
        predicted_Random_Forest = self.model_Random_Forest.predict(predict_x)
        predicted_AdaBoost = self.model_AdaBoost.predict(predict_x)
        predicted_Bayes = self.model_Bayes.predict(predict_x)
        return predicted_LogisticRegression, predicted_DTC, predicted_SVM, \
               predicted_Random_Forest, predicted_AdaBoost, predicted_Bayes
def calcAverage(feature_matrix_PRGIT):
    code_number =0;
    code_sum =0;
    reviewer_number=0;
    reviewer_sum =0;
    for matrix in feature_matrix_PRGIT:
        if matrix[0]:
            code_number +=1;
            code_sum +=matrix[0]*matrix[1]*matrix[2]
        if matrix[3]:
            reviewer_number +=1;
            reviewer_sum +=matrix[3]*matrix[4];
    code_average = code_sum/code_number
    reviewer_average = float(reviewer_sum)/reviewer_number
    return code_average,reviewer_average
if __name__=="__main__":
    from featuresParser import featuresParser
    from configReader import configReader
    from mongodb import mongodb
    #--------------------
    #train the model
    #--------------------
    cReader = configReader('config.ini')
    database = cReader.get_db()
    engineerList = cReader.get_engineerList()
    
    
    dB = mongodb(database['dbName'])
    fparser = featuresParser(db=dB,collName_git=database['collName_git'],collName_PR=database['collName_PR'],collName_PR2=database['collName_PR2'])
    class_list_PRGIT,feature_matrix_PRGIT =fparser.PRgitSetData(engineerList)
    
    #print class_list_PRGIT,feature_matrix_PRGIT

    ML_model = machineLearn(feature_matrix_PRGIT,class_list_PRGIT)

    print "Sample number is", len(feature_matrix_PRGIT)

    split_rate = 0.1
    print "Percentage of test set is", split_rate
    ML_model.setSplitSize(split_rate)

    ML_model.train()
    ML_model.save_model()
    print calcAverage(feature_matrix_PRGIT)

