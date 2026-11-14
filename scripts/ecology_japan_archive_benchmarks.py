#!/usr/bin/env python3
"""Unfitted midpoint benchmark added after the first frozen primary result.

No primary model, weight, input cohort, or test target is reselected here.
Replays source-locked primary weights and checks every annual baseline score.
Only anonymous aggregate output; original archive licence remains Unknown.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from ecology_japan_archive_forward import (SOURCE_SHA,COLS,MODEL_NAMES,prepare_frame,make_features,predict,score_group)

def _weights(ids):
    s=pd.Series(ids,dtype='str');n=s.value_counts();return 1/s.map(n).to_numpy(dtype=float)

def midrank_score(y,horse_ids):
    e=np.asarray(y,dtype=float)-.5;w=_weights(horse_ids)
    return {'RMSE':float(np.sqrt(np.average(e*e,weights=w))),'MAE':float(np.average(abs(e),weights=w))}

def cluster_comparison(y,p,horse_ids,clusters,B=499,seed=20261114):
    y=np.asarray(y,dtype=float);p=np.asarray(p,dtype=float);w=_weights(horse_ids)
    n=(y-.5)**2;m=(y-p)**2
    data=pd.DataFrame({'null':n*w,'model':m*w,'weight':w,'cluster':np.asarray(clusters)})
    groups=data.groupby('cluster',observed=True)[['null','model','weight']].sum().to_numpy();g=len(groups)
    rng=np.random.default_rng(seed);scores=[]
    for _ in range(B):
        x=groups[rng.integers(0,g,g)].sum(axis=0);scores.append(np.sqrt(x[0]/x[2])-np.sqrt(x[1]/x[2]))
    gain=np.sqrt(np.average(n,weights=w))-np.sqrt(np.average(m,weights=w))
    return {'midrank_minus_model_RMSE':float(gain),'clusters':g,'draws':B,'percentile_95_interval':np.quantile(scores,[.025,.975]).tolist()}

def evaluate(archive,primary):
    if primary['source']['archive_sha256']!=SOURCE_SHA or not primary['source']['archive_digest_verified']:raise ValueError('PRIMARY_SOURCE_NOT_VERIFIED')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('ARCHIVE_SOURCE_CHANGED')
    with zipfile.ZipFile(archive) as z,z.open('2010-2021.csv') as f:
        frame=pd.read_csv(f,usecols=COLS,dtype=str,keep_default_na=False)
    d,qa=prepare_frame(frame)
    if qa!=primary['quality']:raise ValueError('SOURCE_COHORT_NOT_IDENTICAL')
    annual=[];all_f=[];all_p=[]
    for report in primary['years']:
        year=report['test_year'];f=make_features(d[d.year<year],d[d.year==year]);p=predict(f,report['validation_selected_weights'])
        check=score_group(f,p)
        if check['rows']!=report['groups']['all']['rows']:raise ValueError('PRIMARY_CASES_CHANGED')
        for m in MODEL_NAMES:
            if abs(check['models'][m]['equal_horse_RMSE']-report['groups']['all']['models'][m]['equal_horse_RMSE'])>1e-10:raise ValueError('PRIMARY_SCORES_CHANGED')
        annual.append({'year':year,'midrank':midrank_score(f.y,f.horse),'unchanged_primary_RMSE':{m:check['models'][m]['equal_horse_RMSE'] for m in MODEL_NAMES}})
        all_f.append(f);all_p.append(p)
    f=pd.concat(all_f,ignore_index=True);p=np.vstack(all_p)
    masks={'all':np.ones(len(f),bool),'Meisho':f.meisho.to_numpy(),'JRA':f.circuit.eq('JRA').to_numpy(),'NAR':f.circuit.eq('NAR').to_numpy(),'first_recorded_start':(f.cold&f.first_recorded).to_numpy(),'unseen_at_year_start':f.cold.to_numpy()}
    groups={}
    for name,mask in masks.items():
        a=f.loc[mask];v=p[mask];score=score_group(a,v);neutral=midrank_score(a.y,a.horse)
        groups[name]={'rows':len(a),'horses':int(a.horse.nunique()),'midrank':neutral,'models':score['models'],
            'midrank_minus_model_RMSE':{m:neutral['RMSE']-score['models'][m]['equal_horse_RMSE'] for m in MODEL_NAMES}}
    ci={}
    for m in ['M0','M_kin','M_trainer_kin']:
        ci[m]={}
        for name,c in [('sire_family',f.sire_id.astype(str)),('race_day',f.day.astype(str))]:
            ci[m][name]=cluster_comparison(f.y,p[:,MODEL_NAMES.index(m)],f.horse,c)
    return {'status':'REAL_SOURCE_LOCKED_MIDRANK_BENCHMARK_WITH_UNCHANGED_PRIMARY_MODELS','archive_sha256':SOURCE_SHA,
        'added_after_first_primary_result':True,'no_primary_refitting_or_weight_selection':True,'annual':annual,'pooled_groups':groups,
        'paired_single_way_cluster_bootstrap':ci,'limits':['Midpoint uses no fitted parameters. Added diagnostically after first primary run; no primary result was tuned again.',
        'Retrospective held-out rank analysis, not a prospective forecast, genome effect, heritability, or wagering return.',
        'Same secondary archive and Unknown redistribution licence; no raw records or individual predictions published.']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--primary-summary',type=Path,required=True);ap.add_argument('--summary',type=Path,required=True);a=ap.parse_args()
    report=evaluate(a.archive,json.loads(a.primary_summary.read_text(encoding='utf-8')))
    a.summary.parent.mkdir(parents=True,exist_ok=True);a.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
