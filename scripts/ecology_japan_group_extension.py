#!/usr/bin/env python3
"""Beyond-Meisho subgroup replay of PR45's *unchanged* frozen predictions.

Exploratory subgroup descriptions, not prospective confirmation, ownership
classification or genetic causation. No row-level source data are exported.
Run inside zuizui0223/keiba at base 12d6cf65683fb4b527d38fc7a5d92ee127227495.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata
import zipfile

import numpy as np
import pandas as pd

MODELS = ['M0','M_sire','M_dam','M_kin','M_trainer','M_trainer_kin','M_name']
SOURCE_SHA = 'c72d280ce82b583686caca6773fd1a7589917f9b10b96a25f8d4e96f9b7a4a8f'
# Exact strings define descriptive name groups, NOT verified owner groups.
ALIASES = {
 'メイショウ':['meisho'], 'マイネル':['meiner'], 'マイネ':['meine'],
 'ウイン':['win'], 'シゲル':['shigeru'], 'テイエム':['t m','tm','teiemu'],
 'エイシン':['eishin'], 'エーシン':['a shin','a-shin'], 'サクラ':['sakura'],
 'ナリタ':['narita'], 'アドマイヤ':['admire'], 'タガノ':['tagano'],
 'ダノン':['danon'], 'サトノ':['satono'], 'ショウナン':['shonan'],
 'トーセン':['tosen'], 'カレン':['curren'], 'コスモ':['cosmo'],
 'ロード':['lord'], 'レッド':['red'], 'サンライズ':['sunrise'],
 'スマート':['smart'], 'スズカ':['suzuka'], 'ニホンピロ':['nihon pillow','nihonpiro'],
 'シンボリ':['symboli'], 'セイウン':['seiun'], 'ニシノ':['nishino'],
 'タイキ':['taiki'], 'アグネス':['agnes'], 'ダイワ':['daiwa'],
 'カシノ':['kashino'], 'クリノ':['kurino'], 'ナムラ':['namura'],
 'デルマ':['derma'], 'テーオー':['t o','to','teio'], 'ホッコー':['hokko'],
 'ウォーター':['water'], 'マテンロウ':['matenro'],
}

def normalized_name(value) -> str:
    if not isinstance(value,str): return ''
    x=unicodedata.normalize('NFKC',value).strip().casefold()
    x=x.replace('.','').replace('・','').replace('-',' ')
    return re.sub(r'\s+',' ',x)

# Japanese starts-with; romanized aliases require a token boundary.
MATCHERS=sorted([(normalized_name(a),label,a==label) for label,aliases in ALIASES.items()
                 for a in [label]+aliases],key=lambda z:len(z[0]),reverse=True)

def prefix_label(name) -> str:
    x=normalized_name(name)
    for alias,label,japanese in MATCHERS:
        if (japanese and x.startswith(alias)) or (not japanese and (x==alias or x.startswith(alias+' '))):
            return label
    return 'OTHER_UNMATCHED'

def source_labels(source:pd.DataFrame):
    """No name-based identity join; conflicting classifications are quarantined."""
    unique=source[['horse_id','horse_name']].drop_duplicates().copy()
    unique['label']=unique.horse_name.map(prefix_label)
    per=unique.groupby('horse_id',observed=True).label.agg(lambda s: sorted(set(s)))
    mapping={str(h):values[0] if len(values)==1 else 'AMBIGUOUS_NAME_GROUP' for h,values in per.items()}
    audit={'source_horse_ids':len(mapping),'conflicting_name_group_horses':sum(len(v)>1 for v in per),
           'name_group_definitions':len(ALIASES),'verified_owner_or_breeder_assignment':False}
    labels={}
    if {'sire_id','sire'}.issubset(source.columns):
        # Display label only: the grouping key is the unchanged supplied sire ID.
        entries=source[['sire_id','sire']].fillna('').astype(str)
        counts=entries.groupby(['sire_id','sire'],observed=True).size().reset_index(name='n')
        for sire,part in counts.groupby('sire_id',observed=True):
            if sire and not set(sire)=={'0'}:
                ranked=part.sort_values(['n','sire'],ascending=[False,True])
                labels[sire]=ranked.iloc[0]['sire']
        audit['sire_ids_with_multiple_display_labels']=int((counts.groupby('sire_id',observed=True).size()>1).sum())
    return mapping,audit,labels

def select_sires(data:pd.DataFrame,top_n:int=20):
    past=data.loc[(data.year<2019)&data.sire_id.ne(''),['horse','sire_id']].drop_duplicates()
    sizes=past.groupby('sire_id',observed=True).horse.nunique()
    return sorted(((str(k),int(v)) for k,v in sizes.items()),key=lambda kv:(-kv[1],kv[0]))[:top_n]

def _weights(f):
    return 1/f.groupby('horse',observed=True).horse.transform('size').to_numpy(dtype=float)

def _check(f,p):
    if p.shape!=(len(f),len(MODELS)):raise ValueError('PREDICTION_ALIGNMENT_FAILED')
    if not np.isfinite(p).all():raise ValueError('NONFINITE_PREDICTIONS')
    if len(f) and not np.isfinite(f.y.to_numpy(dtype=float)).all():raise ValueError('NONFINITE_OUTCOME')

def scores(f:pd.DataFrame,p:np.ndarray) -> dict:
    _check(f,p)
    if f.empty:return {'rows':0,'horses':0,'races':0,'rmse':None}
    w=_weights(f);y=f.y.to_numpy(dtype=float)
    mse=np.average((p-y[:,None])**2,weights=w,axis=0)
    rmse={name:float(np.sqrt(mse[i])) for i,name in enumerate(MODELS)}
    rmse['neutral']=float(np.sqrt(np.average((y-.5)**2,weights=w)))
    r={'rows':len(f),'horses':int(f.horse.nunique()),'races':int(f.race.nunique()),'rmse':rmse,
       'gain_neutral_minus_kin':rmse['neutral']-rmse['M_kin'],
       'gain_neutral_minus_joint':rmse['neutral']-rmse['M_trainer_kin'],
       'gain_own_minus_kin':rmse['M0']-rmse['M_kin'],
       'gain_trainer_minus_joint':rmse['M_trainer']-rmse['M_trainer_kin'],
       'support_status':'AT_LEAST_100_TEST_HORSES' if f.horse.nunique()>=100 else 'SMALL_SUBGROUP_DESCRIPTIVE_ONLY'}
    r['JRA_row_fraction']=float(f.circuit.eq('JRA').mean())
    r['JRA_equal_horse_weight_fraction']=float(np.average(f.circuit.eq('JRA').to_numpy(),weights=w))
    r['cold_row_fraction']=float(f.cold.mean())
    return r

def check_reference(f,p,reference):
    result=scores(f,p)
    if result['rows']!=reference['rows'] or result['horses']!=reference['horses']:
        raise ValueError('PRIMARY_CASES_CHANGED')
    for name in MODELS:
        if abs(result['rmse'][name]-reference['models'][name]['equal_horse_RMSE'])>1e-10:
            raise ValueError('PRIMARY_SCORE_CHANGED_'+name)

def intervals(f:pd.DataFrame,p:np.ndarray,draws:int=399,seed:int=20261114,kind='prefix'):
    _check(f,p)
    if f.empty:return {}
    y=f.y.to_numpy(dtype=float);w=_weights(f)
    # Eight error columns: seven original models plus unfitted neutral.
    sq=np.column_stack([(p-y[:,None])**2,(y-.5)**2])
    totals=np.average(sq,weights=w,axis=0)**.5
    contrasts={'neutral_minus_kin':(7,3),'own_minus_kin':(0,3),
               'trainer_minus_joint':(4,5),'neutral_minus_joint':(7,5)}
    out={}
    first=f.sire_id.astype(str).where(f.sire_id.astype(str).ne(''),'H:'+f.horse.astype(str))
    clusters=[('sire',first),('day',f.day.astype(str))]
    if kind=='sire':clusters=[('horse',f.horse.astype(str)),('day',f.day.astype(str))]
    for label,c in clusters:
        data=pd.DataFrame(sq*w[:,None]);data['w']=w;data['cluster']=c.to_numpy()
        matrix=data.groupby('cluster',observed=True).sum().to_numpy();g=len(matrix)
        if g<20:
            out[label]={'status':'LOW_CLUSTER_SUPPORT','clusters':g};continue
        rng=np.random.default_rng(seed);sim=[]
        for _ in range(draws):
            summed=matrix[rng.integers(g,size=g)].sum(axis=0)
            sim.append(np.sqrt(summed[:-1]/summed[-1]))
        sim=np.asarray(sim)
        r={'status':'DESCRIPTIVE_POINTWISE_SINGLE_CLUSTER','clusters':g,'draws':draws,
           'not_multiple_comparison_adjusted':True}
        for name,(a,b) in contrasts.items():
            r[name]={'gain':float(totals[a]-totals[b]),'interval95':np.quantile(sim[:,a]-sim[:,b],[.025,.975]).tolist()}
        out[label]=r
    return out

def family_counts(data):
    p=data[['horse','sire_id','dam_id']].drop_duplicates()
    if p.groupby('horse',observed=True).size().gt(1).any():raise ValueError('PARENT_CONFLICT_IN_GROUP')
    s=p[p.sire_id.ne('')].groupby('sire_id',observed=True).size()
    d=p[p.dam_id.ne('')].groupby('dam_id',observed=True).size()
    b=p[p.sire_id.ne('')&p.dam_id.ne('')].groupby(['sire_id','dam_id'],observed=True).size()
    choose=lambda x:int((x*(x-1)//2).sum())
    a,c,e=choose(s),choose(d),choose(b)
    return {'horses':len(p),'distinct_sires':len(s),'distinct_dams':len(d),
            'shared_sire_pairs':a,'shared_dam_pairs':c,'full_sibling_pairs':e,
            'any_direct_shared_parent_pairs':a+c-e,'full_multigeneration_A':False}

def group_report(f,p,mask,kind='prefix',draws=399):
    subset=f.loc[mask].copy();pr=p[np.asarray(mask)]
    result={'all':scores(subset,pr)}
    result['by_year']={str(y):scores(subset[subset.year.eq(y)],pr[subset.year.eq(y).to_numpy()]) for y in [2019,2020,2021]}
    result['slices']={}
    filters={'JRA':subset.circuit.eq('JRA'),'NAR':subset.circuit.eq('NAR'),
             'first_recorded_start':subset.cold&subset.first_recorded,
             'seen_before_year_start':~subset.cold}
    for name,m in filters.items():result['slices'][name]=scores(subset.loc[m],pr[m.to_numpy()])
    result['intervals']=intervals(subset,pr,draws=draws,kind=kind)
    result['positive_years_vs_neutral']=sum(x.get('gain_neutral_minus_kin',0)>0 for x in result['by_year'].values())
    result['positive_years_kin_vs_own']=sum(x.get('gain_own_minus_kin',0)>0 for x in result['by_year'].values())
    return result

def run(archive:Path,primary_lock:Path,output:Path,draws=399):
    # Reuse the repository's existing pipeline; NO fit_weights call here.
    from ecology_japan_archive_forward import COLS,prepare_frame,make_features,predict
    start=time.monotonic();digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=SOURCE_SHA:raise ValueError('SOURCE_SHA_CHANGED')
    lock=json.loads(primary_lock.read_text(encoding='utf-8'))
    if lock['source_sha256']!=SOURCE_SHA:raise ValueError('REFERENCE_SOURCE_CHANGED')
    with zipfile.ZipFile(archive) as z,z.open('2010-2021.csv') as stream:
        raw=pd.read_csv(stream,usecols=COLS+['sire'],dtype=str,keep_default_na=False)
    mapping,audit,sire_labels=source_labels(raw)
    d,qa=prepare_frame(raw)
    if qa!=lock['quality']:raise ValueError('PRIMARY_COHORT_CHANGED')
    d['prefix']=d.horse.astype(str).map(mapping)
    if d.prefix.isna().any():raise ValueError('UNMAPPED_SOURCE_HORSE_ID')
    mismatch=d.prefix.eq('メイショウ')!=d.meisho
    audit['name_match_vs_original_meisho_flag_disagreement_rows']=int(mismatch.sum())
    audit['name_match_vs_original_meisho_flag_disagreement_horses']=int(d.loc[mismatch,'horse'].nunique())
    selected=select_sires(d,20)
    frames=[];predictions=[]
    for ref in lock['years']:
        year=ref['test_year'];f=make_features(d[d.year<year],d[d.year==year])
        p=predict(f,ref['validation_selected_weights'])
        check_reference(f,p,ref['all']);frames.append(f);predictions.append(p)
    f=pd.concat(frames,ignore_index=True);p=np.vstack(predictions)
    check_reference(f,p,lock['pooled_all'])
    print(json.dumps({'stage':'PRIMARY_REPLAY_VERIFIED','rows':len(f),'horses':int(f.horse.nunique()),'groups':len(ALIASES)},ensure_ascii=False),flush=True)
    name_groups={}
    for label in [*ALIASES,'OTHER_UNMATCHED','AMBIGUOUS_NAME_GROUP']:
        r=group_report(f,p,f.prefix.eq(label),draws=draws)
        r['source_parent_structure']=family_counts(d[d.prefix.eq(label)])
        name_groups[label]=r
    sire_groups=[]
    for sire,training_count in selected:
        r=group_report(f,p,f.sire_id.astype(str).eq(sire),kind='sire',draws=draws)
        # Only a parent-family display label and aggregated numbers, not row-level horse IDs.
        r['source_sire_label']=sire_labels.get(sire,'DISPLAY_LABEL_UNAVAILABLE')
        r['pre2019_distinct_offspring']=training_count
        sire_groups.append(r)
    nonmeisho=group_report(f,p,~f.meisho,draws=draws)
    report={'status':'REAL_SOURCE_REPLAY_SUBGROUP_EXTENSION_NO_MODEL_REFIT',
        'source_sha256':digest,'primary_lock_sha256':hashlib.sha256(primary_lock.read_bytes()).hexdigest(),
        'primary_refit':False,'all_original_annual_and_pooled_scores_verified':True,
        'new_subgroup_analysis_after_global_results':True,'original_source_license':'Unknown',
        'no_raw_records_or_individual_predictions_exported':True,'source_quality':qa,
        'name_classification_audit':audit,'fixed_prefix_aliases':ALIASES,'non_meisho':nonmeisho,
        'name_groups':name_groups,'training_size_selected_sire_families':sire_groups,
        'limits':['Name strings are NOT verified owner, breeder or true-prefix assignments; homonymous prefixes can be misclassified.',
            'Only starts-with labels; suffix crowns and rare or unlisted names are outside named strata.',
            'All groups shown including small and non-improving groups. Pointwise intervals not adjusted for multiplicity.',
            'Original 2019-2021 test outcomes have already been inspected; this subgroup expansion is exploratory.',
            'Same direct-parent history model, not complete pedigree A, genome G, heritability or betting return.',
            'Source is a secondary archive; Unknown redistribution licence. No official nationwide coverage claim.',
            'Year-start history is frozen; JRA/NAR and first-record subsets retain original selection and confounding limitations.'],
        'elapsed_seconds':round(time.monotonic()-start,3)}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'name_groups':len(name_groups),'sire_groups':len(sire_groups)},ensure_ascii=False))
    return report

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--archive',type=Path,required=True)
    a.add_argument('--primary-lock',type=Path,default=Path('docs/evidence/japan-group-primary-lock-20261114.json'))
    a.add_argument('--output',type=Path,required=True)
    a.add_argument('--draws',type=int,default=399)
    args=a.parse_args()
    if not 99<=args.draws<=1999:a.error('draws must be between 99 and 1999')
    run(args.archive,args.primary_lock,args.output,args.draws)

if __name__=='__main__':main()
