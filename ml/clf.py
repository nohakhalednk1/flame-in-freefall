import sys,numpy as np; sys.path.insert(0,'ml')
from parse import load
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score
d=[x for x in load() if x['g'] and x['co'] is not None and x['th'] and x['o2'] and x['air'] is not None]
G=['PMMA film','PMMA sheet','PMMA rod','Fabric','Nomex']
X=np.array([[x['g']==g for g in G]+[np.log(x['th']),x['o2'],x['air']] for x in d],float)
y=np.array([x['co'] for x in d])
for thr in [50,100]:
    yb=(y>thr).astype(int); print('thr',thr,'positives',yb.sum(),'/',len(yb))
    for name,m,cols in [('material only',LogisticRegression(max_iter=2000),slice(0,5)),('thickness only',LogisticRegression(max_iter=2000),[5]),
                        ('logreg all',LogisticRegression(max_iter=2000,C=1),slice(None)),('RF all',RandomForestClassifier(300,min_samples_leaf=3,random_state=0),slice(None))]:
        aucs=[];accs=[]
        for r in range(10):
            p=cross_val_predict(m,X[:,cols],yb,cv=StratifiedKFold(5,shuffle=True,random_state=r),method='predict_proba')[:,1]
            aucs.append(roc_auc_score(yb,p)); accs.append(accuracy_score(yb,p>.5))
        print(f'  {name:15s} AUC {np.mean(aucs):.2f} acc {np.mean(accs):.2f}')
    print('  majority acc',max(yb.mean(),1-yb.mean()).round(2))
m=RandomForestClassifier(300,min_samples_leaf=3,random_state=0).fit(X,(y>100).astype(int))
print(dict(zip(G+['log_th','o2','air'],m.feature_importances_.round(2))))
