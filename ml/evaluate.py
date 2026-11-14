import sys,numpy as np; sys.path.insert(0,'ml')
from parse import load
from sklearn.model_selection import KFold, cross_val_predict, RepeatedKFold
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from collections import Counter
d=[x for x in load() if x['g'] and x['co'] is not None and x['th'] and x['o2'] and x['air'] is not None]
print(len(d),Counter(x['g'] for x in d))
G=['PMMA film','PMMA sheet','PMMA rod','Fabric','Nomex']
X=np.array([[x['g']==g for g in G]+[np.log(x['th']),x['o2'],x['air']] for x in d],float)
y=np.array([x['co'] for x in d]); yl=np.log1p(np.clip(y,0,None))
print('CO rise: median',np.median(y),'min',y.min(),'max',y.max())
def cv(model,logt=True,reps=10):
    maes=[]
    for r in range(reps):
        kf=KFold(5,shuffle=True,random_state=r)
        p=cross_val_predict(model,X,yl if logt else y,cv=kf)
        if logt: p=np.expm1(p)
        maes.append(np.mean(np.abs(p-y)))
    return np.mean(maes)
# baselines
mae0=[]; mae1=[]
for r in range(10):
    for tr,te in KFold(5,shuffle=True,random_state=r).split(X):
        pass
def base(kind,reps=10):
    m=[]
    for r in range(reps):
        err=np.zeros(len(y))
        for tr,te in KFold(5,shuffle=True,random_state=r).split(X):
            for i in te:
                if kind=='global': pr=np.median(y[tr])
                else:
                    same=[j for j in tr if d[j]['g']==d[i]['g']]; pr=np.median(y[same]) if same else np.median(y[tr])
                err[i]=abs(pr-y[i])
        m.append(err.mean())
    return np.mean(m)
print('baseline global median MAE',round(base('global'),1))
print('baseline per-material median MAE',round(base('group'),1))
print('ridge log',round(cv(Ridge(1.0)),1))
print('RF log',round(cv(RandomForestRegressor(300,min_samples_leaf=3,random_state=0)),1))
print('GBR log',round(cv(GradientBoostingRegressor(n_estimators=200,max_depth=2,learning_rate=.05,random_state=0)),1))
print('RF raw',round(cv(RandomForestRegressor(300,min_samples_leaf=3,random_state=0),logt=False),1))
