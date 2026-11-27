// Synthetic stock and state counterfactual; research only.
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
  },
  "postSeed": 20261202,
  "postBatches": 10,
  "stock": [
    200,
    560
  ],
  "kinds": {
    "none": {
      "h": 0,
      "c": 0
    },
    "differential": {
      "h": 0.3,
      "c": 0
    },
    "group": {
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


function advance(c,a,b,sh,t,theta,alpha,tau,news,T){
 const u=theta.map(x=>c.b*x);u[0]+=news.c+news.h;u[1]+=news.c-news.h;
 const sa=a.map(x=>alpha*Math.log(x)),sb=b.map(x=>alpha*Math.log(x));
 let ia=Array(c.n).fill(0),ib=ia.slice();
 for(let j=0;j<c.batch;j++){
  let iA=-1,iB=-1,mA=-Infinity,mB=-Infinity,off=(t*c.batch+j)*c.n;
  for(let i=0;i<c.n;i++){
   const v=u[i]+tau*sh.z[off+i]+sh.g[off+i],vA=v+sa[i],vB=v+sb[i];
   if(vA>mA){mA=vA;iA=i;}if(vB>mB){mB=vB;iB=i;}
  }ia[iA]++;ib[iB]++;
 }
 return {a:stepcheck(a,ia,T,c.batch),b:stepcheck(b,ib,T,c.batch),ia,ib};
}
function history(c,sh,theta,alpha,tau,d){
 let a=initial(d),b=a.slice();[b[0],b[1]]=[b[1],b[0]];const out={};
 for(let t=0;t<c.batches;t++){
  const x=advance(c,a,b,sh,t,theta,alpha,tau,c.kinds.none,80+t*c.batch);a=x.a;b=x.b;
  if([10,40,60].includes(t+1))out[t+1]={a:a.slice(),b:b.slice(),T:80+(t+1)*c.batch,metrics:measure(a,b,80+(t+1)*c.batch)};
 }
 return out;
}
function rescale(x,T){
 const a=x.a.map(v=>v*T/x.T),b=x.b.map(v=>v*T/x.T);
 near(a.reduce((p,q)=>p+q,0),T,1e-8);near(b.reduce((p,q)=>p+q,0),T,1e-8);
 for(let i=0;i<a.length;i++){near(a[i]/T,x.a[i]/x.T);near(b[i]/T,x.b[i]/x.T);}
 return {a,b,T};
}
function post(c,x,sh,theta,alpha,tau,news){
 let a=x.a.slice(),b=x.b.slice(),fd=0,fp=0,first=null;
 for(let t=0;t<c.postBatches;t++){
  const q=advance(c,a,b,sh,t,theta,alpha,tau,news,x.T+t*c.batch);
  a=q.a;b=q.b;fd+=q.ib[0]-q.ib[1];fp+=q.ib[0]+q.ib[1];
  if(t===0)first={a:q.ia,b:q.ib};
 }
 return {metrics:{...measure(a,b,x.T+c.postBatches*c.batch),flow_reverse_difference:fd/(c.postBatches*c.batch),flow_reverse_pair:fp/(c.postBatches*c.batch)},first};
}
const METRICS=["reverse_r","reverse_d","reverse_correct","D","R","M","reverse_pair_mass","flow_reverse_difference","flow_reverse_pair"];
const ARMS=["ES","EL","LS","LL"];
function effect(a,b){return Object.fromEntries(METRICS.map(k=>[k,a.metrics[k]-b.metrics[k]]));}
function summarize(a){return Object.fromEntries(Object.keys(a[0]).map(k=>[k,stat(a.map(x=>x[k]))]));}
function decomposition(x){
 const d={};for(const k of METRICS){const es=x.ES[k],el=x.EL[k],ls=x.LS[k],ll=x.LL[k],total=es-ll,state=.5*((es-ls)+(el-ll)),stock=.5*((es-el)+(ls-ll)),interaction=(es-el)-(ls-ll);
  near(total,state+stock);
  d[k]={total,state,stock,interaction,state_small:es-ls,state_large:el-ll,stock_early:es-el,stock_late:ls-ll};
 }return d;
}
function compute(c,prior){
 const rows=[],allHist=[],qa={stock_rescale:true,first_arrival_stock_invariance:true,conservation:true,exact_decomposition:true,original_PR123_terminal_parity:true},keys=Object.keys(c.fields);
 let parentN=0;
 for(const f of keys)for(const alpha of c.alpha)for(const tau of c.tau)for(const delta of c.delta){
  const theta=c.fields[f],hist=[],out={differential:[],group:[]},initialStates={E:[],L:[]};
  for(let r=0;r<c.reps;r++){
   const h=history(c,shocks(c,r),theta,alpha,tau,delta);hist.push(h[60].metrics);
   const postShock=shocks({...c,seed:c.postSeed},r);
   initialStates.E.push(h[10].metrics);initialStates.L.push(h[40].metrics);
   const starts={ES:rescale(h[10],200),EL:rescale(h[10],560),LS:rescale(h[40],200),LL:rescale(h[40],560)};
   const base={};for(const k of ARMS)base[k]=post(c,starts[k],postShock,theta,alpha,tau,c.kinds.none);
   for(const [s,l] of [["ES","EL"],["LS","LL"]])if(JSON.stringify(base[s].first)!==JSON.stringify(base[l].first))throw Error("HOLD_FIRST_ARRIVAL");
   for(const kind of ["differential","group"]){
    const v={};for(const k of ARMS)v[k]=post(c,starts[k],postShock,theta,alpha,tau,c.kinds[kind]);
    for(const [s,l] of [["ES","EL"],["LS","LL"]])if(JSON.stringify(v[s].first)!==JSON.stringify(v[l].first))throw Error("HOLD_FIRST_ARRIVAL_NEWS");
    const e=Object.fromEntries(ARMS.map(k=>[k,effect(v[k],base[k])]));
    out[kind].push({e,dec:decomposition(e)});
   }
  }
  const h=summarize(hist),old=prior.all_terminal.find(x=>x[0]===f&&x[1]===alpha&&x[2]===tau&&x[3]===delta&&x[4]==="none");
  if(!old)throw Error("HOLD_PARENT_CELL");
  for(const [k,i] of [["D",5],["R",6],["M",7],["reverse_r",8],["reverse_correct",9]]){near(h[k].mean,old[i]);parentN++;}
  const before={E:summarize(initialStates.E),L:summarize(initialStates.L)};
  for(const kind of ["differential","group"]){
   const a=out[kind],arms=Object.fromEntries(ARMS.map(k=>[k,summarize(a.map(x=>x.e[k]))]));
   const dec=Object.fromEntries(METRICS.map(k=>[k,summarize(a.map(x=>x.dec[k]))]));
   rows.push({field:f,alpha,tau,delta,kind,before,arms,decomposition:dec});
  }
 }
 if(parentN!==240)throw Error("HOLD_PARENT_COUNT");
 const counts={};for(const kind of ["differential","group"]){counts[kind]={};for(const metric of ["reverse_r","D","R","M","flow_reverse_difference"]){counts[kind][metric]={};for(const component of ["total","stock","state","interaction","state_small","state_large"]){const n={positive:0,negative:0,unresolved:0};for(const row of rows.filter(x=>x.kind===kind)){const q=row.decomposition[metric][component];n[q.mc95[0]>0?"positive":q.mc95[1]<0?"negative":"unresolved"]++;}counts[kind][metric][component]=n;}}}
 return {status:"SYNTHETIC_STOCK_STATE_COUNTERFACTUAL",config:c,qa,parent_numeric_values:parentN,rows,counts,limits:["Artificial support states, not real observations or prices.","Crossed rescaling creates fractional historical count weights; new arrivals are integer, stock is conserved.","Early and late states generated by same synthetic untreated history; fresh common post shocks independent of history by separate fixed seed.","Stock effect includes changed relative weight of each new arrival and resulting feedback, not merely terminal arithmetic dilution.","State effect includes pair mass, internal balance and all six alternative shares; not a causal real-market mechanism or a single historical-time effect.","Monte Carlo intervals conditional on synthetic grid, not independent empirical tests or simultaneous inference. No actual participant, odds calibration, or wagering advice."]};
}
function compact(r){
 const triple=x=>[x.mean,...x.mc95];
 return {qa:r.qa,parent_numeric_values:r.parent_numeric_values,n:r.rows.length,counts:r.counts,
  selected:r.rows.filter(x=>x.alpha===1.5&&x.tau===0&&x.delta===4).map(x=>({field:x.field,kind:x.kind,before:{early_mass:x.before.E.reverse_pair_mass.mean,late_mass:x.before.L.reverse_pair_mass.mean,early_r:x.before.E.reverse_r.mean,late_r:x.before.L.reverse_r.mean},arms:Object.fromEntries(ARMS.map(k=>[k,triple(x.arms[k].reverse_r)])),r:Object.fromEntries(Object.entries(x.decomposition.reverse_r).map(([k,v])=>[k,triple(v)])),D:Object.fromEntries(Object.entries(x.decomposition.D).map(([k,v])=>[k,triple(v)])),flow:Object.fromEntries(Object.entries(x.decomposition.flow_reverse_difference).map(([k,v])=>[k,triple(v)]))})),
  all:r.rows.map(x=>[x.field,x.alpha,x.tau,x.delta,x.kind,...["reverse_r","D","R","M","flow_reverse_difference"].flatMap(k=>["total","stock","state","interaction"].flatMap(j=>triple(x.decomposition[k][j])))])};
}

const prior=JSON.parse(readFileSync(process.argv[3],"utf8"));const result=compute(cfg,prior),s=compact(result);
const original=JSON.parse(readFileSync(process.argv[4],"utf8"));let n=0,max=0;
function same(a,b){if(typeof a==="number"){near(a,b,1e-9*Math.max(1,Math.abs(a)));max=Math.max(max,Math.abs(a-b));n++;}else if(a!==null&&typeof a==="object"){if(!b||JSON.stringify(Object.keys(a))!==JSON.stringify(Object.keys(b)))throw Error("HOLD_KEYS");for(const k of Object.keys(a))same(a[k],b[k]);}else if(a!==b)throw Error("HOLD_VALUE");}
same(original,s);
const out=process.argv[2]||"tmp/market-stock-state-counterfactual.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");
console.log(JSON.stringify({status:"SYNTHETIC_STOCK_STATE_REPLAY",parent_numeric_values:result.parent_numeric_values,summary_numeric_values:n,max_abs_diff:max,rows:result.rows.length,qa:result.qa,counts:result.counts}));
