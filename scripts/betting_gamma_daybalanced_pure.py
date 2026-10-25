#!/usr/bin/env python3
"""No-dependency reference for Kikuka 2026's experimental day-balanced gamma mixture.

The dated log-loss pseudo-posterior is NOT a calibrated Bayesian posterior.
No 2026-10-25 results are accessed. Original Oct24/Oct25 seals are immutable.
"""
import argparse
import hashlib
from itertools import permutations
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

GAMMAS = tuple(round(.5+.05*i,2) for i in range(37))
SIGMAS = (.25,.50,.75)
DATES = ("2026-10-12", "2026-10-18")
SOURCE_SCHEMA="KEIBA_KIKKA_LOCAL_PRICE_VECTOR_V1"
HISTORY_SCHEMA="KEIBA_TWO_MEETING_DATE_HISTORICAL_GAMMA_LOGLOSS_V1"
POST = datetime.fromisoformat('2026-10-25T15:40:00+09:00')
RACE = '2026-10-25-KYOTO-11'


def sha(doc):
    return hashlib.sha256(json.dumps(doc,ensure_ascii=False,sort_keys=True,
                                  separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_source(s):
    if (s.get('schema')!=SOURCE_SCHEMA or s.get('race_id')!=RACE
            or s.get('runner_count')!=18
            or s.get('provider_publication_clock_verified') is not False):
        raise ValueError('HOLD_SOURCE_SCHEMA_OR_UNVERIFIED_CLOCK_FLAG')
    t=datetime.fromisoformat(s['source_page_retrieved_at_jst'])
    if t.utcoffset() is None or not t<POST-timedelta(minutes=10):
        raise ValueError('HOLD_PRICE_CAPTURE_TOO_LATE')
    if any(k in s for k in ('winner','result','finish_order','official_payout')):
        raise ValueError('HOLD_FUTURE_TARGET_LABEL_LEAK')
    q=s.get('odds_by_number',{})
    if set(q)!={str(i) for i in range(1,19)}:
        raise ValueError('HOLD_INCOMPLETE_FIELD')
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=1
           for v in q.values()):
        raise ValueError('HOLD_INVALID_WIN_QUOTE')
    return {int(k):float(v) for k,v in q.items()}


def validate_history(doc):
    if (doc.get('schema')!=HISTORY_SCHEMA
        or set(doc.get('by_meeting_date',{}))!=set(DATES)
        or tuple(doc.get('gamma_grid',[]))!=GAMMAS):
        raise ValueError('HOLD_WRONG_HISTORICAL_AGGREGATES')
    if len(doc.get('source_git_blob_sha',{}))!=8:
        raise ValueError('HOLD_MISSING_GIT_BLOB_PINS')
    out={}
    for day,n in zip(DATES,(5,9)):
        d=doc['by_meeting_date'][day]
        vals=d['mean_win_log_loss']
        if d.get('n_races')!=n or len(vals)!=len(GAMMAS) or any(
                type(x) not in (int,float) or not math.isfinite(x) or x<=0
                for x in vals):
            raise ValueError('HOLD_INVALID_DATE_SCORE_VECTOR')
        out[day]=tuple(vals)
    if abs(out[DATES[0]][10]-1.921389738634519)>1e-9 or abs(
           out[DATES[1]][10]-1.9118761430864737)>1e-9:
        raise ValueError('HOLD_BASELINE_SCORE_NOT_REPRODUCED')
    return out


def weights(history,sigma,dates=DATES):
    if sigma<=0 or not math.isfinite(sigma):
        raise ValueError('HOLD_INVALID_SIGMA')
    if not dates or any(d not in history for d in dates):
        raise ValueError('HOLD_DATE_SPLIT_MISMATCH')
    logw=[]
    for index,g in enumerate(GAMMAS):
        l=-.5*((g-1)/sigma)**2
        for date in dates:
            l-=history[date][index]-history[date][10]  # ONE pseudo-race/date
        logw.append(l)
    peak=max(logw)
    w=[math.exp(z-peak) for z in logw]
    tot=sum(w)
    return [v/tot for v in w]


def ordered_model(odds,gamma):
    ids=sorted(odds)
    rates={i:odds[i]**(-gamma) for i in ids}
    full=sum(rates.values())
    q={i:rates[i]/full for i in ids}
    out={}
    for i,j,k in permutations(ids,3):
        out[(i,j,k)]=(q[i]*(q[j]/(1-q[i]))*
                      (q[k]/(1-q[i]-q[j])))
    if not math.isclose(sum(out.values()),1,abs_tol=1e-10):
        raise AssertionError('PL_MASS_INVALID')
    return out


def marginals(ordered):
    horse={i:{'win':0.0,'top2':0.0,'top3':0.0} for i in range(1,19)}
    trio={}
    pair={}
    for (a,b,c),p in ordered.items():
        horse[a]['win']+=p
        for i in (a,b):horse[i]['top2']+=p
        for i in (a,b,c):horse[i]['top3']+=p
        t=tuple(sorted((a,b,c)))
        trio[t]=trio.get(t,0.0)+p
        for a1,b1 in ((a,b),(a,c),(b,c)):
            pairkey=tuple(sorted((a1,b1)))
            pair[pairkey]=pair.get(pairkey,0.0)+p
    if not (math.isclose(sum(x['win'] for x in horse.values()),1,abs_tol=1e-10)
            and math.isclose(sum(x['top2'] for x in horse.values()),2,abs_tol=1e-10)
            and math.isclose(sum(x['top3'] for x in horse.values()),3,abs_tol=1e-10)
            and math.isclose(sum(trio.values()),1,abs_tol=1e-10)
            and math.isclose(sum(pair.values()),3,abs_tol=1e-10)):
        raise AssertionError('MIXTURE_MASS_INVALID')
    return {'horses':{str(k):v for k,v in horse.items()},
            'wide':{'-'.join(map(str,k)):v for k,v in sorted(pair.items())},
            'trio':{'-'.join(map(str,k)):v for k,v in sorted(trio.items())}}


def predict(source,agg):
    odds=validate_source(source)
    hist=validate_history(agg)
    conditionals={g:ordered_model(odds,g) for g in GAMMAS}
    keys=list(next(iter(conditionals.values())))
    result={}
    for sigma in SIGMAS:
        wt=weights(hist,sigma)
        together={triple:sum(wt[i]*conditionals[g][triple]
                              for i,g in enumerate(GAMMAS)) for triple in keys}
        model=marginals(together)
        model['gamma_mean']=sum(g*w for g,w in zip(GAMMAS,wt))
        model['gamma_weights']=wt
        result[f'sigma_{sigma:.2f}']=model
    for name,g in [('market_gamma1',1.0),('point_gamma185',1.85)]:
        result[name]=marginals(conditionals[g])
    return {'schema':'KEIBA_KIKKA_DAY_BALANCED_PURE_REFERENCE_V1',
            'race_id':RACE,'source_sha256':sha(source),
            'aggregate_sha256':sha(agg),'original_oct24_forecasts_unchanged':True,
            'result_used':False,'models':result,
            'not_calibrated_and_not_a_valid_betting_roi':True}


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--source',type=Path,required=True)
    a.add_argument('--historical',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    result=predict(json.loads(args.source.read_text(encoding='utf8')),
                   json.loads(args.historical.read_text(encoding='utf8')))
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':'EXPLORATORY_NO_TARGET_OUTCOME','sha256':sha(result),
                      'gamma_mean_sigma05':result['models']['sigma_0.50']['gamma_mean']}))


if __name__=='__main__':main()
