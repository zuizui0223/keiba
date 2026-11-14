#!/usr/bin/env python3
"""Exploratory learned baseline and outcome-blind parent-pair controls for PR45.

Same retrospective archive, same 2019--2021 target rows. Not a fresh holdout,
complete multigeneration A, genetic causation, prospective forecast or profit.
Raw/individual outputs are never written; publisher redistribution licence Unknown.
"""
from __future__ import annotations
import argparse,gc,hashlib,json,time,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import lsqr

SEEDS=(20261114,20261115,20261116)
ALPHA=100.0


def weights(ids):
    s=pd.Series(np.asarray(ids)).astype(str)
    return 1/s.map(s.value_counts()).to_numpy(dtype=float)


def temporal(history,future):
    if history.empty or future.empty:raise ValueError('EMPTY_TIME_WINDOW')
    if history.day.max()>=future.day.min():raise ValueError('TEMPORAL_OVERLAP')


def peers(history,future,group):
    h=history[history[group].astype(str).ne('')]
    if h.empty:return np.zeros(len(future)),np.zeros(len(future))
    p=h.groupby([group,'stratum','horse'],observed=True).y.mean().rename('v').reset_index()
    p['v']=p.v-.5
    total=p.groupby([group,'stratum'],observed=True).v.agg(['sum','size'])
    a=total.reindex(pd.MultiIndex.from_frame(future[[group,'stratum']])).fillna(0)
    own=p.set_index([group,'stratum','horse']).v.reindex(pd.MultiIndex.from_frame(future[[group,'stratum','horse']]))
    return a['sum'].to_numpy()-own.fillna(0).to_numpy(),np.maximum(a['size'].to_numpy()-own.notna().to_numpy(),0)


def history_features(history,future):
    temporal(history,future)
    f=future.reset_index(drop=True)
    h=history.sort_values(['day','horse','race'])
    g=h.groupby('horse',observed=True).y.agg(['mean','size'])
    own=g.reindex(f.horse).fillna({'mean':.5,'size':0})
    n=own['size'].to_numpy();m=own['mean'].to_numpy()
    x=pd.DataFrame({'own_mean':.5+n/(n+5)*(m-.5),'log_n':np.log1p(n),'cold':(n==0).astype(float)})
    for k in (1,3,10):
        last=h.groupby('horse',observed=True).tail(k).groupby('horse',observed=True).y.mean()
        x['last'+str(k)]=last.reindex(f.horse).fillna(.5).to_numpy()
    cg=h.groupby(['horse','stratum'],observed=True).y.agg(['mean','size'])
    c=cg.reindex(pd.MultiIndex.from_frame(f[['horse','stratum']])).fillna({'mean':.5,'size':0})
    cn=c['size'].to_numpy();cm=c['mean'].to_numpy()
    x['context_mean']=.5+cn/(cn+5)*(cm-.5);x['log_context_n']=np.log1p(cn)
    recent=h[h.day>=pd.Timestamp(int(f.year.min()),1,1)-pd.Timedelta(days=365)]
    r=recent.groupby('horse',observed=True).y.agg(['mean','size']).reindex(f.horse).fillna({'mean':.5,'size':0})
    rn=r['size'].to_numpy();x['recent_mean']=.5+rn/(rn+5)*(r['mean'].to_numpy()-.5);x['log_recent_n']=np.log1p(rn)
    lastday=h.groupby('horse',observed=True).day.max().reindex(f.horse).to_numpy()
    delta=(f.day.to_numpy()-lastday)/np.timedelta64(1,'D')
    x['log_days_since_last']=np.log1p(np.nan_to_num(np.clip(delta,0,3650),nan=3650))
    for name in ('trainer_id','jockey_id'):
        s,q=peers(h,f,name);x[name+'_mean']=s/(8+q);x[name+'_log_support']=np.log1p(q)
    age=pd.to_numeric(f.age,errors='coerce').clip(1,15).fillna(4)
    x['age_years']=age.to_numpy();x['distance_km']=f.distance.to_numpy()/1000
    numeric=list(x.columns)
    jra=f.circuit.eq('JRA').to_numpy().astype(float)
    for col in numeric:x[col+'_JRA']=x[col].to_numpy()*jra
    for col in ('course','circuit','surface','sex','going','race_class','stratum'):
        x[col]=f[col].astype(str).fillna('').to_numpy()
    return x


def parent_features(history,future):
    temporal(history,future)
    n=history.groupby('horse',observed=True).size().reindex(future.horse).fillna(0).to_numpy()
    out={}
    for col,label in [('sire_id','sire'),('dam_id','dam')]:
        s,k=peers(history,future,col);signal=s/(8+k)
        out[label+'_signal']=signal
        out[label+'_unseen']=signal*(n==0)
        out[label+'_attenuated']=signal*5/(n+5)
    return pd.DataFrame(out)


def shuffle_parent_map(data,seed):
    parents=data[['horse','sire_id','dam_id']].astype(str).drop_duplicates()
    if parents.horse.duplicated().any():raise ValueError('CONFLICTING_PARENT_PAIRS')
    first=data.sort_values(['day','horse']).drop_duplicates('horse').copy()
    age=pd.to_numeric(first.age,errors='coerce')
    first['birth_bin']=((first.year-age)//5).fillna(-999).astype(int)
    first['horse']=first.horse.astype(str)
    base=parents.set_index('horse').sort_index();out=base.copy()
    rng=np.random.default_rng(seed)
    for _,g in first.groupby(['birth_bin','circuit'],observed=True,sort=True):
        ids=sorted(g.horse.tolist());perm=rng.permutation(len(ids))
        out.loc[ids,['sire_id','dam_id']]=base.loc[ids].to_numpy()[perm]
    return out


def _matrix(x,state=None):
    if state is None:
        nums=[c for c in x if pd.api.types.is_numeric_dtype(x[c])]
        cats=[c for c in x if c not in nums]
        a=x[nums].to_numpy(dtype=float);mean=np.nanmean(a,axis=0);std=np.nanstd(a,axis=0);std[std<1e-10]=1
        vocab={}
        for c in cats:
            counts=x[c].astype(str).value_counts()
            vals=sorted(counts[counts>=20].head(256).index)
            vocab[c]={v:i for i,v in enumerate(vals)}
        state={'nums':nums,'cats':cats,'mean':mean,'std':std,'vocab':vocab}
    a=np.nan_to_num((x[state['nums']].to_numpy(dtype=float)-state['mean'])/state['std'])
    blocks=[sparse.csr_matrix(np.ones((len(x),1))),sparse.csr_matrix(a)]
    for c in state['cats']:
        v=state['vocab'][c];index=x[c].astype(str).map(v).fillna(len(v)).to_numpy(dtype=int)
        blocks.append(sparse.csr_matrix((np.ones(len(x)),(np.arange(len(x)),index)),shape=(len(x),len(v)+1)))
    return sparse.hstack(blocks,format='csr'),state


def fit_linear(x,y,w,alpha=ALPHA):
    X,state=_matrix(x)
    w=np.asarray(w,dtype=float);w=w/w.mean();root=np.sqrt(w)
    Xw=X.multiply(root[:,None]).tocsr();pen=np.ones(X.shape[1]);pen[0]=0
    A=sparse.vstack([Xw,np.sqrt(alpha)*sparse.diags(pen)],format='csr')
    target=np.r_[np.asarray(y,dtype=float)*root,np.zeros(X.shape[1])]
    sol=lsqr(A,target,atol=1e-8,btol=1e-8,iter_lim=2000)
    if sol[1] not in (0,1,2):raise ValueError('RIDGE_SOLVER_DID_NOT_CONVERGE_'+str(sol[1]))
    return {'state':state,'coef':sol[0],'alpha':alpha,'iterations':sol[2],'uses_test_data':False}


def predict_linear(model,x):
    X,_=_matrix(x,model['state'])
    return np.clip(np.asarray(X@model['coef']).ravel(),0,1)


def summarize(f,p):
    if f.empty:return {'rows':0,'horses':0,'rmse':None}
    w=weights(f.horse);y=f.y.to_numpy()
    r={k:float(np.sqrt(np.average((np.asarray(v)-y)**2,weights=w))) for k,v in p.items()}
    r['midrank']=float(np.sqrt(np.average((y-.5)**2,weights=w)))
    return {'rows':len(f),'horses':int(f.horse.nunique()),'races':int(f.race.nunique()),'rmse':r,
        'gain_strong_to_kin':r['strong']-r['strong_kin'],
        'gain_midrank_to_strong':r['midrank']-r['strong'],
        'gain_midrank_to_kin':r['midrank']-r['strong_kin'],
        'gain_sham_to_kin':{k:r[k]-r['strong_kin'] for k in r if k.startswith('sham_')}}


def cluster_ci(f,p,B=399):
    if f.empty:return {}
    keys=['strong','strong_kin']+[k for k in p if k.startswith('sham_')]
    y=f.y.to_numpy();w=weights(f.horse)
    sq=np.column_stack([(p[k]-y)**2 for k in keys]+[(y-.5)**2])*w[:,None]
    out={}
    for name,c in [('sire',f.sire_id.astype(str)),('day',f.day.astype(str))]:
        a=pd.DataFrame(sq);a['w']=w;a['c']=c.to_numpy();mat=a.groupby('c',observed=True).sum().to_numpy();n=len(mat)
        if n<20:out[name]={'clusters':n,'status':'LOW_SUPPORT'};continue
        rng=np.random.default_rng(20261114);samples=[]
        for _ in range(B):
            s=mat[rng.integers(n,size=n)].sum(axis=0);v=np.sqrt(s[:-1]/s[-1])
            samples.append([v[0]-v[1],v[-1]-v[1]]+[v[i]-v[1] for i in range(2,len(keys))])
        a=np.asarray(samples);out[name]={'clusters':n,'draws':B,'pointwise_single_way_only':True,
            'strong_minus_kin':np.quantile(a[:,0],[.025,.975]).tolist(),
            'midrank_minus_kin':np.quantile(a[:,1],[.025,.975]).tolist(),
            'sham_minus_kin':{keys[i]:np.quantile(a[:,i],[.025,.975]).tolist() for i in range(2,len(keys))}}
    return out


def run(archive,output):
    from ecology_japan_archive_forward import SOURCE_SHA,COLS,prepare_frame,make_features,predict as old_predict
    from ecology_japan_group_extension import source_labels,select_sires,ALIASES,check_reference
    start=time.monotonic();digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=SOURCE_SHA:raise ValueError('SOURCE_SHA_CHANGED')
    lock=json.loads(Path('docs/evidence/japan-group-primary-lock-20261114.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(archive) as z,z.open('2010-2021.csv') as file:
        raw=pd.read_csv(file,usecols=COLS+['sire','going','race_class','jockey_id'],dtype=str,keep_default_na=False)
    mapping,name_qa,sire_labels=source_labels(raw);d,qa=prepare_frame(raw)
    if qa!=lock['quality']:raise ValueError('PRIMARY_SOURCE_COHORT_CHANGED')
    raw['race']=pd.to_datetime(raw.date,format='mixed').dt.strftime('%Y-%m-%d')+'|'+raw.racecourse.str.strip()+'|'+pd.to_numeric(raw.race_number).astype(int).astype(str)
    raw['horse']=raw.horse_id.astype(str)
    meta=raw.set_index(['horse','race'])[['age','sex','going','race_class','jockey_id']].reindex(pd.MultiIndex.from_frame(d[['horse','race']]))
    if meta.isna().all(axis=1).any():raise ValueError('METADATA_ID_JOIN_FAILED')
    for c in meta:d[c]=meta[c].fillna('').astype(str).to_numpy()
    d['prefix']=d.horse.astype(str).map(mapping)
    if d.prefix.isna().any():raise ValueError('PREFIX_JOIN_FAILED')
    source_extra={c:{'missing_rows':int(d[c].eq('').sum()),'distinct_values':int(d[c].nunique())} for c in meta}
    del raw,meta;gc.collect()
    selected=select_sires(d,20)
    maps={str(seed):shuffle_parent_map(d,seed) for seed in SEEDS}
    original=d[['horse','sire_id','dam_id']].astype(str).drop_duplicates().set_index('horse')
    perm_audit={k:{'horses':len(m),'changed_sire_fraction':float(m.sire_id.ne(original.reindex(m.index).sire_id).mean()),
        'changed_dam_fraction':float(m.dam_id.ne(original.reindex(m.index).dam_id).mean())} for k,m in maps.items()}
    feature_years={};targets={};old_predictions={}
    for year in range(2016,2022):
        h=d[d.year<year];f=d[d.year==year].reset_index(drop=True)
        x=history_features(h,f);kin=parent_features(h,f)
        controls={}
        for seed,m in maps.items():
            hh=h.copy();ff=f.copy()
            for col in ('sire_id','dam_id'):
                hh[col]=hh.horse.astype(str).map(m[col]);ff[col]=ff.horse.astype(str).map(m[col])
            controls['sham_'+seed]=parent_features(hh,ff)
            del hh,ff
        feature_years[year]=(x,kin,controls);targets[year]=f
        if year>=2019:
            ref=next(r for r in lock['years'] if r['test_year']==year)
            of=make_features(h,f);op=old_predict(of,ref['validation_selected_weights']);check_reference(of,op,ref['all'])
            old_predictions[year]={'old_own':op[:,0],'old_kin':op[:,3]}
        print(json.dumps({'stage':'YEAR_FEATURES_READY','year':year,'rows':len(f)},ensure_ascii=False),flush=True)
        del h;gc.collect()
    annual=[];predictions=[];frames=[]
    for year in (2019,2020,2021):
        past=list(range(2016,year));train=pd.concat([targets[t] for t in past],ignore_index=True)
        tx=pd.concat([feature_years[t][0] for t in past],ignore_index=True);fx=feature_years[year][0]
        y=train.y.to_numpy();w=weights(train.horse);out={};fits={}
        configurations={'strong':None,'strong_kin':'real',**{k:k for k in feature_years[year][2]}}
        for name,extra in configurations.items():
            a=tx;b=fx
            if extra is not None:
                parts=[feature_years[t][1] if extra=='real' else feature_years[t][2][extra] for t in past]
                ktrain=pd.concat(parts,ignore_index=True);ktest=feature_years[year][1] if extra=='real' else feature_years[year][2][extra]
                a=pd.concat([tx,ktrain],axis=1);b=pd.concat([fx,ktest],axis=1)
            model=fit_linear(a,y,w);out[name]=predict_linear(model,b)
            fits[name]={'training_rows':len(a),'training_horses':int(train.horse.nunique()),'max_training_date':str(train.day.max().date()),'alpha':ALPHA,'iterations':model['iterations']}
        out.update(old_predictions[year]);f=targets[year]
        annual.append({'year':year,'fits':fits,'scores':summarize(f,out)})
        predictions.append(out);frames.append(f)
        print(json.dumps({'stage':'NEW_YEAR_SCORED','year':year,'summary':annual[-1]['scores']},ensure_ascii=False),flush=True)
        del tx,train;gc.collect()
    f=pd.concat(frames,ignore_index=True);p={k:np.concatenate([a[k] for a in predictions]) for k in predictions[0]}
    def group(mask,ci=False):
        ff=f.loc[mask];pp={k:v[np.asarray(mask)] for k,v in p.items()};r=summarize(ff,pp)
        r['years']={str(y):summarize(ff[ff.year==y],{k:v[ff.year.eq(y).to_numpy()] for k,v in pp.items()}) for y in (2019,2020,2021)}
        if ci:r['intervals']=cluster_ci(ff,pp)
        return r
    primary={'all':np.ones(len(f),bool),'JRA':f.circuit.eq('JRA'),'NAR':f.circuit.eq('NAR'),
        'first_recorded_start':f.first_recorded,'Meisho':f.prefix.eq('メイショウ'),'Tagano':f.prefix.eq('タガノ'),
        'nonMeisho':~f.prefix.eq('メイショウ')}
    results={k:group(m,True) for k,m in primary.items()}
    prefix={label:group(f.prefix.eq(label)) for label in [*ALIASES,'OTHER_UNMATCHED','AMBIGUOUS_NAME_GROUP']}
    sires=[{'source_sire_label':sire_labels.get(s,'unavailable'),'pre2019_offspring':n,'results':group(f.sire_id.astype(str).eq(s))} for s,n in selected]
    report={'status':'REAL_RETROSPECTIVE_STRONG_BASELINE_AND_THREE_SHUFFLED_PARENT_CONTROLS',
        'source_sha256':digest,'source_quality':qa,'extra_source_metadata':source_extra,
        'target_rows':len(f),'target_horses':int(f.horse.nunique()),'original_annual_predictions_unchanged':True,
        'new_hyperparameters_fixed_before_this_run':{'ridge_alpha':ALPHA,'feature_years':[2016,2017,2018,2019,2020,2021],'sham_seeds':list(SEEDS)},
        'new_untouched_test_set':False,'parent_shuffle':{'strata':'birth estimate five-year bin and first retained circuit; outcome-blind entire retrospective roster','audit':perm_audit,'permutation_p_value':False},
        'annual':annual,'groups':results,'prefix_groups':prefix,'selected_sire_groups':sires,
        'raw_or_individual_outputs_exported':False,'source_redistribution_license':'Unknown',
        'limits':['This sensitivity was designed after seeing earlier 2019-2021 results; no new untouched test cohort.',
          'All own and peer histories are frozen at January 1, not updated after every race within a test year.',
          'Metadata and parent labels are retrospective and not independently timestamp-verified; not a prospective forecast.',
          'Three whole parent-pair permutations are negative controls, not a calibrated randomization significance test.',
          'Strong baseline is one fixed regularized linear model; its complexity is not guaranteed optimal.',
          'Classification finishers only, direct shared parents not multigeneration A/genomic G/causal genetics, no odds or profit.',
          'Prefix comparisons are unadjusted exploratory subgroup descriptions, not owner identity or independent replication.'],
        'seconds':round(time.monotonic()-start,3)}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'target_rows':len(f),'groups':results},ensure_ascii=False),flush=True)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.archive,a.output)
if __name__=='__main__':main()
