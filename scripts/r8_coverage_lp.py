#!/usr/bin/env python3
"""Exploratory maximin coverage LP using only saved, mixed-time odds quotes.

Continuous purchase weights; place/wide use displayed lower odds. No probabilities,
no live fetch, no bet execution, no claim of achievable fixed-odds arbitrage.
"""
import argparse
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import scipy
from scipy import sparse
from scipy.optimize import linprog


def solve(input_path):
    raw = input_path.read_bytes()
    data = json.loads(raw)
    outcomes = np.array(list(itertools.permutations(range(1, 12), 3)), dtype=int)
    frame_lookup = np.array([0] + [data['horse_frames'][str(h)] for h in range(1,12)])
    assert frame_lookup.tolist() == [0,1,2,3,4,5,6,6,7,7,8,8]
    frames = frame_lookup[outcomes]
    top2 = np.sort(outcomes[:, :2], axis=1)
    top3 = np.sort(outcomes, axis=1)
    frame2 = np.sort(frames[:, :2], axis=1)
    tickets, columns = [], []
    sizes = {k: len(v['quotes']) for k, v in data['markets'].items()}
    for kind, market in data['markets'].items():
        for quote in market['quotes']:
            s = np.array(quote['selection'], dtype=int)
            odds = float(quote['odds_low'])
            if not np.isfinite(odds) or odds < 1:
                raise ValueError('Invalid odds')
            if kind == 'win': hit = outcomes[:, 0] == s[0]
            elif kind == 'place': hit = np.any(outcomes == s[0], axis=1)
            elif kind == 'frame': hit = np.all(frame2 == np.sort(s), axis=1)
            elif kind == 'quinella': hit = np.all(top2 == np.sort(s), axis=1)
            elif kind == 'wide': hit = np.all(np.isin(outcomes, s).sum(axis=1)[:, None] == len(s), axis=1)
            elif kind == 'exacta': hit = np.all(outcomes[:, :2] == s, axis=1)
            elif kind == 'trio': hit = np.all(top3 == np.sort(s), axis=1)
            elif kind == 'trifecta': hit = np.all(outcomes == s, axis=1)
            else: raise ValueError('Unsupported market: ' + kind)
            columns.append(sparse.csc_matrix((hit.astype(float)*odds)[:, None]))
            tickets.append({'type': kind, 'selection': list(map(int,s)), 'odds_low': odds,
                            'updated_at_jst': market['updated_at_jst'],
                            'source_url': market['source_url']})
    A = sparse.hstack(columns, format='csc')
    n = len(tickets)
    # -A*x + t <= 0; sum(x)=1; x,t >=0; maximize t.
    Aub = sparse.hstack([-A, sparse.csc_matrix(np.ones((len(outcomes), 1)))], format='csc')
    Aeq = sparse.csc_matrix(np.array([[1.0]*n+[0.0]]))
    c = np.zeros(n+1); c[-1] = -1
    result = linprog(c, A_ub=Aub, b_ub=np.zeros(len(outcomes)), A_eq=Aeq,
                     b_eq=[1.0], bounds=(0,None), method='highs')
    if not result.success:
        raise RuntimeError(result.message)
    weights = result.x[:-1]; value = float(result.x[-1])
    returns = np.asarray(A @ weights).ravel()
    active = []
    for ticket, weight in zip(tickets, weights):
        if weight > 1e-8:
            active.append({**ticket, 'weight': float(weight)})
    active.sort(key=lambda t: -t['weight'])
    dual = -np.asarray(result.ineqlin.marginals)
    # Dual: y>=0, sum(y)=1, A.T*y <= z, minimize z.
    dual_bound = float(result.eqlin.marginals[0] * -1)
    dual_expected = np.asarray(A.T @ dual).ravel()
    check = {
        'weight_sum_minus_one': float(weights.sum()-1),
        'min_weight': float(weights.min()),
        'max_primal_coverage_violation': float(max(0.0,value-returns.min())),
        'minimum_recomputed_return': float(returns.min()),
        'maximum_recomputed_return': float(returns.max()),
        'dual_weight_sum_minus_one': float(dual.sum()-1),
        'min_dual_weight': float(dual.min()),
        'dual_upper_bound': dual_bound,
        'max_dual_constraint_violation': float(max(0.0,dual_expected.max()-dual_bound)),
        'primal_dual_gap': float(dual_bound-value),
        'binding_outcome_count_tolerance_1e_7': int(np.sum(np.abs(returns-value)<1e-7)),
    }
    assert abs(check['weight_sum_minus_one']) < 1e-7
    assert check['max_primal_coverage_violation'] < 1e-7
    assert abs(check['primal_dual_gap']) < 1e-7
    assert check['max_dual_constraint_violation'] < 1e-7
    # Verify payout definitions with direct independent membership checks.
    probe_outcome = (2,11,5)
    probe_frame = sorted([int(frame_lookup[h]) for h in probe_outcome[:2]])
    for index,t in enumerate(tickets):
        s=t['selection']; k=t['type']
        hit={'win': lambda:s[0]==probe_outcome[0],
             'place':lambda:s[0] in probe_outcome,
             'frame':lambda:sorted(s)==probe_frame,
             'quinella':lambda:set(s)==set(probe_outcome[:2]),
             'wide':lambda:set(s).issubset(probe_outcome),
             'exacta':lambda:tuple(s)==probe_outcome[:2],
             'trio':lambda:set(s)==set(probe_outcome),
             'trifecta':lambda:tuple(s)==probe_outcome}[k]()
        row=next(i for i,o in enumerate(outcomes) if tuple(o)==probe_outcome)
        assert A[row,index] == (t['odds_low'] if hit else 0)
    return {
        'race_id': data['race_id'], 'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'input_path':str(input_path),'input_sha256':hashlib.sha256(raw).hexdigest(),
        'versions':{'numpy':np.__version__,'scipy':scipy.__version__},
        'horse_frames':data['horse_frames'],
        'price_comparison':compare_prices(data),
        'conditional_5_11_budget_1000':conditional_budget(data),
        'solver':'scipy.optimize.linprog(method=highs)',
        'objective':'maximize minimum gross return / total purchase across all 11P3 outcomes',
        'outcome_count':int(len(outcomes)), 'available_ticket_count':n,
        'available_market_sizes':sizes,'full_market_sizes':data['expected_full_market_sizes'],
        'maximin_gross_return_multiplier':value,
        'maximin_net_return_fraction':value-1,
        'nonzero_ticket_count_tolerance_1e_8':len(active),
        'selected_tickets':active,'verification':check,
        'assumptions':['通常の同着なし上位3着、取消・返還なし。',
                       '複勝とワイドは表示下限オッズを全的中結果に固定。',
                       '枠連は馬番1→1枠、2→2枠、3→3枠、4→4枠、5→5枠、6・7→6枠、8・9→7枠、10・11→8枠。',
                       '購入比率は非負連続値。100円単位、予算、自己購入によるオッズ影響を未反映。',
                       '市場の更新時刻は混在し、中間オッズは購入時に固定されない。',
                       '3連複165組は全取得、3連単は400/990の部分取得。取得済み券に限定した最適値であり、全券種全組合せの最適値ではない。',
                       '結果確率は設定していない。期待利益の最大化、的中予測ではない。'],
        'reproduction_command':'python -B scripts/r8_coverage_lp.py --input '+str(input_path)
    }



def compare_prices(data):
    markets=data['markets']
    def quotes(k):return {tuple(q['selection']):q['odds_low'] for q in markets[k]['quotes']}
    quin,ex,tri,st,fr=[quotes(k) for k in ['quinella','exacta','trio','trifecta','frame']]
    pairs=[]
    for pair,plain in quin.items():
        reverse=pair[::-1]
        if pair not in ex or reverse not in ex:continue
        synthetic=1/(1/ex[pair]+1/ex[reverse])
        pairs.append({'horses':pair,'quinella_odds':plain,'exacta_orders':[{'selection':pair,'odds':ex[pair]},{'selection':reverse,'odds':ex[reverse]}],'exacta_equal_return_multiplier':synthetic,'preferred_equal_return_market':'quinella' if plain>=synthetic else 'exacta_dutch'})
    triples=[]
    for triple,plain in tri.items():
        orders=list(itertools.permutations(triple))
        if not all(o in st for o in orders):continue
        synthetic=1/sum(1/st[o] for o in orders)
        triples.append({'horses':triple,'trio_odds':plain,'trifecta_equal_return_multiplier':synthetic,'trifecta_orders':[{'selection':o,'odds':st[o]} for o in orders],'preferred_equal_return_market':'trio' if plain>=synthetic else 'trifecta_dutch'})
    frame_pairs=[]
    mapping={int(h):f for h,f in data['horse_frames'].items()}
    for frames,plain in fr.items():
        covered=[p for p in quin if sorted([mapping[h] for h in p])==list(frames)]
        synthetic=1/sum(1/quin[p] for p in covered)
        frame_pairs.append({'frames':frames,'covered_horse_pairs':covered,'frame_odds':plain,'quinella_equal_return_multiplier':synthetic,'preferred_equal_return_market':'frame' if plain>=synthetic else 'quinella_dutch'})
    direct_dominance=[]
    for row in frame_pairs:
        for pair in row['covered_horse_pairs']:
            if row['frame_odds'] > quin[pair]:
                direct_dominance.append({'frame':row['frames'],'frame_odds':row['frame_odds'],'horse_pair':pair,'quinella_odds':quin[pair],'frame_covers_horse_pairs':row['covered_horse_pairs'],'same_event':len(row['covered_horse_pairs'])==1,'payout_ratio':row['frame_odds']/quin[pair]})
    selected={1,3,5,9,11}
    return {'market_timestamps':{k:v['updated_at_jst'] for k,v in markets.items()},'frame_pointwise_dominance_at_saved_quotes':direct_dominance,'pair_comparisons':pairs,'triple_comparisons_with_all_six_orders_available':triples,'frame_comparisons':frame_pairs,'candidate_pair_comparisons':[p for p in pairs if set(p['horses']).issubset(selected)],'candidate_triple_comparisons':[p for p in triples if set(p['horses']).issubset(selected)],'note':'同一的中条件の払戻均等連続配分。市場時刻は混在、100円単位は未反映。三連単6順序の1つでも未取得なら比較しない。期待値・的中率の比較ではない。'}



def conditional_budget(data):
    ex={tuple(q['selection']):q['odds_low'] for q in data['markets']['exacta']['quotes']}
    pair={tuple(q['selection']):q['odds_low'] for q in data['markets']['quinella']['quotes']}
    a,b,c=ex[(11,5)],ex[(5,11)],pair[(5,11)]
    best=None
    for ka in range(11):
        for kb in range(11-ka):
            kc=10-ka-kb
            r1=100*(ka*a+kc*c);r2=100*(kb*b+kc*c)
            result=(min(r1,r2),ka,kb,kc,r1,r2)
            if best is None or result[0]>best[0]+1e-9:best=result
    return {'budget_yen':1000,'stake_unit_yen':100,'condition':'5番・11番が1着と2着を占めると仮定した2結果のみ。',
            'odds':{'11_to_5':a,'5_to_11':b,'quinella_5_11':c},
            'stake_yen':{'11_to_5':100*best[1],'5_to_11':100*best[2],'quinella_5_11':100*best[3]},
            'payout_yen':{'11_first_5_second':round(best[4]),'5_first_11_second':round(best[5])},
            'minimum_conditional_payout_yen':round(best[0]),'minimum_conditional_net_yen':round(best[0]-1000),
            'allocations_enumerated':66,'prediction_probabilities_assigned':False,
            'outside_condition_payout_yen':0,'market_updated_at_jst':{k:data['markets'][k]['updated_at_jst'] for k in ['exacta','quinella']},
            'note':'条件を満たさなければ全券外れ。全結果保証や予算増額の推薦ではない。表示オッズを固定した整数配分の比較。'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path('data/2026-10-12/r8_markets.json'))
    p.add_argument('--output',type=Path,default=Path('reports/r8-coverage-lp.json'))
    a=p.parse_args(); result=solve(a.input)
    result['reproduction_command'] += ' --output '+str(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['outcome_count','available_ticket_count','maximin_gross_return_multiplier','nonzero_ticket_count_tolerance_1e_8','verification']},ensure_ascii=False))
    print(json.dumps(result['selected_tickets'][:12],ensure_ascii=False))

if __name__=='__main__': main()
