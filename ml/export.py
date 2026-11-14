import sys,json,numpy as np; sys.path.insert(0,'ml')
from parse import load
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix
from collections import defaultdict
d=[x for x in load() if x['g'] and x['co'] is not None and x['th'] and x['o2'] and x['air'] is not None]
G=['PMMA film','PMMA sheet','PMMA rod','Fabric','Nomex']
X=np.array([[x['g']==g for g in G]+[np.log(x['th']),x['o2']] for x in d],float)
y=np.array([x['co'] for x in d]); yb=(y>100).astype(int)
mk=lambda s=0:RandomForestClassifier(60,max_depth=6,min_samples_leaf=3,random_state=s)
aucs=[];accs=[];cms=[]
for r in range(10):
    p=cross_val_predict(mk(),X,yb,cv=StratifiedKFold(5,shuffle=True,random_state=r),method='predict_proba')[:,1]
    aucs.append(roc_auc_score(yb,p)); accs.append(accuracy_score(yb,p>.5)); cms.append(confusion_matrix(yb,p>.5))
cm=np.mean(cms,0)
print('AUC',np.mean(aucs).round(3),'acc',np.mean(accs).round(3),'cm',cm.round(1))
m=mk().fit(X,yb)
def tree(t):
    T=t.tree_; out=[]
    for i in range(T.node_count):
        if T.children_left[i]==-1:
            v=T.value[i][0]; out.append([-1,round(float(v[1]/v.sum()),4)])
        else: out.append([int(T.feature[i]),round(float(T.threshold[i]),4),int(T.children_left[i]),int(T.children_right[i])])
    return out
ranges=defaultdict(dict)
for g in G:
    xs=[x for x in d if x['g']==g]
    ranges[g]=dict(n=len(xs),th=sorted(set(x['th'] for x in xs)),o2=[min(x['o2'] for x in xs),max(x['o2'] for x in xs)])
model=dict(features=G+['log_thickness_mm','o2_pct'],threshold_ppm=100,trees=[tree(t) for t in m.estimators_],
  cv=dict(folds=5,repeats=10,auc=round(float(np.mean(aucs)),2),accuracy=round(float(np.mean(accs)),2),baseline_accuracy=round(float(max(yb.mean(),1-yb.mean())),2),n=len(d),n_high=int(yb.sum())),
  importance=dict(zip(['material','thickness','oxygen'],[round(float(sum(m.feature_importances_[:5])),2)]+[round(float(v),2) for v in m.feature_importances_[5:]])),
  ranges=ranges,tests=[[G.index(x['g']),x['th'],x['o2'],x['co']] for x in d])
s='window.FIRE_MODEL='+json.dumps(model,separators=(',',':'))+';'
open('docs/model.js','w').write(s); print('bytes',len(s)); print(json.dumps(model['cv']),model['importance']); print(json.dumps(ranges))
