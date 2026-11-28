// Synthetic popularity state composition; research only.
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
  },
  "components": [
    "pair_mass",
    "internal_balance",
    "outside_composition"
  ]
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

const KEY_METRICS=["reverse_r","D","R","M","flow_reverse_difference"];
function parts(v,T){
 const sum=v[0]+v[1],outside=T-sum;
 if(!(sum>0&&outside>0))throw Error("HOLD_SIMPLEX");
 const out={m:sum/T,r:(v[0]-v[1])/sum,C:v.slice(2).map(x=>x/outside)};
 near(out.C.reduce((s,x)=>s+x,0),1);return out;
}
function mix(e,l,T,mask){
 // Exact endpoints use original rescaling to preserve previous replay.
 if(mask===7)return rescale(e,T);
 if(mask===0)return rescale(l,T);
 const choose=(bit,k)=>(mask&bit?e:l);
 function make(side){
  const a=parts(e[side],e.T),b=parts(l[side],l.T);
  const m=(mask&1?a:b).m,r=(mask&2?a:b).r,C=(mask&4?a:b).C;
  const v=[T*m*(1+r)/2,T*m*(1-r)/2,...C.map(x=>T*(1-m)*x)];
  if(v.some(x=>!(x>0)))throw Error("HOLD_POSITIVE");
  near(v.reduce((x,y)=>x+y,0),T,1e-8);const q=parts(v,T);
  near(q.m,m);near(q.r,r);q.C.forEach((x,i)=>near(x,C[i]));return v;
 }
 return {a:make("a"),b:make("b"),T};
}
function nbits(x){return (x&1)+((x>>1)&1)+((x>>2)&1);}
function attribution(v){
 const phi=[];for(const bit of [1,2,4]){
  let x=0;for(let m=0;m<8;m++)if(!(m&bit)){const k=nbits(m),w=k===1?1/6:1/3;x+=w*(v[m|bit]-v[m]);}phi.push(x);
 }
 const total=v[7]-v[0];near(phi.reduce((a,b)=>a+b,0),total);
 // Baseline-anchored factorial differences, distinct from Shapley allocations.
 const i12=v[3]-v[1]-v[2]+v[0],i13=v[5]-v[1]-v[4]+v[0],i23=v[6]-v[2]-v[4]+v[0];
 const i123=v[7]-v[6]-v[5]-v[3]+v[4]+v[2]+v[1]-v[0];
 near(total,(v[1]-v[0])+(v[2]-v[0])+(v[4]-v[0])+i12+i13+i23+i123);
 return {total,pair_mass:phi[0],internal_balance:phi[1],outside_composition:phi[2],mass_balance_interaction:i12,mass_outside_interaction:i13,balance_outside_interaction:i23,three_way_interaction:i123};
}
function compute3(c,prior){
 const rows=[];let checked=0;
 for(const [field,theta] of Object.entries(c.fields))for(const alpha of c.alpha)for(const tau of c.tau)for(const delta of c.delta){
  const all={differential:[],group:[]};
  for(let r=0;r<c.reps;r++){
   const h=history(c,shocks(c,r),theta,alpha,tau,delta),sh=shocks({...c,seed:c.postSeed},r);
   const es=h[10],ls=h[40],out={differential:[],group:[]};
   for(const T of c.stock){
    const base=[],x=[];for(let mask=0;mask<8;mask++){x.push(mix(es,ls,T,mask));base.push(post(c,x[mask],sh,theta,alpha,tau,c.kinds.none));}
    for(const kind of ["differential","group"]){
     const arms=x.map((v,m)=>effect(post(c,v,sh,theta,alpha,tau,c.kinds[kind]),base[m]));
     out[kind].push({arms,attrib:Object.fromEntries(KEY_METRICS.map(k=>[k,attribution(arms.map(v=>v[k]))]))});
    }
   }
   for(const kind of ["differential","group"]){
    const s=out[kind][0],l=out[kind][1],e={ES:s.arms[7],EL:l.arms[7],LS:s.arms[0],LL:l.arms[0]},old=decomposition(e),averaged={};
    for(const k of KEY_METRICS){averaged[k]={};for(const j of Object.keys(s.attrib[k]))averaged[k][j]=.5*(s.attrib[k][j]+l.attrib[k][j]);near(averaged[k].total,old[k].state);near(averaged[k].pair_mass+averaged[k].internal_balance+averaged[k].outside_composition,old[k].state);}
    all[kind].push({small:s,large:l,old,averaged});
   }
  }
  for(const kind of ["differential","group"]){
   const a=all[kind],old=prior.all.find(x=>x[0]===field&&x[1]===alpha&&x[2]===tau&&x[3]===delta&&x[4]===kind);
   if(!old)throw Error("HOLD_PARENT");
   let i=5;for(const k of KEY_METRICS)for(const j of ["total","stock","state","interaction"]){
    const q=stat(a.map(x=>x.old[k][j]));for(const x of [q.mean,...q.mc95]){near(x,old[i++]);checked++;}
   }
   if(i!==old.length)throw Error("HOLD_PARENT_LAYOUT");
   const summaries={};for(const stock of ["small","large","averaged"])summaries[stock]=Object.fromEntries(KEY_METRICS.map(k=>[k,summarize(a.map(x=>stock==="averaged"?x.averaged[k]:x[stock].attrib[k]))]));
   const arms={};for(const stock of ["small","large"])arms[stock]=Array.from({length:8},(_,m)=>summarize(a.map(x=>x[stock].arms[m])));
   rows.push({field,alpha,tau,delta,kind,summaries,arms});
  }
 }
 if(checked!==96*5*4*3)throw Error("HOLD_PARENT_COUNT");
 const counts={};for(const kind of ["differential","group"]){counts[kind]={};for(const k of KEY_METRICS){counts[kind][k]={};for(const name of ["total",...c.components]){const z={positive:0,negative:0,unresolved:0};for(const row of rows.filter(x=>x.kind===kind)){const q=row.summaries.averaged[k][name];z[q.mc95[0]>0?"positive":q.mc95[1]<0?"negative":"unresolved"]++;}counts[kind][k][name]=z;}}}
 return {status:"SYNTHETIC_STATE_COMPONENTS_COUNTERFACTUAL",config:c,qa:{simplex:true,component_preservation:true,exact_attribution:true,PR124_factorial_parity:true},parent_numeric_values:checked,rows,counts,limits:["Synthetic state interventions, not actual market participants or prices.","Three components are reconstructed separately in each mirrored world; hybrid fractional support states need not be reachable by the original history.","Shapley values are arithmetic averages over the six replacement orders, not unique mechanistic or empirical causal attributions.","Composition and feedback can interact, and the early/late components are correlated in original histories. Same original 48 scenarios and 128 histories, no new empirical validation.","MC95 conditional on synthetic scenarios, common shocks and fitted-free model; no multiplicity adjustment or real-world confidence claims."]};
}
function compact3(r){
 const tri=x=>[x.mean,...x.mc95],parts=["total","pair_mass","internal_balance","outside_composition"];
 return {qa:r.qa,parent_numeric_values:r.parent_numeric_values,n:r.rows.length,counts:r.counts,selected:r.rows.filter(x=>x.alpha===1.5&&x.tau===0&&x.delta===4).map(x=>({field:x.field,kind:x.kind,components:Object.fromEntries(["reverse_r","D","flow_reverse_difference"].map(k=>[k,Object.fromEntries(Object.entries(x.summaries.averaged[k]).map(([j,v])=>[j,tri(v)]))])),stock:Object.fromEntries(["small","large"].map(s=>[s,Object.fromEntries(parts.map(k=>[k,tri(x.summaries[s].reverse_r[k])]))]))})),all:r.rows.map(x=>[x.field,x.alpha,x.tau,x.delta,x.kind,...KEY_METRICS.flatMap(k=>parts.flatMap(j=>tri(x.summaries.averaged[k][j])))])};
}

const prior=JSON.parse(readFileSync(process.argv[3],"utf8"));const result=compute3(cfg,prior),s=compact3(result);
const original=JSON.parse(readFileSync(process.argv[4],"utf8"));let n=0,max=0;
function same(a,b){if(typeof a==="number"){near(a,b,1e-9*Math.max(1,Math.abs(a)));max=Math.max(max,Math.abs(a-b));n++;}else if(a!==null&&typeof a==="object"){if(!b||JSON.stringify(Object.keys(a))!==JSON.stringify(Object.keys(b)))throw Error("HOLD_KEYS");for(const k of Object.keys(a))same(a[k],b[k]);}else if(a!==b)throw Error("HOLD_VALUE");}
same(original,s);const out=process.argv[2]||"tmp/market-state-components-counterfactual.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");console.log(JSON.stringify({status:"SYNTHETIC_STATE_COMPONENTS_REPLAY",parent_numeric_values:result.parent_numeric_values,summary_numeric_values:n,max_abs_diff:max,rows:result.rows.length,qa:result.qa,counts:result.counts}));
