// Research-only archive audit.
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {dirname} from 'node:path';
const cfg={
  "sourceRevision": "dfd0450769abf17bf38bdc17872e3e91b2a286fa",
  "cardPaths": [
    "data/2026-10-12/kyoto_06.json",
    "data/2026-10-12/kyoto_07.json",
    "data/2026-10-12/kyoto_08.json",
    "data/2026-10-12/kyoto_09.json",
    "data/2026-10-12/kyoto_10.json",
    "data/2026-10-12/kyoto_11.json",
    "data/2026-10-12/kyoto_12.json"
  ],
  "tfwPaths": [
    "data/2026-10-12/remaining-snapshots/r8_tfw.json",
    "data/2026-10-12/remaining-snapshots/r9_tfw.json",
    "data/2026-10-12/remaining-snapshots/r10_tfw.json",
    "data/2026-10-12/remaining-snapshots/r11_tfw.json",
    "data/2026-10-12/remaining-snapshots/r12_tfw.json"
  ],
  "bundlePaths": [
    "data/2026-10-12/r7_markets.json",
    "data/2026-10-12/r8_markets.json",
    "data/2026-10-12/r8_markets_latest.json"
  ],
  "extraPaths": [
    "reports/2026-10-12/r8-latest-fetch.json",
    "reports/2026-10-12/monitor-1339-r9-r10.json",
    "reports/2026-10-12/monitor-1339-r11-r12.json",
    "reports/2026-10-12/remaining-final-price-check.json",
    "data/2026-10-18/ticket-odds-snapshot.json"
  ],
  "blobs": {
    "data/2026-10-12/kyoto_06.json": "4dd1fd493e2db967ab74e5ac301f9428dbc17250",
    "data/2026-10-12/kyoto_07.json": "253ba03fcdadc7517ac63eb2587561d12b81cf33",
    "data/2026-10-12/kyoto_08.json": "40b8626ece484ef6631d4bd97aaf89f26eedec09",
    "data/2026-10-12/kyoto_09.json": "71f6fd82a3c8f44d99ce66354ae077e998b6a238",
    "data/2026-10-12/kyoto_10.json": "4b8c098eedb478ebd6a9e3e874aa6b692adcfe9a",
    "data/2026-10-12/kyoto_11.json": "72180071976ffb9efe81cf6b4a6dfdb2aa458bd0",
    "data/2026-10-12/kyoto_12.json": "3b9194da50df0ead111d179dac609e3c61d3a1c2",
    "data/2026-10-12/r7_markets.json": "d61125bc680800221f2064ac84b4b1f332738416",
    "data/2026-10-12/r8_markets.json": "a01268d94b341e8d9e8b5f600e75579c7d22eb4a",
    "data/2026-10-12/r8_markets_latest.json": "5e84f3c445249564b2cd7ed358591ed02a8b2d88",
    "data/2026-10-12/remaining-snapshots/r10_tfw.json": "cdf8f36a073f68d351417d0046f5ab5c1ccc2be3",
    "data/2026-10-12/remaining-snapshots/r11_tfw.json": "751734355c67149b39cd1ebaf9682aac24f352e5",
    "data/2026-10-12/remaining-snapshots/r12_tfw.json": "6da13808c7b2a9c716a74b1c41d2c08296318c09",
    "data/2026-10-12/remaining-snapshots/r8_tfw.json": "65fa640d6a07b7d94eb6e2904f6cc73f07a96448",
    "data/2026-10-12/remaining-snapshots/r9_tfw.json": "be94d8b01a2b67287958598842cc724029f45e89",
    "data/2026-10-18/ticket-odds-snapshot.json": "8a7d37f02a40e7c6f93d6ee428089cd5c84e59df",
    "reports/2026-10-12/monitor-1339-r11-r12.json": "48ae8762a0036339ce31266252cf9ac3d546ff41",
    "reports/2026-10-12/monitor-1339-r9-r10.json": "fedddc4ef510983059e425adbf10eb8b4a1e0d05",
    "reports/2026-10-12/r8-latest-fetch.json": "7e4a5b7bda10a573caa68c71ea41c3b063c1d6ef",
    "reports/2026-10-12/remaining-final-price-check.json": "7acffe0e4bea7961ebd3ce3de1b24905d15f364d"
  },
  "displaySensitivity": [
    [
      "center",
      0,
      0
    ],
    [
      "truncation",
      0,
      0.1
    ],
    [
      "nearest",
      -0.05,
      0.05
    ]
  ]
};
function near(a,b,tol=1e-10){if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("IDENTITY "+a+" "+b);}

function check(x,msg){if(!x)throw Error(msg);}

function numTime(x){const d=Date.parse(x);check(Number.isFinite(d)&&typeof x==="string"&&/T/.test(x),"CLOCK");return d;}

function norm(x){return String(x).normalize("NFKC").replace(/\s/g,"");}

function quoteMap(xs){const m=new Map();for(const [i,o] of xs){check(Number.isInteger(i)&&i>0&&!m.has(i)&&Number.isFinite(o)&&o>=1,"BAD_QUOTE");m.set(i,o);}return m;}

function quotePairs(xs){return xs.map(x=>{check(Array.isArray(x.selection)&&x.selection.length===1&&x.odds_low===x.odds_high,"WIN_SCHEMA");return [x.selection[0],x.odds_low];});}

function urlCheck(s,rid){const match=String(s).match(/^https:\/\/sports\.yahoo\.co\.jp\/keiba\/race\/odds\/tfw\/(\d{10})(?:\?.*)?$/);check(match&&match[1]===rid,"WRONG_SOURCE");}

function record(c,path,kind,update,receipt,url,quotes,names,hash){urlCheck(url,c.race_id);const u=numTime(update),v=numTime(receipt),start=numTime(c.start_jst);check(u<=v&&v<start,"PRESTART_CLOCK");const m=quoteMap(quotes);const ids=c.horses.map(h=>h.number).sort((a,b)=>a-b);check(m.size===ids.length&&ids.every(i=>m.has(i)),"ROSTER");if(names){const a=new Map(names.map(h=>[h.number,norm(h.name)]));check(a.size===ids.length&&c.horses.every(h=>a.get(h.number)===norm(h.name)),"NAME");}return {race:c.race,path,kind,update,receipt,u,v,odds:ids.map(i=>m.get(i)),hash:hash&&/^[a-f0-9]{64}$/.test(hash)?"recorded_not_raw_verified":"absent",name_match:!!names};}

function fromInputs(cfg,input){
 const cards={},records=[],exclusions=[];
 for(const path of cfg.cardPaths){const c=input[path];check(c.date==="2026-10-12"&&c.race_id==="26080405"+String(c.race).padStart(2,"0"),"CARD_ID");cards[c.race]=c;const a=c.sources.filter(v=>v.kind==="win_odds");check(a.length===1&&a[0].updated_at_jst===c.odds_updated_at_jst,"CARD_SOURCE_TIME");records.push(record(c,path,"card_record",c.odds_updated_at_jst,c.odds_observed_at_jst,a[0].url,c.horses.map(h=>[h.number,h.win_odds]),c.horses,null));}
 for(const path of cfg.tfwPaths){const x=input[path],c=cards[x.race];check(x.page_code==="tfw"&&Array.isArray(x.missing)&&!x.missing.length,"TFW_INCOMPLETE");records.push(record(c,path,"full_tfw",x.updated_at_jst,x.observed_at_jst,x.url,quotePairs(x.quotes.win),x.horses,x.html_sha256));}
 for(const path of cfg.bundlePaths){const x=input[path],c=cards[x.race],v=x.markets.win;check(x.race_id===c.race_id&&x.start_jst===c.start_jst&&(x.horse_count??x.expected_full_market_sizes?.win)===c.horses.length&&x.expected_full_market_sizes?.win===c.horses.length,"BUNDLE_ROSTER:"+path);records.push(record(c,path,"market_bundle",v.updated_at_jst,v.observed_at_utc||x.checked_at_utc,v.source_url,quotePairs(v.quotes),null,v.html_sha256));}
 const rawPath=cfg.extraPaths[0],a=input[rawPath].find(x=>x.url.includes("/odds/tfw/")),c=cards[8];
 try{const m=a.times[0].match(/^(\d{4})\/(\d\d)\/(\d\d) (\d\d):(\d\d) 更新$/);check(m,"RAW_TIME");const update=`${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:00+09:00`;check(norm(a.rows[0])===norm("人気 枠番 馬番 馬名 単勝 複勝"),"RAW_HEADER");const qs=[],names=[];for(const line of a.rows.slice(1,c.horses.length+1)){const m=line.normalize("NFKC").match(/^\s*\d+\s+\d+\s+(\d+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*[-–−]\s*(\d+(?:\.\d+)?)\s*$/);check(m,"RAW_ROW");qs.push([Number(m[1]),Number(m[3])]);names.push({number:Number(m[1]),name:m[2]});}records.push(record(c,rawPath,"text_extract_sensitivity",update,a.checked_at_utc,a.url,qs,names,null));}catch(e){exclusions.push({path:rawPath,reason:"RAW_TEXT_PARSE_HOLD:"+e.message});}
 for(const path of cfg.extraPaths.slice(1,3))for(const r of input[path].races){const n=r.win_odds?.quotes?.length??r.horses?.length;check(n<cards[r.race].horses.length,"MONITOR_UNEXPECTED_COMPLETE");exclusions.push({path,race:r.race,reason:"partial_selected_horses",rows:n,expected:cards[r.race].horses.length});}
 for(const r of input[cfg.extraPaths[3]].pages.filter(x=>x.page_code==="tfw")){check(r.quotes.length<cards[r.race].horses.length,"FINAL_UNEXPECTED_COMPLETE");exclusions.push({path:cfg.extraPaths[3],race:r.race,reason:"partial_selected_quotes",rows:r.quotes.length,expected:cards[r.race].horses.length});}
 for(const r of input[cfg.extraPaths[4]].races){check(r.win_place_upstream_updated_at===null,"OCT18_NEW_CLOCK");exclusions.push({path:cfg.extraPaths[4],reason:"upstream_update_time_missing",race_id:r.race_id,rows:r.horses.length});}
 return {cards,records,exclusions};
}

function bounds(o,lo,hi){return [1/(o+hi),1/Math.max(1,o+lo)];}

function pairBounds(odds,i,j,lo,hi){
 const w=odds.map(o=>bounds(o,lo,hi));const [a,A]=w[i],[b,B]=w[j],small=w.reduce((s,x,k)=>s+(k!==i&&k!==j?x[0]:0),0),large=w.reduce((s,x,k)=>s+(k!==i&&k!==j?x[1]:0),0);
 const ml=(a+b)/(a+b+large),mh=(A+B)/(A+B+small),rlo=(a-B)/(a+B),rhi=(A-b)/(A+b),dlo=(a-B)/(a+B+(a>=B?large:small)),dhi=(A-b)/(A+b+(A>=b?small:large));
 function absInterval(l,h){return [l<=0&&h>=0?0:Math.min(Math.abs(l),Math.abs(h)),Math.max(Math.abs(l),Math.abs(h))];}
 return {M:[ml,mh],r:absInterval(rlo,rhi),D:absInterval(dlo,dhi)};
}

function shares(odds){const w=odds.map(o=>1/o),z=w.reduce((a,b)=>a+b,0);return w.map(x=>x/z);}

function cmp(x,y){return y[0]>x[1]+1e-12?"grow":y[1]<x[0]-1e-12?"shrink":"unresolved";}

function interval(a,b,cfg){
 const p=shares(a.odds),q=shares(b.odds),n=p.length,categories={},identity=[];
 for(const [label,lo,hi] of cfg.displaySensitivity){let ct={pairs:0,both_resolved:0,opposite:0,Dgrow_rshrink:0,Dshrink_rgrow:0,M_grow:0,M_shrink:0};for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){const x=pairBounds(a.odds,i,j,lo,hi),y=pairBounds(b.odds,i,j,lo,hi),d=cmp(x.D,y.D),r=cmp(x.r,y.r),m=cmp(x.M,y.M);ct.pairs++;if(m==="grow")ct.M_grow++;if(m==="shrink")ct.M_shrink++;if(d!=="unresolved"&&r!=="unresolved"){ct.both_resolved++;if(d!==r){ct.opposite++;ct[d==="grow"?"Dgrow_rshrink":"Dshrink_rgrow"]++;}}if(label==="center"){const M0=p[i]+p[j],M1=q[i]+q[j],r0=Math.abs(p[i]-p[j])/M0,r1=Math.abs(q[i]-q[j])/M1,D0=Math.abs(p[i]-p[j]),D1=Math.abs(q[i]-q[j]),mass=.5*(r0+r1)*(M1-M0),within=.5*(M0+M1)*(r1-r0);near(D1-D0,mass+within);identity.push({mass,within,net:D1-D0});}}categories[label]=ct;}
 const avgAbs=k=>identity.reduce((s,x)=>s+Math.abs(x[k]),0)/identity.length,inverseSum=x=>x.odds.reduce((s,o)=>s+1/o,0),pFeas=x=>{const l=x.odds.reduce((s,o)=>s+.8/(o+.1),0),h=.8*inverseSum(x);return {lower:l,upper:h,contains_unit_sum:l<=1+1e-12&&h>=1-1e-12};};
 return {race:a.race,from:a.update,to:b.update,minutes:(b.u-a.u)/60000,n,pair_count:n*(n-1)/2,from_kind:a.kind,to_kind:b.kind,categories,mean_abs_components:{mass:avgAbs("mass"),within:avgAbs("within"),net:avgAbs("net")},TV:.5*p.reduce((s,x,i)=>s+Math.abs(x-q[i]),0),reciprocal_sum:[inverseSum(a),inverseSum(b)],conditional_pool_feasibility:[pFeas(a),pFeas(b)]};
}

function audit(cfg,input){
 const {cards,records,exclusions}=fromInputs(cfg,input),races=[],primary=[],sensitivity=[],allPoints=[];
 for(const c of Object.values(cards)){const rr=records.filter(x=>x.race===c.race).sort((a,b)=>a.v-b.v||a.u-b.u);let last=-Infinity,kept=[];for(const r of rr){const row={race:r.race,path:r.path,kind:r.kind,update:r.update,receipt:r.receipt,n:r.odds.length,html_hash:r.hash,name_match:r.name_match};if(r.u<=last){exclusions.push({...row,reason:"nonincreasing_source_time_in_receipt_order"});continue;}if(r.kind==="text_extract_sensitivity"){allPoints.push({...row,status:"sensitivity_only"});continue;}kept.push(r);last=r.u;allPoints.push({...row,status:"primary"});}
 for(let k=1;k<kept.length;k++)primary.push(interval(kept[k-1],kept[k],cfg));const raw=rr.find(x=>x.kind==="text_extract_sensitivity");if(raw){const left=kept.filter(x=>x.u<raw.u).at(-1),right=kept.find(x=>x.u>raw.u);if(left&&right&&left.v<raw.v&&raw.v<right.v)sensitivity.push(interval(left,raw,cfg),interval(raw,right,cfg));}races.push({race:c.race,roster:c.horses.length,primary_states:kept.length,source_minutes:kept.map(x=>x.update.slice(11,16)),has_raw_text_sensitivity:!!raw});}
 function aggregate(rows){return Object.fromEntries(cfg.displaySensitivity.map(([key])=>{let z={pairs:0,both_resolved:0,opposite:0,Dgrow_rshrink:0,Dshrink_rgrow:0,M_grow:0,M_shrink:0};for(const r of rows)for(const k of Object.keys(z))z[k]+=r.categories[key][k];return [key,z];}));}
 return {status:"OBSERVED_ARCHIVED_WIN_PRICE_PROXY_TRAJECTORY",qa:{clock_gates:true,complete_boards:true,roster_gate:true,exact_pair_change_accounting:true,stale_excluded:true},source_revision:cfg.sourceRevision,pinned_blobs:cfg.blobs,races,points:allPoints,exclusions,primary_intervals:primary,raw_text_sensitivity_intervals:sensitivity,aggregate:aggregate(primary),counts:{race_count:races.length,multi_state_races:races.filter(x=>x.primary_states>=2).length,primary_states:races.reduce((s,x)=>s+x.primary_states,0),primary_intervals:primary.length,unique_date_count:1,actual_stock_observed:0,externally_timed_news_observed:0},limits:["Retrospective saved quote records, not actual vote shares or independent receipt/source verification; original HTML hashes when present not rehashed.","Card provenance weaker than raw archived full page; bundle joins race-local numbers only; raw text extract sensitivity excluded from primary.","Normalized reciprocal quote proxy, not probability or money flow. Display perturbation intervals are hypothetical, not certified true pool-share bounds.","Pair rows and repeated race intervals dependent; one date, no causal or population inference, no external information event or cumulative stock.","Conditional .8/odds feasibility assumes single winner, ordinary payout factor, floor rounding and no exceptional rules; not true-share estimate.","No outcomes, individual quotes, betting recommendation or prospective scoring."]};
}

function selfTest(){const o=[2,4,6,8],p=shares(o);for(let i=0;i<o.length;i++)for(let j=i+1;j<o.length;j++){const b=pairBounds(o,i,j,0,0),m=p[i]+p[j],d=Math.abs(p[i]-p[j]);near(b.M[0],m);near(b.D[0],d);near(b.r[0],d/m);const z=pairBounds(o,i,j,-.05,.05);for(let mask=0;mask<16;mask++){const v=shares(o.map((x,k)=>x+((mask>>k)&1?.05:-.05))),M=v[i]+v[j],D=Math.abs(v[i]-v[j]),r=D/M;for(const [k,a] of [["M",M],["D",D],["r",r]])check(a>=z[k][0]-1e-12&&a<=z[k][1]+1e-12,"BOUND");}}}
selfTest();const inputs={};for(const [path,sha] of Object.entries(cfg.blobs)){const buf=readFileSync(path),actual=createHash("sha1").update("blob "+buf.length).update(Buffer.from([0])).update(buf).digest("hex");check(actual===sha,"INPUT_BLOB:"+path);inputs[path]=JSON.parse(buf);}
const result=audit(cfg,inputs);const out=process.argv[2]||"tmp/market-observed-win-trajectory.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");console.log(JSON.stringify(result));
