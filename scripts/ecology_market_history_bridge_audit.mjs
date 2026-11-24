#!/usr/bin/env node
// Research-only archival bridge; run from repository root with Node >=18.
// No names, tokens, raw records or wagering outcomes are emitted.
import fs from 'node:fs';
import crypto from 'node:crypto';
function ensure(x,msg){if(!x)throw Error(msg)}

function horseToken(s){if(typeof s!=="string")return null;const u=s.match(/^https:\/\/([a-z0-9.-]+)(\/[^?#]*)(?:\?([^#]*))?(?:#.*)?$/);if(!u)return null;let [,h,p,q=""]=u,m=null,provider=null;const query=k=>{let entries=q.split("&").filter(v=>v.startsWith(k+"="));return entries.length===1?entries[0].slice(k.length+1):""};if(h==="sports.yahoo.co.jp"){m=p.match(/^\/keiba\/directory\/horse\/(\d{10})\/?$/);provider="yahoo"}else if(["db.netkeiba.com","db.sp.netkeiba.com"].includes(h)){m=p.match(/^\/horse\/(?:result\/)?(\d{10})\/?$/);provider="netkeiba"}else if(h==="race.sp.netkeiba.com"&&p==="/modal/horse.html"){m=query("horse_id").match(/^(\d{10})$/);provider="netkeiba"}else if(h==="own.netkeiba.com"&&p==="/db/horse.html"){m=query("id").match(/^(\d{10})$/);provider="netkeiba"}else if(h==="www.jbis.or.jp"){m=p.match(/^\/horse\/(\d{10})(?:\/record)?\/?$/);provider="jbis"}else if(h==="tospo-keiba.jp"){m=p.match(/^\/horse\/(\d{10})\/?$/);provider="tospo"}else if(["keibalab.jp","pc.keibalab.jp","www.keibalab.jp"].includes(h)){m=p.match(/^\/db\/horse\/(\d{10})\/?$/);provider="keibalab"}return m?{provider,token:m[1]}:null}

function normalize(s){ensure(typeof s==="string"&&s.trim(),"missing name");return s.normalize("NFKC").replace(/\s/g,"")}

function project(edges,n){const m=edges.reduce((a,e)=>a+e.z,0)/edges.length;const b=Array(n).fill(0);for(const e of edges){b[e.i]+=e.z-m;b[e.j]+=e.z-m}const a=b.map(x=>x/(n-2));let sst=0,sse=0;for(const e of edges){sst+=(e.z-m)**2;sse+=(e.z-m-a[e.i]-a[e.j])**2}ensure(sst>1e-20,"constant edge response");return 1-sse/sst}

function marketStructure(t,w,n){const ws=Array(n).fill(0);for(const q of t.quotes.win){let a=q.selection;ensure(a.length===1&&Number.isInteger(a[0])&&a[0]>=1&&a[0]<=n&&ws[a[0]-1]===0&&Number.isFinite(q.odds_low)&&q.odds_low>=1&&q.odds_low===q.odds_high,"invalid win");ws[a[0]-1]=1/q.odds_low}ensure(ws.every(x=>x>0),"missing win");const sum=ws.reduce((a,b)=>a+b,0),ps=ws.map(x=>x/sum);const pairs=new Map;for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)pairs.set(`${i},${j}`,0);for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(j!==i)for(let k=0;k<n;k++)if(k!==i&&k!==j){let p=ps[i]*ps[j]/(1-ps[i])*ps[k]/(1-ps[i]-ps[j]);for(let [a,b] of [[i,j],[i,k],[j,k]]){let key=`${Math.min(a,b)},${Math.max(a,b)}`;pairs.set(key,pairs.get(key)+p/3)}}ensure(Math.abs([...pairs.values()].reduce((a,b)=>a+b,0)-1)<1e-10,"PL pair mass");let seen=new Set;const quotes=w.quotes.wide.map(q=>{let a=q.selection;ensure(a.length===2&&a.every(x=>Number.isInteger(x)&&x>=1&&x<=n)&&a[0]!==a[1]&&Number.isFinite(q.odds_low)&&Number.isFinite(q.odds_high)&&q.odds_low>=1&&q.odds_high>=q.odds_low,"invalid pair");let [i,j]=a.map(x=>x-1).sort((a,b)=>a-b);let key=`${i},${j}`;ensure(!seen.has(key),"duplicate pair");seen.add(key);return {i,j,key,iv:1/Math.sqrt(q.odds_low*q.odds_high)}});ensure(seen.size===pairs.size,"incomplete pair board");const qsum=quotes.reduce((a,q)=>a+q.iv,0);return project(quotes.map(q=>({i:q.i,j:q.j,z:Math.log((q.iv/qsum)/pairs.get(q.key))})),n)}

function selfTest(){ensure(horseToken("https://db.sp.netkeiba.com/horse/result/1234567890/")?.token==="1234567890","recognizer positive");ensure(horseToken("https://race.netkeiba.com/race/shutuba_past.html?race_id=1234567890")===null,"race ID not horse ID");ensure(horseToken("https://sports.yahoo.co.jp.evil/keiba/directory/horse/1234567890/")===null,"host allowlist");ensure(horseToken("https://race.sp.netkeiba.com/modal/horse.html?horse_id=1234567890&horse_id=0000000000")===null,"duplicate query");let edges=[];let a=[-2,-1,1,2];for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)edges.push({i,j,z:a[i]+a[j]+3});ensure(Math.abs(project(edges,4)-1)<1e-12,"additive oracle");let e=[{i:0,j:1,z:1},{i:0,j:2,z:-1},{i:0,j:3,z:0},{i:1,j:2,z:0},{i:1,j:3,z:-1},{i:2,j:3,z:1}];ensure(Math.abs(project(e,4))<1e-12,"orthogonal dyad oracle")}

function replay(inputs){const out=[],allTokens=[];for(let idx=0;idx<inputs.length;idx+=4){const [c,h,t,w]=inputs.slice(idx,idx+4);const r=8+idx/4,n=c.horses.length;ensure(c.race===r&&h.race===r&&t.race===r&&w.race===r&&c.date==="2026-10-12"&&h.date===c.date&&c.race_id===`26080405${String(r).padStart(2,"0")}`,"wrong race");ensure(n>=8&&new Set(c.horses.map(x=>x.number)).size===n&&c.horses.every(x=>Number.isInteger(x.number)&&x.number>=1&&x.number<=n),"bad card roster");ensure(t.horses.length===n&&new Set(t.horses.map(x=>x.number)).size===n&&c.horses.every(x=>t.horses.some(y=>y.number===x.number&&normalize(x.name)===normalize(y.name))),"racecard-market name/number mismatch");ensure(Object.keys(h.horses).length===n&&c.horses.every(x=>Object.hasOwn(h.horses,x.number)),"history number set mismatch");const start=Date.parse(c.start_jst);for(const [page,row] of [["tfw",t],["wide",w]]){ensure(row.page_code===page&&row.url.match(new RegExp(`^https://sports\\.yahoo\\.co\\.jp/keiba/race/odds/${page}/${c.race_id}(\\?.*)?$`))&&Array.isArray(row.missing)&&row.missing.length===0&&/^[0-9a-f]{64}$/.test(row.html_sha256),"bad source page");const u=Date.parse(row.updated_at_jst),o=Date.parse(row.observed_at_jst);ensure(u<=o&&o<start,"time not prior to start")}let sourceGap=Math.abs(Date.parse(t.updated_at_jst)-Date.parse(w.updated_at_jst))/60000;let receiveGap=Math.abs(Date.parse(t.observed_at_jst)-Date.parse(w.observed_at_jst))/1000;ensure(sourceGap<=1&&receiveGap<=1,"source alignment outside cohort");ensure(Date.parse(h.history_checked_at_jst)>start,"history check not after race");let z={race:r,horse_rows:n,wide_pairs:w.quotes.wide.length,source_update_gap_minutes:sourceGap,node_R2_unweighted_in_sample:marketStructure(t,w,n),card_yahoo_candidate_rows:0,history_any_candidate_rows:0,card_and_history_consistent_candidate_rows:0,unambiguous_combined_candidate_rows:0,multiple_provider_same_token_rows:0,conflicting_candidate_rows:0,no_candidate_rows:0,history_rows_with_prior_runs:0,strictly_pre_race_run_rows:0,career_starts_note_rows:0};for(const x of c.horses){let y=h.horses[x.number];ensure(Number.isInteger(y.career_starts)&&y.career_starts>=0&&Array.isArray(y.recent_runs),"bad history count");let ca=(x.evidence_urls||[]).map(horseToken).filter(Boolean);let top=horseToken(y.history_source_url);let hi=[top,...y.recent_runs.map(e=>horseToken(e.source_url))].filter(Boolean);let all=[...ca,...hi];let ids=a=>new Set(a.map(v=>v.token));let cu=ids(ca),hu=ids(hi),au=ids(all);if(ca.some(v=>v.provider==="yahoo"))z.card_yahoo_candidate_rows++;if(hu.size)z.history_any_candidate_rows++;if(cu.size&&hu.size&&au.size===1)z.card_and_history_consistent_candidate_rows++;if(au.size===1){z.unambiguous_combined_candidate_rows++;allTokens.push([...au][0]);if(new Set(all.map(v=>v.provider)).size>=2)z.multiple_provider_same_token_rows++;}else if(!au.size)z.no_candidate_rows++;else z.conflicting_candidate_rows++;if(y.career_starts_note)z.career_starts_note_rows++;let ds=y.recent_runs.map(e=>e.date);ensure(ds.every(d=>typeof d==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&d<c.date),"history contains target or later record");z.strictly_pre_race_run_rows+=ds.length;if(ds.length)z.history_rows_with_prior_runs++;ensure((ds.length?[...ds].sort().at(-1):null)===y.source_latest_run_date,"latest date mismatch")}ensure(z.unambiguous_combined_candidate_rows+z.no_candidate_rows+z.conflicting_candidate_rows===n,"candidate partition");out.push(z)}ensure(out.length===5&&new Set(allTokens).size===62&&allTokens.length===62,"cohort / candidate uniqueness");return out}
const PINNED={
  "data/2026-10-12/kyoto_08.json": "40b8626ece484ef6631d4bd97aaf89f26eedec09",
  "data/2026-10-12/v3/history_08.json": "ae4cdc33c40d0387a11940046b37546a765473d3",
  "data/2026-10-12/remaining-snapshots/r8_tfw.json": "65fa640d6a07b7d94eb6e2904f6cc73f07a96448",
  "data/2026-10-12/remaining-snapshots/r8_wide.json": "10bb0d0bcab6035eceaa4edda8c31999d83dae05",
  "data/2026-10-12/kyoto_09.json": "71f6fd82a3c8f44d99ce66354ae077e998b6a238",
  "data/2026-10-12/v3/history_09.json": "c1b923254a7f1063d3322c29fe486e43faf0e4b1",
  "data/2026-10-12/remaining-snapshots/r9_tfw.json": "be94d8b01a2b67287958598842cc724029f45e89",
  "data/2026-10-12/remaining-snapshots/r9_wide.json": "9f49f4379537100038111be3b09b671e42e99e44",
  "data/2026-10-12/kyoto_10.json": "4b8c098eedb478ebd6a9e3e874aa6b692adcfe9a",
  "data/2026-10-12/v3/history_10.json": "a2fd99cb2f5990393708c64b9fe82b2be9b4232d",
  "data/2026-10-12/remaining-snapshots/r10_tfw.json": "cdf8f36a073f68d351417d0046f5ab5c1ccc2be3",
  "data/2026-10-12/remaining-snapshots/r10_wide.json": "2f169fb146260a26a7d6a5d9a73dd4838c7b82fc",
  "data/2026-10-12/kyoto_11.json": "72180071976ffb9efe81cf6b4a6dfdb2aa458bd0",
  "data/2026-10-12/v3/history_11.json": "7119c1a219731f6ce033794bd042daeb0c0854bf",
  "data/2026-10-12/remaining-snapshots/r11_tfw.json": "751734355c67149b39cd1ebaf9682aac24f352e5",
  "data/2026-10-12/remaining-snapshots/r11_wide.json": "c88b4420c1c3d2a3ea5b75e485f46a4eff129203",
  "data/2026-10-12/kyoto_12.json": "3b9194da50df0ead111d179dac609e3c61d3a1c2",
  "data/2026-10-12/v3/history_12.json": "845b2a8508c640e5b14d4cabbde5a7a2f2bb9861",
  "data/2026-10-12/remaining-snapshots/r12_tfw.json": "6da13808c7b2a9c716a74b1c41d2c08296318c09",
  "data/2026-10-12/remaining-snapshots/r12_wide.json": "151369b0f392bd10e18530ebbcfea4e701fc4919"
};
const EXPECTED=[
  {
    "race": 8,
    "horse_rows": 11,
    "wide_pairs": 55,
    "source_update_gap_minutes": 0,
    "node_R2_unweighted_in_sample": 0.5528691078802781,
    "card_yahoo_candidate_rows": 8,
    "history_any_candidate_rows": 9,
    "card_and_history_consistent_candidate_rows": 7,
    "unambiguous_combined_candidate_rows": 10,
    "multiple_provider_same_token_rows": 8,
    "conflicting_candidate_rows": 0,
    "no_candidate_rows": 1,
    "history_rows_with_prior_runs": 10,
    "strictly_pre_race_run_rows": 30,
    "career_starts_note_rows": 2
  },
  {
    "race": 9,
    "horse_rows": 12,
    "wide_pairs": 66,
    "source_update_gap_minutes": 1,
    "node_R2_unweighted_in_sample": 0.6648820444365728,
    "card_yahoo_candidate_rows": 7,
    "history_any_candidate_rows": 12,
    "card_and_history_consistent_candidate_rows": 7,
    "unambiguous_combined_candidate_rows": 11,
    "multiple_provider_same_token_rows": 5,
    "conflicting_candidate_rows": 1,
    "no_candidate_rows": 0,
    "history_rows_with_prior_runs": 12,
    "strictly_pre_race_run_rows": 36,
    "career_starts_note_rows": 1
  },
  {
    "race": 10,
    "horse_rows": 10,
    "wide_pairs": 45,
    "source_update_gap_minutes": 0,
    "node_R2_unweighted_in_sample": 0.7606341868965709,
    "card_yahoo_candidate_rows": 6,
    "history_any_candidate_rows": 9,
    "card_and_history_consistent_candidate_rows": 6,
    "unambiguous_combined_candidate_rows": 9,
    "multiple_provider_same_token_rows": 6,
    "conflicting_candidate_rows": 0,
    "no_candidate_rows": 1,
    "history_rows_with_prior_runs": 10,
    "strictly_pre_race_run_rows": 30,
    "career_starts_note_rows": 1
  },
  {
    "race": 11,
    "horse_rows": 18,
    "wide_pairs": 153,
    "source_update_gap_minutes": 1,
    "node_R2_unweighted_in_sample": 0.6483315740723741,
    "card_yahoo_candidate_rows": 8,
    "history_any_candidate_rows": 18,
    "card_and_history_consistent_candidate_rows": 8,
    "unambiguous_combined_candidate_rows": 18,
    "multiple_provider_same_token_rows": 8,
    "conflicting_candidate_rows": 0,
    "no_candidate_rows": 0,
    "history_rows_with_prior_runs": 18,
    "strictly_pre_race_run_rows": 54,
    "career_starts_note_rows": 0
  },
  {
    "race": 12,
    "horse_rows": 16,
    "wide_pairs": 120,
    "source_update_gap_minutes": 0,
    "node_R2_unweighted_in_sample": 0.5464750541609737,
    "card_yahoo_candidate_rows": 1,
    "history_any_candidate_rows": 14,
    "card_and_history_consistent_candidate_rows": 1,
    "unambiguous_combined_candidate_rows": 14,
    "multiple_provider_same_token_rows": 1,
    "conflicting_candidate_rows": 0,
    "no_candidate_rows": 2,
    "history_rows_with_prior_runs": 16,
    "strictly_pre_race_run_rows": 48,
    "career_starts_note_rows": 2
  }
];
selfTest();
const inputs=Object.entries(PINNED).map(([path,sha])=>{
 const bytes=fs.readFileSync(path);
 const actual=crypto.createHash('sha1').update('blob '+bytes.length+'\0').update(bytes).digest('hex');
 ensure(actual===sha,'source git blob differs: '+path);
 return JSON.parse(bytes);
});
const actual=replay(inputs);
for(let i=0;i<actual.length;i++)for(const [key,value] of Object.entries(EXPECTED[i]))
 ensure(Math.abs(actual[i][key]-value)<1e-10,'replay differs: '+i+' '+key);
process.stdout.write(JSON.stringify(actual,null,2)+'\n');
