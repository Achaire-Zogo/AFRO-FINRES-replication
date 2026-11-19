import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'serif','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
S = pd.read_csv('data/afro_finres_scores.csv').set_index('iso3')
K = ['P','D','S','C','G','T']
LAB = ['Prevention (P)','Detection (D)','Response (S)','Recovery &\ncontinuity (C)','Governance (G)','Third-party\nmgmt (T)']
CEMAC = ['CMR','CAF','TCD','COG','GNQ','GAB']
F='figures/'
import os; os.makedirs(F, exist_ok=True)
# Fig 2: ranking with MC uncertainty
d = S.sort_values('AFRO_FINRES')
fig, ax = plt.subplots(figsize=(6.3,7.6))
col = ['#c0392b' if i=='CMR' else ('#e59866' if i in CEMAC else '#5d6d7e') for i in d.index]
ax.barh(range(len(d)), d.AFRO_FINRES, color=col, height=.72)
ax.set_yticks(range(len(d))); ax.set_yticklabels([f"{n} ({int(lo)}–{int(hi)})" for n,lo,hi in zip(d.name.str.replace(', Fed. Rep.','').str.replace(', The',''),d.rank_p05,d.rank_p95)], fontsize=7)
ax.axvline(S.AFRO_FINRES.mean(), ls='--', c='k', lw=.8); ax.text(S.AFRO_FINRES.mean()+1, 1, 'SSA mean', fontsize=7)
ax.set_xlabel('AFRO-FINRES score (0–100), equal weights, arithmetic aggregation'); ax.set_xlim(0,100)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#c0392b',label='Cameroon'),Patch(color='#e59866',label='Other CEMAC'),Patch(color='#5d6d7e',label='Other SSA')],loc='lower right',frameon=False,fontsize=7)
plt.tight_layout(); plt.savefig(F+'fig2_ranking.pdf'); plt.savefig(F+'fig2_ranking.png',dpi=200); plt.close()
# Fig 3: radar
ang = np.linspace(0,2*np.pi,6,endpoint=False).tolist(); ang+=ang[:1]
fig = plt.figure(figsize=(5,4.6)); ax = plt.subplot(111, polar=True)
series = {'Cameroon':S.loc['CMR',K],'CEMAC mean':S.loc[CEMAC,K].mean(),'SSA mean':S[K].mean(),'SSA top quartile':S[S['rank']<=12][K].mean()}
sty = {'Cameroon':('#c0392b','-'),'CEMAC mean':('#e59866','--'),'SSA mean':('#2c3e50',':'),'SSA top quartile':('#27ae60','-.')}
for k,v in series.items():
    vals=list(v.values)+[v.values[0]]; c,l=sty[k]; ax.plot(ang,vals,c=c,ls=l,lw=1.5,label=k)
    if k=='Cameroon': ax.fill(ang,vals,c=c,alpha=.12)
ax.set_xticks(ang[:-1]); ax.set_xticklabels(LAB,fontsize=7.5); ax.set_ylim(0,100); ax.set_yticks([25,50,75]); ax.tick_params(axis='y',labelsize=6)
ax.legend(loc='upper center',bbox_to_anchor=(.5,-.08),ncol=2,frameon=False,fontsize=7.5)
plt.tight_layout(); plt.savefig(F+'fig3_radar.pdf'); plt.savefig(F+'fig3_radar.png',dpi=200); plt.close()
# Fig 4: validation scatter
from scipy import stats
wb = pd.read_csv('data/wb_raw.csv'); wb=wb[wb.year>=2021].sort_values('year').groupby(['iso3','indicator']).last().value.unstack()
fig, axs = plt.subplots(1,2,figsize=(6.6,2.9))
for ax,(code,lab) in zip(axs,[('account.t.d','Account ownership, % age 15+ (Findex 2024)'),('mobileaccount.t.d','Mobile money account, % age 15+ (Findex 2024)')]):
    dd = pd.concat([S.AFRO_FINRES, wb[code]],axis=1).dropna()
    ax.scatter(dd.AFRO_FINRES, dd[code], s=14, c=['#c0392b' if i=='CMR' else ('#e59866' if i in CEMAC else '#5d6d7e') for i in dd.index])
    for i in dd.index:
        if i in CEMAC+['KEN','GHA','MUS','ZAF','RWA']: ax.annotate(i,(dd.loc[i,'AFRO_FINRES'],dd.loc[i,code]),fontsize=6,xytext=(2,2),textcoords='offset points')
    rho,p=stats.spearmanr(dd.iloc[:,0],dd.iloc[:,1]); b=np.polyfit(dd.iloc[:,0],dd.iloc[:,1],1); xs=np.linspace(0,100,10)
    ax.plot(xs,np.polyval(b,xs),c='k',lw=.7,ls='--'); ax.set_title(f"Spearman ρ = {rho:.2f} (n = {len(dd)})",fontsize=8)
    ax.set_xlabel('AFRO-FINRES score'); ax.set_ylabel(lab,fontsize=7)
plt.tight_layout(); plt.savefig(F+'fig4_validation.pdf'); plt.savefig(F+'fig4_validation.png',dpi=200); plt.close()

# ---- Scenario analysis: resilience-triangle model ----
# Q(t): service functionality (%). Shock at t=0 removes I = I0*(1-a*P~)*(1-b*T~) for third-party shocks / (1-a*P~) others,
# undetected-propagation delay tau = tau0*(1-c*D~); recovery is linear over Tr = Tr0*(1-e*(S~+C~)/2); governance scales a,c,e via (0.5+0.5*G~).
SCEN = {'SC1 Phishing / SIM-swap account takeover':dict(I0=25,tau0=72,Tr0=120,third=False),
        'SC2 Payment-API provider failure':dict(I0=60,tau0=6,Tr0=48,third=True),
        'SC3 Core mobile-money platform outage':dict(I0=90,tau0=2,Tr0=36,third=False),
        'SC4 Attack on shared switch / central infrastructure':dict(I0=70,tau0=24,Tr0=96,third=True)}
a,b,c,e = .6,.5,.7,.6
def simulate(row,p,T=240,dt=.5):
    P,Dd,Ss,C,G,Tt = [row[k]/100 for k in K]; g=.5+.5*G
    I = p['I0']*(1-a*g*P)*((1-b*Tt) if p['third'] else 1)
    tau = p['tau0']*(1-c*g*Dd); Tr = p['Tr0']*(1-e*g*(Ss+C)/2)
    t=np.arange(0,T,dt); Q=np.full_like(t,100.)
    Q[(t>=0)&(t<tau)] = 100-I
    m=(t>=tau)&(t<tau+Tr); Q[m]=100-I*(1-(t[m]-tau)/Tr)
    L = I*tau + I*Tr/2           # area of lost functionality (%·h)
    return t,Q,dict(impact=I,tau=tau,Tr=Tr,loss=L,R=1-L/(100*T))
COUNTRIES=['CMR','GAB','TCD','KEN','GHA','MUS']
rows=[]
for sn,p in SCEN.items():
    for iso in S.index:
        _,_,r=simulate(S.loc[iso],p); rows.append(dict(scenario=sn,iso3=iso,**r))
sc=pd.DataFrame(rows); sc.round(3).to_csv('data/scenario_results.csv',index=False)
fig,axs=plt.subplots(2,2,figsize=(6.6,4.8),sharex=True,sharey=True)
cc={'CMR':'#c0392b','GAB':'#e59866','TCD':'#f5cba7','KEN':'#2980b9','GHA':'#27ae60','MUS':'#2c3e50'}
for ax,(sn,p) in zip(axs.flat,SCEN.items()):
    for iso in COUNTRIES:
        t,Q,_=simulate(S.loc[iso],p); ax.plot(t,Q,c=cc[iso],lw=1.3,label=S.loc[iso,'name'])
    ax.set_title(sn,fontsize=7.5); ax.set_ylim(0,102); ax.set_xlim(0,200)
for ax in axs[1]: ax.set_xlabel('Hours after incident')
for ax in axs[:,0]: ax.set_ylabel('Service functionality Q(t), %')
axs[0,0].legend(fontsize=6,frameon=False,loc='lower right')
plt.tight_layout(); plt.savefig(F+'fig5_scenarios.pdf'); plt.savefig(F+'fig5_scenarios.png',dpi=200); plt.close()
# summary table for paper
piv=sc.pivot(index='iso3',columns='scenario',values='loss')
summ=sc[sc.iso3.isin(COUNTRIES)].copy(); summ['name']=summ.iso3.map(S.name)
print(summ.round(1).to_string())
# correlation between index and mean loss
print('rho(index, mean loss)=',stats.spearmanr(S.AFRO_FINRES, piv.mean(axis=1).reindex(S.index))[0])
# Cameroon improvement simulation: raise D to SSA top-quartile mean
cm=S.loc['CMR'].copy(); tq=S[S['rank']<=12][K].mean()
for dim in K:
    alt=cm.copy(); alt[dim]=max(cm[dim],tq[dim])
    red=[]
    for sn,p in SCEN.items():
        red.append(1-simulate(alt,p)[2]['loss']/simulate(cm,p)[2]['loss'])
    newidx=np.mean([alt[k] for k in K])
    print(f"CMR lift {dim} to TQ: {cm[dim]:.1f}->{alt[dim]:.1f}; index {cm['AFRO_FINRES']:.1f}->{newidx:.1f}; mean loss reduction {np.mean(red)*100:.1f}% ; per scen {[round(x*100,1) for x in red]}")
