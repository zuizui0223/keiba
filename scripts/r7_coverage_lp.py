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
    outcomes = np.array(list(itertools.permutations(range(1, 17), 3)), dtype=int)
    frames = (outcomes + 1) // 2
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
    probe_outcome = (2,15,5)
    probe_frame = sorted([(h+1)//2 for h in probe_outcome[:2]])
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
        'solver':'scipy.optimize.linprog(method=highs)',
        'objective':'maximize minimum gross return / total purchase across all 16P3 outcomes',
        'outcome_count':int(len(outcomes)), 'available_ticket_count':n,
        'available_market_sizes':sizes,'full_market_sizes':data['expected_full_market_sizes'],
        'maximin_gross_return_multiplier':value,
        'maximin_net_return_fraction':value-1,
        'nonzero_ticket_count_tolerance_1e_8':len(active),
        'selected_tickets':active,'verification':check,
        'assumptions':['通常の同着なし上位3着、取消・返還なし。',
                       '複勝とワイドは表示下限オッズを全的中結果に固定。',
                       '枠連は馬番1・2が1枠、3・4が2枠、以降同様で15・16が8枠。',
                       '購入比率は非負連続値。100円単位、予算、自己購入によるオッズ影響を未反映。',
                       '市場の更新時刻は混在し、中間オッズは購入時に固定されない。',
                       '3連複・3連単は部分取得。取得済み券に限定した最適値であり、全券種全組合せの最適値ではない。',
                       '結果確率は設定していない。期待利益の最大化、的中予測ではない。'],
        'reproduction_command':'python -B scripts/r7_coverage_lp.py --input data/2026-10-12/r7_markets.json --output reports/2026-10-12/r7-coverage-lp.json'
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path('data/2026-10-12/r7_markets.json'))
    p.add_argument('--output',type=Path,default=Path('reports/2026-10-12/r7-coverage-lp.json'))
    a=p.parse_args(); result=solve(a.input)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['outcome_count','available_ticket_count','maximin_gross_return_multiplier','nonzero_ticket_count_tolerance_1e_8','verification']},ensure_ascii=False))
    print(json.dumps(result['selected_tickets'][:12],ensure_ascii=False))

if __name__=='__main__': main()
