# Chạy thử LR (phát triển, CHỈ P). Không phải kết quả nghiên cứu. Chạy từ thư mục gốc dự án: python notebooks/02b_dev_LR_P_only.py
import sys; sys.path.insert(0,"src")
import numpy as np, pandas as pd, dev_pipeline as dp, pathlib
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import SplineTransformer, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
coh=dp.load_P(pathlib.Path("data/raw"))
NUM=["RIDAGEYR","BMXBMI","BMXWAIST","BMXHT","BMXWT","WHTR","SBP_MEAN","DBP_MEAN","PAD680","INDFMPIR"]
CAT=["RIAGENDR","RIDRETH3","BPQ020","SMOKE3","DMDEDUC2"]
def model(cols):
    num=[c for c in NUM if c in cols]; cat=[c for c in CAT if c in cols]; ind=[c for c in cols if c.startswith("MISS_")]
    tr=[("num",make_pipeline(SimpleImputer(strategy="median",add_indicator=True,keep_empty_features=True),SplineTransformer(n_knots=4,degree=3)),num),
        ("cat",make_pipeline(SimpleImputer(strategy="most_frequent",keep_empty_features=True),OneHotEncoder(handle_unknown="ignore")),cat)]
    if ind: tr.append(("ind","passthrough",ind))
    return make_pipeline(ColumnTransformer(tr),LogisticRegression(C=0.1,max_iter=3000))
def Xmask(df,blocks):
    X=df[dp.FEATURES].copy()
    for b in dp.BLOCKS: X[f"MISS_{b}"]=0
    for b in blocks: X[dp.BLOCKS[b]]=np.nan; X[f"MISS_{b}"]=1
    return X
def run(ycol):
    rng=np.random.default_rng(0); rows=[]
    for tr,va in GroupKFold(5).split(coh,coh[ycol],coh.grp):
        T,V=coh.iloc[tr],coh.iloc[va]; y=T[ycol].values
        X0=Xmask(T,[]); cols=list(X0.columns)
        base=model(cols).fit(X0,y)
        pick=rng.choice(dp.MASK_SCEN,len(T)); Xc=X0.copy()
        for s in dp.MASK_SCEN:
            m=pick==s
            for b in dp.SCEN[s]: Xc.loc[m,dp.BLOCKS[b]]=np.nan; Xc.loc[m,f"MISS_{b}"]=1
        aug=model(cols).fit(pd.concat([X0,Xc]),np.concatenate([y,y]))
        for s,bl in dp.SCEN.items():
            keep=[c for c in dp.FEATURES if c not in [v for b in bl for v in dp.BLOCKS[b]]]
            ps=model(keep).fit(T[keep],y)
            Xv=Xmask(V,bl)
            for meth,p in [("BASE",base.predict_proba(Xv)[:,1]),("AUG",aug.predict_proba(Xv)[:,1]),("PS",ps.predict_proba(V[keep])[:,1])]:
                rows.append(pd.DataFrame({"idx":V.index,"scenario":s,"method":meth,"p":p}))
    d=pd.concat(rows).pivot_table(index=["idx","scenario"],columns="method",values="p").reset_index()
    return d.merge(coh[[ycol,"w","SDMVSTRA","SDMVPSU"]].rename(columns={ycol:"y"}),left_on="idx",right_index=True)
def stats(df,w):
    o={}
    for s in dp.SCEN:
        g=df[df.scenario==s]; ww=w[g.index]; y=g.y.values; pb=np.average(y,weights=ww); nul=pb*(1-pb)
        for m in ["AUG","PS","BASE"]:
            o[(s,m,"sb")]=1-np.average((g[m]-y)**2,weights=ww)/nul; o[(s,m,"auc")]=roc_auc_score(y,g[m],sample_weight=ww)
    r={}
    for m in ["AUG","PS","BASE"]:
        r[f"{m}_sb_S0"]=o[("S0",m,"sb")]; r[f"{m}_auc_S0"]=o[("S0",m,"auc")]
        r[f"{m}_sb_S1-5"]=np.mean([o[(s,m,"sb")] for s in dp.MASK_SCEN]); r[f"{m}_auc_S1-5"]=np.mean([o[(s,m,"auc")] for s in dp.MASK_SCEN])
    for k in ["sb","auc"]:
        r[f"AUG-PS_{k}_S1-5"]=r[f"AUG_{k}_S1-5"]-r[f"PS_{k}_S1-5"]; r[f"AUG-BASE_{k}_S1-5"]=r[f"AUG_{k}_S1-5"]-r[f"BASE_{k}_S1-5"]
    r["AUG-PS_sb_S0"]=r["AUG_sb_S0"]-r["PS_sb_S0"]; r["BASE_degr_sb"]=r["BASE_sb_S0"]-r["BASE_sb_S1-5"]
    return r
def jk(df):
    w0=df["w"].astype(float); full=stats(df,w0)
    psu=df[["SDMVSTRA","SDMVPSU"]].drop_duplicates(); nh=psu.groupby("SDMVSTRA").size(); reps=[]
    for _,r in psu.iterrows():
        n=nh[r.SDMVSTRA]; w=w0.copy(); inh=df.SDMVSTRA==r.SDMVSTRA
        w[inh&(df.SDMVPSU==r.SDMVPSU)]=0; w[inh&(df.SDMVPSU!=r.SDMVPSU)]*=n/(n-1); reps.append((n,stats(df,w)))
    for k,v in full.items():
        se=sum((n-1)/n*(rr[k]-v)**2 for n,rr in reps)**.5
        print(f"  {k:18s} {v:8.4f}  SE {se:.4f}  CI [{v-2.07*se:.4f}, {v+2.07*se:.4f}]")
coh["y57"]=(coh.LBXGH>=5.7).astype(int)
for yc,lab in [("y","HbA1c>=6.5 (237 ca)"),("y57","HbA1c>=5.7 (2345 ca)")]:
    print("==",lab); jk(run(yc))
