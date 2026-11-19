"""AFRO-FINRES: African FinTech Operational Resilience index, Sub-Saharan Africa (48 countries)."""
import json, numpy as np, pandas as pd
rng = np.random.default_rng(20261118)
D = 'data/'
ssf = json.load(open(D+'ssf.json'))[1]
meta = pd.DataFrame([{'iso3':c['id'],'iso2':c['iso2Code'],'name':c['name']} for c in ssf]).set_index('iso3')
CEMAC = ['CMR','CAF','TCD','COG','GNQ','GAB']

# ---- latest value per country (2015-2025) ----
wb = pd.read_csv(D+'wb_raw.csv')
FINDEX = ['account.t.d','mobileaccount.t.d','con18.s','con19.s','fin11d.s','fin25e4c','fin13_1a','fin16']
wb = wb[~(wb.indicator.isin(FINDEX) & (wb.year<2021))]
wb = wb.sort_values('year').groupby(['iso3','indicator']).last().reset_index()
val = wb.pivot(index='iso3', columns='indicator', values='value')
yr  = wb.pivot(index='iso3', columns='indicator', values='year')
gci = pd.read_csv(D+'gci2024_pillars.csv').set_index('iso3')

# ---- PeeringDB: active IXPs and colocation facilities ----
def pdb_count(f):
    d = pd.DataFrame(json.load(open(D+f))['data'])
    d = d[d.status=='ok']
    return d.groupby('country').size()
ix, fac = pdb_count('pdb_ix.json'), pdb_count('pdb_fac.json')
meta['ixp'] = meta.iso2.map(ix).fillna(0)
meta['fac'] = meta.iso2.map(fac).fillna(0)

X = pd.DataFrame(index=meta.index)
pop10m = val['SP.POP.TOTL']/1e7
X['P1_secure_servers_log'] = np.log1p(val['IT.NET.SECR.P6'])
X['P2_gci_capacity']       = gci['capacity']
X['D1_gci_technical']      = gci['technical']
X['S1_gci_organizational'] = gci['organizational']
X['S2_gci_cooperation']    = gci['cooperation']
X['C1_electricity_access'] = val['EG.ELC.ACCS.ZS']
X['C2_outages_inv']        = -np.log1p(val['IC.ELC.OUTG.ZS'])
X['C3_internet_users']     = val['IT.NET.USER.ZS']
X['G1_wgi_rq'] = val['GOV_WGI_RQ.EST']; X['G2_wgi_ge'] = val['GOV_WGI_GE.EST']
X['G3_wgi_rl'] = val['GOV_WGI_RL.EST']; X['G4_wgi_cc'] = val['GOV_WGI_CC.EST']
X['G5_gci_legal'] = gci['legal']
X['T1_ixp_per10m_log'] = np.log1p(meta['ixp']/pop10m)
X['T2_fac_per10m_log'] = np.log1p(meta['fac']/pop10m)
DIMS = {'P':['P1_secure_servers_log','P2_gci_capacity'],
        'D':['D1_gci_technical'],
        'S':['S1_gci_organizational','S2_gci_cooperation'],
        'C':['C1_electricity_access','C2_outages_inv','C3_internet_users'],
        'G':['G1_wgi_rq','G2_wgi_ge','G3_wgi_rl','G4_wgi_cc','G5_gci_legal'],
        'T':['T1_ixp_per10m_log','T2_fac_per10m_log']}
DNAME = {'P':'Prevention','D':'Detection','S':'Response','C':'Recovery & continuity','G':'Governance','T':'Third-party dependency management'}

missing = X.isna().sum()
# winsorise at 2.5/97.5 pct, min-max to 0-100
def mm(s):
    lo, hi = s.quantile(.025), s.quantile(.975); s = s.clip(lo, hi)
    return 100*(s-s.min())/(s.max()-s.min())
N = X.apply(mm)
def dim_scores(N):
    return pd.DataFrame({k: N[v].mean(axis=1, skipna=True) for k,v in DIMS.items()})
S = dim_scores(N)
K = list(DIMS)
def linear(S,w): return (S[K]*w).sum(axis=1)/sum(w)
def geometric(S,w): return np.exp((np.log(S[K].clip(lower=1))*w).sum(axis=1)/sum(w))
w0 = np.ones(6)/6
S['AFRO_FINRES'] = linear(S,w0)
S['AFRO_FINRES_geo'] = geometric(S,w0)
# moderated specification: governance amplifies security capabilities
lam = 0.5
sec = (S.P+S.D)/2
S['AFRO_FINRES_mod'] = ( S[['S','C','T']].sum(axis=1) + sec*(1-lam+lam*S.G/100)*2 + S.G )/6

# PCA weights on dimensions (first component loadings^2)
Z = (S[K]-S[K].mean())/S[K].std()
ev, evec = np.linalg.eigh(np.corrcoef(Z.T.values))
pc1 = np.abs(evec[:,-1]); w_pca = pc1**2/np.sum(pc1**2)
S['AFRO_FINRES_pca'] = linear(S,w_pca)
expl = ev[::-1]/ev.sum()

# Monte Carlo uncertainty: Dirichlet weights x aggregation rule x normalisation (minmax vs z)
Nz = X.apply(lambda s:(s.clip(s.quantile(.025),s.quantile(.975))-s.mean())/s.std())
Nz = Nz.apply(lambda s: 100*(s-s.min())/(s.max()-s.min()))
Sz = dim_scores(Nz)
R=5000; ranks=np.zeros((R,len(S)))
for r in range(R):
    w = rng.dirichlet(np.ones(6)*4)
    base = S if rng.random()<.5 else Sz
    sc = linear(base,w) if rng.random()<.5 else geometric(base,w)
    ranks[r]=sc.rank(ascending=False).values
rk = pd.DataFrame({'rank_median':np.median(ranks,0),'rank_p05':np.percentile(ranks,5,0),'rank_p95':np.percentile(ranks,95,0)},index=S.index)
S['rank'] = S.AFRO_FINRES.rank(ascending=False).astype(int)
S = S.join(rk).join(meta[['name']])
# leave-one-dimension-out
lodo = {}
for k in K:
    kk=[x for x in K if x!=k]; lodo[k]=(S[kk].mean(axis=1)).rank(ascending=False)
lodo = pd.DataFrame(lodo)
lodo_shift = (lodo.sub(S['rank'],axis=0)).abs()

# ---- validation against outcomes (not used in index) ----
out = pd.DataFrame({'mm_account':val['mobileaccount.t.d'],'account':val['account.t.d'],
    'distrust_digital':val['fin25e4c'],'phone_lock':val['con18.s'],'mm_meets_needs':val['fin13_1a'],
    'gdppc_log':np.log(val['NY.GDP.PCAP.PP.KD'])}, index=S.index)
out_year = yr[['mobileaccount.t.d','account.t.d']]
from scipy import stats
def partial_spearman(x,y,z):
    d=pd.concat([x,y,z],axis=1).dropna(); r=d.rank()
    rx=np.polyfit(r.iloc[:,2],r.iloc[:,0],1); ry=np.polyfit(r.iloc[:,2],r.iloc[:,1],1)
    ex=r.iloc[:,0]-np.polyval(rx,r.iloc[:,2]); ey=r.iloc[:,1]-np.polyval(ry,r.iloc[:,2])
    rho,p=stats.pearsonr(ex,ey); return rho,p,len(d)
val_rows=[]
for o in ['mm_account','account','distrust_digital','phone_lock','mm_meets_needs']:
    d=pd.concat([S.AFRO_FINRES,out[o]],axis=1).dropna()
    rho,p=stats.spearmanr(d.iloc[:,0],d.iloc[:,1])
    prho,pp,n=partial_spearman(S.AFRO_FINRES,out[o],out.gdppc_log)
    val_rows.append(dict(outcome=o,n=len(d),spearman=rho,p=p,partial_rho_gdp=prho,partial_p=pp))
valid=pd.DataFrame(val_rows)

# internal consistency
cr = S[K].corr(method='spearman')
def cronbach(df):
    df=df.dropna(); k=df.shape[1]; return k/(k-1)*(1-df.var().sum()/df.sum(axis=1).var())
alpha = cronbach(S[K])
rank_corr = {m: stats.spearmanr(S.AFRO_FINRES,S[m])[0] for m in ['AFRO_FINRES_geo','AFRO_FINRES_mod','AFRO_FINRES_pca']}

# ---- save ----
S.round(2).sort_values('rank').to_csv('data/afro_finres_scores.csv')
X.join(meta[['ixp','fac']]).round(4).to_csv('data/afro_finres_indicators_raw.csv')
valid.round(4).to_csv('data/validation.csv',index=False)
res = dict(n=len(S), missing=missing.to_dict(), w_pca=dict(zip(K,np.round(w_pca,3))), pca_explained=list(np.round(expl,3)),
   alpha=round(alpha,3), rank_corr={k:round(v,3) for k,v in rank_corr.items()},
   lodo_max_shift=lodo_shift.max().to_dict(), lodo_mean_shift=lodo_shift.mean().round(2).to_dict(),
   corr=cr.round(2).to_dict(), outages_years=yr['IC.ELC.OUTG.ZS'].describe().to_dict(),
   findex_year=out_year.describe().to_dict(), cemac_mean=S.loc[CEMAC,K+['AFRO_FINRES']].mean().round(1).to_dict(),
   ssa_mean=S[K+['AFRO_FINRES']].mean().round(1).to_dict(), ixp_total=int(meta.ixp.sum()), fac_total=int(meta.fac.sum()),
   ixp_cmr=int(meta.loc['CMR','ixp']), fac_cmr=int(meta.loc['CMR','fac']))
json.dump(res, open('data/results_summary.json','w'), indent=1, default=float)
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
print(S.sort_values('rank')[['name']+K+['AFRO_FINRES','AFRO_FINRES_geo','rank','rank_p05','rank_median','rank_p95']].round(1).to_string())
print(json.dumps(res,indent=1,default=float)[:3500])
print(valid.round(3).to_string())
