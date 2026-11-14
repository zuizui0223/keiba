#!/usr/bin/env python3
"""Retrospective chronological rank prediction, not prospective betting/genetics.

Original public archive: ayuser/horse-racing-in-japan; publisher licence Unknown.
Do not redistribute raw/row-level data. Only aggregate analysis is exported.
Parent IDs are supplied source IDs; this is a direct-parent-history score, NOT
complete multigeneration A, IBD, heritability or GPS early-section timing.
"""
from __future__ import annotations
import argparse, gc, hashlib, json, math, tempfile, time, zipfile
from itertools import product
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
import pandas as pd

SOURCE='https://www.kaggle.com/api/v1/datasets/download/ayuser/horse-racing-in-japan'
SOURCE_SHA='c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f'
COLS=['date','racecourse','race_number','track','distance','place','horse_id','sire_id','dam_id','horse_name','trainer_id','age','sex']
MODEL_NAMES=['M0','M_sire','M_dam','M_kin','M_trainer','M_trainer_kin','M_name']
FEATURES=['sire','dam','kin','trainer','name']
GRID=(0.,.25,.5,1.)
JRA={'札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉','Tokyo'}

def clean_id(s):
    x=s.fillna('').astype(str).str.strip()
    return x.mask(x.str.fullmatch(r'0+|(?i:nan|none|null|na)|[-－]+',na=False),'')

def prepare_frame(frame):
    """Normalize records; retain full, untied classified finishing orders only."""
    if not set(COLS).issubset(frame.columns): raise ValueError('MISSING_SOURCE_COLUMNS')
    d=pd.DataFrame(index=frame.index)
    d['day']=pd.to_datetime(frame.date,format='mixed',errors='coerce')
    d['year']=d.day.dt.year.fillna(0).astype('int16')
    d['horse']=clean_id(frame.horse_id);d['sire_id']=clean_id(frame.sire_id);d['dam_id']=clean_id(frame.dam_id)
    d['trainer_id']=clean_id(frame.trainer_id)
    d['meisho']=frame.horse_name.fillna('').astype(str).str.match(r'(?i)^(メイショウ|meisho)')
    track=frame.track.fillna('').str.strip().str.lower()
    d['surface']=track.replace({'芝':'turf','ダ':'dirt','ダート':'dirt'})
    d['distance']=pd.to_numeric(frame.distance.astype(str).str.extract(r'^(\d+)(?:[mM])?$')[0],errors='coerce')
    d['rank']=pd.to_numeric(frame.place,errors='coerce')
    d['course']=frame.racecourse.fillna('').astype(str).str.strip()
    d['circuit']=np.where(d.course.isin(JRA),'JRA','NAR')
    number=pd.to_numeric(frame.race_number,errors='coerce')
    d['race']=d.day.dt.strftime('%Y-%m-%d').fillna('')+'|'+d.course+'|'+number.fillna(-1).astype('int16').astype(str)
    qa={'input_rows':int(len(d)),'all_source_horses':int(d.horse[d.horse!=''].nunique()),'all_source_races':int(d.race.nunique()),
        'track_rows':{str(k):int(v) for k,v in frame.track.value_counts().items()},
        'source_date_min':str(d.day.min().date()),'source_date_max':str(d.day.max().date()),
        'year_rows':{str(k):int(v) for k,v in d.year.value_counts().sort_index().items()}}
    valid=d.day.notna() & d.horse.ne('') & d.course.ne('') & number.between(1,20) & d.surface.isin(['turf','dirt']) & d.distance.between(600,3600)
    qa['rows_outside_predeclared_flat_racing_scope']=int((~valid).sum())
    d=d[valid].copy()
    if d.duplicated(['horse','race']).any(): raise ValueError('DUPLICATE_HORSE_RACE_SOURCE_ROWS')
    qa['rows_without_positive_integer_finish']=int((~(d['rank'].ge(1) & (d['rank']%1==0))).sum())
    d=d[d['rank'].ge(1) & (d['rank']%1==0)].copy()
    r=d.groupby('race',observed=True).agg(n=('rank','size'),lo=('rank','min'),hi=('rank','max'),unique=('rank','nunique'),surfaces=('surface','nunique'),distances=('distance','nunique'))
    good=r.index[(r.n>=2)&(r.lo==1)&(r.hi==r.n)&(r.unique==r.n)&(r.surfaces==1)&(r.distances==1)]
    qa['incomplete_or_tied_races']=int(len(r)-len(good));qa['valid_complete_races']=int(len(good))
    d=d[d.race.isin(good)].copy()
    d['field']=d.race.map(r.n).astype('int16')
    d['y']=((d['rank']-1)/(d.field-1)).astype('float64')
    d['stratum']=d.circuit+':'+d.surface+':'+(d.distance//400).astype('int16').astype(str)
    first=d.groupby('horse',observed=True).day.transform('min')
    d['first_recorded']=d.day.eq(first)
    qa['analysis_rows']=int(len(d));qa['analysis_horses']=int(d.horse.nunique());qa['analysis_meisho_horses']=int(d.loc[d.meisho,'horse'].nunique())
    parent=d[['horse','sire_id','dam_id']].drop_duplicates()
    clash=parent.groupby('horse',observed=True).size()
    qa['horses_with_inconsistent_parent_pairs']=int((clash>1).sum())
    qa['horses_with_known_sire']=int(d.loc[d.sire_id.ne(''),'horse'].nunique())
    qa['horses_with_known_dam']=int(d.loc[d.dam_id.ne(''),'horse'].nunique())
    for k in ['horse','sire_id','dam_id','trainer_id','course','surface','stratum','circuit','race']:d[k]=d[k].astype('category')
    return d.sort_values(['day','race','horse']).reset_index(drop=True),qa

def profile_pairs(data):
    p=data[['horse','sire_id','dam_id']].drop_duplicates()
    n=p.groupby('horse',observed=True).size();bad=set(n[n>1].index)
    p=p[~p.horse.isin(bad)]
    s=p[p.sire_id.ne('')].groupby('sire_id',observed=True).size()
    d=p[p.dam_id.ne('')].groupby('dam_id',observed=True).size()
    b=p[p.sire_id.ne('')&p.dam_id.ne('')].groupby(['sire_id','dam_id'],observed=True).size()
    choose=lambda a:int(((a*(a-1))//2).sum())
    full=choose(b)
    return {'source_consistent_horses':int(len(p)),'inconsistent_parent_horses_quarantined':len(bad),
        'different_sires':int(len(s)),'different_dams':int(len(d)),
        'shared_sire_pairs':choose(s),'shared_dam_pairs':choose(d),'same_both_parents_pairs':full,
        'union_shared_parent_pairs':choose(s)+choose(d)-full,
        'all_horse_pairs_if_enumerated':int(len(p)*(len(p)-1)//2),
        'full_multigeneration_A_not_computed':True,'parent_ids_independently_studbook_verified':False}

def _peer_aggregates(history, future, group):
    """Distinct horse means in context, then group sum, excluding focal horse."""
    h=history[history[group].ne('')]
    p=h.groupby([group,'stratum','horse'],observed=True).y.mean().rename('v').reset_index()
    p['v']=p.v-.5
    g=p.groupby([group,'stratum'],observed=True).v.agg(['sum','size'])
    keys=pd.MultiIndex.from_frame(future[[group,'stratum']])
    v=g.reindex(keys).fillna(0)
    own=p.set_index([group,'stratum','horse']).v
    ownkeys=pd.MultiIndex.from_frame(future[[group,'stratum','horse']])
    q=own.reindex(ownkeys)
    own_present=q.notna().to_numpy()
    sums=v['sum'].to_numpy()-q.fillna(0).to_numpy()
    sizes=v['size'].to_numpy()-own_present.astype(float)
    return sums,np.maximum(sizes,0)

def make_features(history,future):
    if history.empty or future.empty:raise ValueError('EMPTY_TIME_WINDOW')
    if history.day.max()>=future.day.min():raise ValueError('TEMPORAL_OVERLAP_OR_SAME_DAY')
    f=future.reset_index(drop=True).copy()
    own=history.groupby('horse',observed=True).y.agg(['mean','size'])
    a=own.reindex(f.horse).fillna({'mean':.5,'size':0})
    own_n=a['size'].to_numpy();own_mean=a['mean'].to_numpy()
    base=.5+own_n/(own_n+5)*(own_mean-.5)
    ctx=history.groupby(['horse','stratum'],observed=True).y.agg(['mean','size'])
    c=ctx.reindex(pd.MultiIndex.from_frame(f[['horse','stratum']])).fillna({'mean':.5,'size':0})
    cn=c['size'].to_numpy();cm=c['mean'].to_numpy()
    base=base+cn/(cn+3)*(cm-base)
    factor=5/(own_n+5)
    hparents=history[['horse','sire_id','dam_id']].drop_duplicates()
    npar=hparents.groupby('horse',observed=True).size();conflict=set(npar[npar>1].index)
    h=history[~history.horse.isin(conflict)]
    ss,sn=_peer_aggregates(h,f,'sire_id');ds,dn=_peer_aggregates(h,f,'dam_id')
    ts,tn=_peer_aggregates(history,f,'trainer_id')
    hh=history.copy();ff=f.copy()
    hh['name_group']=np.where(hh.meisho,'MEISHO','');ff['name_group']=np.where(ff.meisho,'MEISHO','')
    ns,nn=_peer_aggregates(hh,ff,'name_group')
    f['base']=base;f['sire']=factor*ss/(8+sn);f['dam']=factor*ds/(8+dn)
    f['kin']=factor*(ss+ds)/(8+sn+dn)
    f['trainer']=factor*ts/(8+tn);f['name']=factor*ns/(8+nn)
    f['sire_relatives']=sn;f['dam_relatives']=dn;f['trainer_peers']=tn
    f['kin_exposed']=(sn+dn)>0;f['cold']=own_n==0;f['own_prior_count']=own_n
    return f

def _horse_weights(f):
    return 1/f.groupby('horse',observed=True).horse.transform('size').to_numpy(dtype=float)

def candidates():
    v={k:[] for k in MODEL_NAMES};v['M0']=[(0,0,0,0,0)]
    for j,name in enumerate(['M_sire','M_dam','M_kin','M_trainer','M_name']):
        for lam in GRID:
            w=[0.]*5;w[j]=lam;v[name].append(tuple(w))
    v['M_trainer_kin']=[(0.,0.,b,a,0.) for a,b in product(GRID,GRID)]
    return v

def fit_weights(features):
    x=features[FEATURES].to_numpy();base=features.base.to_numpy();y=features.y.to_numpy();weights=_horse_weights(features)
    selected={}
    for name,possible in candidates().items():
        def score(w):
            p=np.clip(base+x@np.asarray(w),0,1)
            return float(np.average((p-y)**2,weights=weights)),sum(w),w
        selected[name]=list(min(possible,key=score))
    return selected

def predict(features,weights):
    x=features[FEATURES].to_numpy();base=features.base.to_numpy()
    return np.column_stack([np.clip(base+x@np.asarray(weights[m]),0,1) for m in MODEL_NAMES])

def score_group(f,p):
    if len(f)==0:return {'rows':0,'horses':0,'models':None}
    weights=_horse_weights(f);error=p-f.y.to_numpy()[:,None]
    rmse=np.sqrt(np.average(error**2,axis=0,weights=weights));mae=np.average(abs(error),axis=0,weights=weights)
    return {'rows':int(len(f)),'horses':int(f.horse.nunique()),'races':int(f.race.nunique()),
        'models':{m:{'equal_horse_RMSE':float(rmse[j]),'equal_horse_MAE':float(mae[j]),'M0_minus_RMSE':float(rmse[0]-rmse[j])} for j,m in enumerate(MODEL_NAMES)}}

def bootstrap_pairs(f,p,seed=20261114,B=499):
    """Two separate single-way clustered bootstraps, not multiway causal CI."""
    y=f.y.to_numpy();w=_horse_weights(f);sq=(p-y[:,None])**2
    results={}
    for label,clusters in [('sire_family',f.sire_id.astype(str).where(f.sire_id.ne(''),'H:'+f.horse.astype(str))),('race_day',f.day.astype(str))]:
        work=pd.DataFrame(sq*w[:,None],columns=MODEL_NAMES);work['w']=w;work['cluster']=clusters.to_numpy()
        sums=work.groupby('cluster',observed=True).sum().to_numpy();G=len(sums)
        rng=np.random.default_rng(seed);draws=[]
        for _ in range(B):
            sample=sums[rng.integers(0,G,G)].sum(axis=0);r=np.sqrt(sample[:-1]/sample[-1])
            draws.append([r[0]-r[3],r[4]-r[5]])
        a=np.asarray(draws)
        results[label]={'clusters':G,'draws':B,'kin_vs_own_RMSE_gain_2_5_97_5':np.quantile(a[:,0],[.025,.975]).tolist(),
            'kin_plus_trainer_vs_trainer_RMSE_gain_2_5_97_5':np.quantile(a[:,1],[.025,.975]).tolist()}
    return results

def run_analysis(frame,years=(2019,2020,2021),source_digest=None):
    start=time.monotonic();d,qa=prepare_frame(frame);pair=profile_pairs(d)
    print(json.dumps({'stage':'SOURCE_AND_OUTCOME_QA','quality':qa,'direct_parent_pairs':pair},ensure_ascii=False),flush=True)
    reports=[];preds=[];future_frames=[]
    for year in years:
        train=d[d.year<year-1];validation=d[d.year==year-1]
        val=make_features(train,validation);weights=fit_weights(val)
        hist=d[d.year<year];test=d[d.year==year]
        f=make_features(hist,test);p=predict(f,weights)
        masks={'all':np.ones(len(f),bool),'unseen_at_year_start':f.cold.to_numpy(),'first_recorded_start':(f.cold&f.first_recorded).to_numpy(),
            'Meisho':f.meisho.to_numpy(),'JRA':f.circuit.eq('JRA').to_numpy(),'NAR':f.circuit.eq('NAR').to_numpy(),
            'kin_exposed':f.kin_exposed.to_numpy()}
        report={'test_year':int(year),'training_end':str(hist.day.max().date()),'tuning_year':int(year-1),
            'test_start':str(test.day.min().date()),'test_end':str(test.day.max().date()),'weights_order':FEATURES,'validation_selected_weights':weights,
            'support':{'test_rows':len(f),'test_horses':int(f.horse.nunique()),'kin_exposed_rows':int(f.kin_exposed.sum()),
                'sire_relatives_median':float(f.sire_relatives.median()),'dam_relatives_median':float(f.dam_relatives.median())},
            'groups':{g:score_group(f.loc[m],p[m]) for g,m in masks.items()}}
        print(json.dumps({'stage':'YEAR_SCORED','year':year,'results':report},ensure_ascii=False),flush=True)
        reports.append(report);future_frames.append(f[['horse','day','year','race','y','cold','first_recorded','meisho','sire_id','dam_id','circuit']]);preds.append(p)
        del val,train,validation,hist,test;gc.collect()
    combined=pd.concat(future_frames,ignore_index=True);pr=np.vstack(preds)
    aggregate={'all':score_group(combined,pr),'Meisho':score_group(combined[combined.meisho],pr[combined.meisho.to_numpy()])}
    ci=bootstrap_pairs(combined,pr)
    return {'status':('REAL_PUBLIC_ARCHIVE_RETROSPECTIVE_TEMPORAL_RANK_TEST_NOT_PROSPECTIVE' if source_digest==SOURCE_SHA else 'UNVERIFIED_INPUT_TEMPORAL_RANK_TEST'),
        'source':{'publisher':'ayuser','url':'https://www.kaggle.com/datasets/ayuser/horse-racing-in-japan','archive_sha256':source_digest,'archive_digest_verified':source_digest==SOURCE_SHA,
                  'declared_redistribution_license':'Unknown','raw_data_or_individual_scores_redistributed':False},
        'outcome':'normalized_classified_finishing_rank_0_best_1_last','quality':qa,'direct_parent_structure':pair,
        'years':reports,'pooled':aggregate,'paired_clustered_bootstrap':ci,'seconds':round(time.monotonic()-start,3),
        'limitations':['Archive is a secondary public source; its redistribution licence is Unknown, not a rights-cleared official JRA/NAR export.',
            'Only complete, untied classified finishing orders in flat turf/dirt races 600-3600m; not all starts or a national census.',
            'Same-parent score is not multigeneration pedigree A, genomic G, heritability or genetic causation.',
            'The pedigree and trainer fields are retrospectively collected, with no independently verified historical publication timestamps.',
            'Future outcome leakage is blocked by year cutoffs, but this is retrospective validation, not genuinely prospective.',
            'Model histories are frozen at year start, including for later test-year races; first recorded start is not confirmed debut.',
            'Rank is a relative outcome conditional on race entry/competition. No GPS phenotype, calibrated win probability or betting profit is estimated.',
            'Single-way sire-family and day bootstrap intervals are sensitivity summaries, not a joint multiway population inference.']}

def download(path):
    h=hashlib.sha256();n=0
    with urlopen(Request(SOURCE,headers={'User-Agent':'keiba-research/1.0'}),timeout=90) as f,path.open('wb') as w:
        while b:=f.read(1024*1024):
            n+=len(b)
            if n>250_000_000:raise ValueError('SOURCE_SIZE_LIMIT')
            h.update(b);w.write(b)
    if h.hexdigest()!=SOURCE_SHA:raise ValueError('SOURCE_SHA_CHANGED')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path);ap.add_argument('--summary',type=Path,required=True);args=ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        archive=args.archive or Path(td)/'source.zip'
        if not args.archive:download(archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('SOURCE_SHA_CHANGED')
        with zipfile.ZipFile(archive) as z,z.open('2010-2021.csv') as f:
            frame=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
        result=run_analysis(frame,source_digest=SOURCE_SHA)
    args.summary.parent.mkdir(parents=True,exist_ok=True);args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FINAL_AGGREGATE_JSON\n'+json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
