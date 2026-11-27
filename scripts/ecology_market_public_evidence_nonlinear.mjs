// Synthetic collective evaluation, research only.
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {dirname} from 'node:path';
const cfg={
  "seed": 20261127,
  "reps": 128,
  "n": 8,
  "b": 2,
  "batches": 60,
  "batch": 12,
  "alpha": [
    0.8,
    1.5,
    4
  ],
  "tau": [
    0,
    2
  ],
  "delta": [
    1,
    4
  ],
  "checkpoints": [
    10,
    20,
    40,
    50,
    60
  ],
  "fields": {
    "equal": [
      0.35,
      0.35,
      0.35,
      0.35,
      0.35,
      0.35,
      0.35,
      0.35
    ],
    "pair_advantaged": [
      0.35,
      0.35,
      -0.2,
      -0.2,
      -0.2,
      -0.2,
      -0.2,
      -0.2
    ],
    "pair_disadvantaged": [
      0.35,
      0.35,
      0.9,
      0.9,
      0.9,
      0.9,
      0.9,
      0.9
    ],
    "heterogeneous": [
      0.35,
      0.35,
      -0.6,
      -0.35,
      -0.1,
      0.15,
      0.5,
      0.8
    ]
  },
  "scenarios": {
    "none": {
      "start": 0,
      "end": 0,
      "h": 0,
      "c": 0
    },
    "early_pulse": {
      "start": 10,
      "end": 20,
      "h": 0.3,
      "c": 0
    },
    "late_pulse": {
      "start": 40,
      "end": 50,
      "h": 0.3,
      "c": 0
    },
    "early_persistent": {
      "start": 10,
      "end": 60,
      "h": 0.3,
      "c": 0
    },
    "late_persistent": {
      "start": 40,
      "end": 60,
      "h": 0.3,
      "c": 0
    },
    "early_group": {
      "start": 10,
      "end": 20,
      "h": 0,
      "c": 0.3
    },
    "late_group": {
      "start": 40,
      "end": 50,
      "h": 0,
      "c": 0.3
    }
  }
};
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return(((t^(t>>>14))>>>0)+.5)/4294967296;};}

function shocks(c,r){const next=rng((c.seed+Math.imul(r+1,0x9E3779B9))>>>0),n=c.batches*c.batch*c.n,z=new Float64Array(n),g=new Float64Array(n);for(let i=0;i<n;i+=2){const u=next(),v=next(),m=Math.sqrt(-2*Math.log(u));z[i]=m*Math.cos(2*Math.PI*v);if(i+1<n)z[i+1]=m*Math.sin(2*Math.PI*v);}for(let i=0;i<n;i++)g[i]=-Math.log(-Math.log(next()));return {z,g};}

function near(a,b,tol=1e-10){if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("HOLD_NUMERIC "+a+" "+b);}

function stat(a){const m=a.reduce((v,x)=>v+x,0)/a.length,sd=Math.sqrt(a.reduce((v,x)=>v+(x-m)**2,0)/(a.length-1));return {mean:m,mc95:[m-1.96*sd/Math.sqrt(a.length),m+1.96*sd/Math.sqrt(a.length)],sd};}

function initial(d){return [10+d,10-d,10,10,10,10,10,10];}

function state(x,T){return {m:(x[0]+x[1])/T,r:(x[0]-x[1])/(x[0]+x[1]),d:(x[0]-x[1])/T};}

function measure(a,b,T){const x=state(a,T),y=state(b,T),M=(x.m+y.m)/2,R=(x.r-y.r)/2,D=(x.d-y.d)/2,cross=(x.r+y.r)/2*(x.m-y.m)/2;near(D,M*R+cross);return {D,R,M,cross,reverse_r:y.r,reverse_d:y.d,reverse_correct:y.r>1e-12?1:y.r< -1e-12?0:.5,reverse_pair_mass:y.m,reverse_A_share:b[0]/T};}

function stepcheck(x,inc,T,B){const m=(x[0]+x[1])/T,r=(x[0]-x[1])/(x[0]+x[1]),P=(inc[0]+inc[1])/B,H=(inc[0]-inc[1])/B,mm=(T*m+B*P)/(T+B),rr=(T*m*r+B*H)/(T*m+B*P),n=x.map((v,i)=>v+inc[i]);near(n.reduce((s,v)=>s+v,0),T+B,1e-8);const z=state(n,T+B);near(mm,z.m);near(rr,z.r);return n;}

function sim(c,sh,theta,alpha,tau,d,news,det=false,swap=true){if(det&&tau!==0)throw Error("HOLD_DETERMINISTIC_NOISE");let a=initial(d),b=a.slice(),out=[];if(swap)[b[0],b[1]]=[b[1],b[0]];const mu=theta.map(x=>c.b*x);let fd=0,fa=0,fp=0,fn=0;for(let t=0;t<c.batches;t++){const active=t>=news.start&&t<news.end,u=mu.slice();if(active){u[0]+=news.c+news.h;u[1]+=news.c-news.h;}const sa=a.map(x=>alpha*Math.log(x)),sb=b.map(x=>alpha*Math.log(x));let ia=Array(c.n).fill(0),ib=ia.slice();if(det){const probs=x=>{const w=x.map((v,i)=>v+u[i]),m=Math.max(...w),e=w.map(v=>Math.exp(v-m)),s=e.reduce((p,q)=>p+q,0);return e.map(v=>c.batch*v/s);};ia=probs(sa);ib=probs(sb);}else{for(let j=0;j<c.batch;j++){let iA=-1,iB=-1,mA=-Infinity,mB=-Infinity,off=(t*c.batch+j)*c.n;for(let i=0;i<c.n;i++){const v=u[i]+tau*sh.z[off+i]+sh.g[off+i],vA=v+sa[i],vB=v+sb[i];if(vA>mA){mA=vA;iA=i;}if(vB>mB){mB=vB;iB=i;}}ia[iA]++;ib[iB]++;}}const T=80+t*c.batch;a=stepcheck(a,ia,T,c.batch);b=stepcheck(b,ib,T,c.batch);if(a.some(v=>v<=0)||b.some(v=>v<=0))throw Error("HOLD_POSITIVE");fd+=ib[0]-ib[1];fa+=ib[0];fp+=ib[0]+ib[1];fn+=c.batch;if(c.checkpoints.includes(t+1)){out.push({...measure(a,b,T+c.batch),flow_reverse_difference:fd/fn,flow_reverse_A:fa/fn,flow_reverse_pair:fp/fn});fd=0;fa=0;fp=0;fn=0;}}return out;}

function stats(x){return Object.fromEntries(Object.keys(x[0]).map(k=>[k,stat(x.map(v=>v[k]))]));}

function diff(a,b,keys){return Object.fromEntries(keys.map(k=>[k,stat(a.map((v,i)=>v[k]-b[i][k]))]));}

function equalState(a,b){for(const k of Object.keys(a))near(a[k],b[k]);}

function checks(c){const sh=shocks(c,0),theta=c.fields.heterogeneous;for(const t of c.tau)for(const d of c.delta){const zero=sim(c,sh,theta,0,t,d,c.scenarios.none),same=sim(c,sh,theta,1.5,t,d,c.scenarios.early_pulse,false,false);for(let i=0;i<c.checkpoints.length;i++){near(zero[i].D,2*d/(80+c.checkpoints[i]*c.batch));near(same[i].D,0);near(same[i].R,0);}const a=sim(c,sh,theta,1.5,t,d,c.scenarios.none);for(const n of Object.keys(c.scenarios).filter(x=>x!=="none")){const b=sim(c,sh,theta,1.5,t,d,c.scenarios[n]);for(let i=0;i<c.checkpoints.length;i++)if(c.checkpoints[i]<=c.scenarios[n].start)equalState(a[i],b[i]);}equalState(sim(c,sh,theta,1.5,t,d,c.scenarios.early_pulse)[1],sim(c,sh,theta,1.5,t,d,c.scenarios.early_persistent)[1]);}const a=sim(c,sh,theta,1.5,2,1,c.scenarios.early_pulse),b=sim(c,shocks(c,0),theta,1.5,2,1,c.scenarios.early_pulse);if(JSON.stringify(a)!==JSON.stringify(b))throw Error("HOLD_REPRO");for(const x of sim(c,null,c.fields.equal,1,0,1,c.scenarios.none,true)){near(x.D,.025);near(x.R,.1);near(x.M,.25);}return {mass:true,finite_state_equations:true,exact_two_world_decomposition:true,no_feedback_mechanical:true,identical_world:true,pre_arrival_parity:true,equal_exposure_prefix:true,deterministic_reproduction:true};}

function run(c){const qa=checks(c),cells=new Map(),names=Object.keys(c.scenarios),rows=[],contrasts=[];for(const f of Object.keys(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta)for(const n of names)cells.set([f,a,t,d,n].join("|"),[]);for(let r=0;r<c.reps;r++){const sh=shocks(c,r);for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta)for(const n of names)cells.get([f,a,t,d,n].join("|")).push(sim(c,sh,theta,a,t,d,c.scenarios[n]));}const keys=["D","R","M","reverse_r","reverse_correct","reverse_pair_mass","reverse_d","flow_reverse_difference","flow_reverse_pair"];for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta){const get=n=>cells.get([f,a,t,d,n].join("|")),none=get("none"),k=c.checkpoints.length-1;for(const n of names){const x=get(n),det=t===0?sim(c,null,theta,a,t,d,c.scenarios[n],true):null,checkpoints=c.checkpoints.map((b,i)=>({batch:b,...stats(x.map(v=>v[i]))}));rows.push({field:f,alpha:a,tau:t,delta:d,scenario:n,checkpoints,deterministic_tau0:det});if(n!=="none"){const post=c.checkpoints.indexOf(c.scenarios[n].start+10);contrasts.push({field:f,alpha:a,tau:t,delta:d,scenario:n,post_batch:c.checkpoints[post],after_ten_batches:diff(x.map(v=>v[post]),none.map(v=>v[post]),keys),terminal:diff(x.map(v=>v[k]),none.map(v=>v[k]),keys)});}}}const timing=[],comparative=[];for(const f of Object.keys(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta){const get=n=>cells.get([f,a,t,d,n].join("|")),none=get("none"),end=c.checkpoints.length-1,ei=1,li=3;for(const kind of ["pulse","group","persistent"]){const e=get("early_"+kind),l=get("late_"+kind),after={};for(const m of keys)after[m]=stat(e.map((v,i)=>(v[ei][m]-none[i][ei][m])-(l[i][li][m]-none[i][li][m])));timing.push({field:f,alpha:a,tau:t,delta:d,kind,early_minus_late_effect_after_equal_ten_batches:after,early_minus_late_terminal:diff(e.map(v=>v[end]),l.map(v=>v[end]),keys)});}for(const when of ["early","late"]){const g=get(when+"_group"),p=get(when+"_pulse"),i=when==="early"?ei:li;comparative.push({field:f,alpha:a,tau:t,delta:d,when,group_minus_differential_after_ten:diff(g.map(v=>v[i]),p.map(v=>v[i]),keys),group_minus_differential_terminal:diff(g.map(v=>v[end]),p.map(v=>v[end]),keys)});}}return {status:"SYNTHETIC_PUBLIC_EVIDENCE_NONLINEAR",config:c,qa,rows,contrasts,timing,comparative,limits:["Artificial support counts; no actual odds, votes, participants or race-outcome model.","Imposed differential utility gap .6 and symmetric +.3 attention signal, not estimated. Latent advantage disclosure is a synthetic interpretation.","Equal exposure contrasts same-time no-news baseline, but cumulative states and stock sizes differ. Persistent terminal exposures differ.","Deterministic tau=0 conditional mean recursion is not stochastic expectation.","MC95 conditional on chosen scenarios, not empirical uncertainty or multiplicity-adjusted inference. Net alpha not separately identified."]};}

function compact(r){const s=x=>[x.mean,...x.mc95];return {qa:r.qa,n:r.rows.length,selected:r.rows.filter(x=>x.field==="heterogeneous"&&x.tau===0&&x.delta===4).map(x=>({a:x.alpha,n:x.scenario,points:x.checkpoints.map(p=>({batch:p.batch,D:p.D.mean,R:p.R.mean,M:p.M.mean,r:p.reverse_r.mean,recovery:p.reverse_correct.mean,flow:p.flow_reverse_difference.mean}))})),timing:r.timing.filter(x=>x.delta===4&&x.tau===0&&x.alpha===1.5).map(x=>({f:x.field,kind:x.kind,immediate:s(x.early_minus_late_effect_after_equal_ten_batches.reverse_r),flow:s(x.early_minus_late_effect_after_equal_ten_batches.flow_reverse_difference),terminal:s(x.early_minus_late_terminal.reverse_r)})),contrasts:r.contrasts.filter(x=>x.field==="heterogeneous"&&x.delta===4&&x.tau===0&&x.alpha===1.5).map(x=>({n:x.scenario,immediate:s(x.after_ten_batches.reverse_r),terminal:s(x.terminal.reverse_r),D:s(x.terminal.D),M:s(x.terminal.M),R:s(x.terminal.R)})),all_terminal:r.rows.map(x=>{const p=x.checkpoints.at(-1);return [x.field,x.alpha,x.tau,x.delta,x.scenario,p.D.mean,p.R.mean,p.M.mean,p.reverse_r.mean,p.reverse_correct.mean];}),direction_counts:r.contrasts.reduce((o,x)=>{const k=x.scenario;if(!o[k])o[k]={D_pos:0,D_neg:0,R_pos:0,R_neg:0,rank_pos:0,rank_neg:0,within_pos:0,within_neg:0};for(const [m,key] of [["D","D"],["R","R"],["reverse_correct","rank"],["reverse_r","within"]]){if(x.terminal[m].mc95[0]>0)o[k][key+"_pos"]++;if(x.terminal[m].mc95[1]<0)o[k][key+"_neg"]++;}return o;},{})};}
const result=run(cfg);
const prior=JSON.parse(readFileSync(process.argv[3],"utf8"));let parentN=0;for(const row of result.rows.filter(x=>x.scenario==="none")){const p=prior.rows.find(x=>x.field===row.field&&x.alpha===row.alpha&&x.tau===row.tau&&x.delta===row.delta);if(!p)throw Error("HOLD_PARENT_CELL");for(const t of [10,60]){const a=row.checkpoints.find(x=>x.batch===t),b=p.checkpoints.find(x=>x.batch===t);for(const [k,l,scale] of [["D","D_gain",2*row.delta/80],["R","R_gain",2*row.delta/20],["M","pair_mass",1]]){near(a[k].mean/scale,b[l].mean);near(a[k].sd/scale,b[l].sd);for(let i=0;i<2;i++)near(a[k].mc95[i]/scale,b[l].mc95[i]);parentN+=4;}}}if(parentN!==48*2*3*4)throw Error("HOLD_PARENT_COUNT");
const out=process.argv[2]||"tmp/market-public-evidence-nonlinear.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");const original=JSON.parse(readFileSync(process.argv[4],"utf8")),newSummary=compact(result);let max=0,n=0;function same(a,b){if(typeof a==="number"){near(a,b,1e-9*Math.max(1,Math.abs(a)));max=Math.max(max,Math.abs(a-b));n++;}else if(a!==null&&typeof a==="object"){if(!b||JSON.stringify(Object.keys(a))!==JSON.stringify(Object.keys(b)))throw Error("HOLD_KEYS");for(const k of Object.keys(a))same(a[k],b[k]);}else if(a!==b)throw Error("HOLD_VALUE");}same(original,newSummary);console.log(JSON.stringify({status:"SYNTHETIC_PUBLIC_EVIDENCE_REPLAY",parent_numeric_values:parentN,summary_numeric_values:n,max_abs_diff:max,rows:result.rows.length,qa:result.qa}));
