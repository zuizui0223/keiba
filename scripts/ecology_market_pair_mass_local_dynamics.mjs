// Research-only local expected-drift dynamics and synthetic ABM comparison.
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {dirname} from 'node:path';
const cfg={
  "seed": 20261127,
  "quadratureSeed": 20261130,
  "reps": 128,
  "batches": 60,
  "batch": 12,
  "n": 8,
  "b": 2,
  "alpha": [
    0,
    0.8,
    1,
    1.25,
    1.5,
    1.75,
    3.5,
    4
  ],
  "tau": [
    0,
    2,
    6
  ],
  "checkpoints": [
    10,
    30,
    60
  ],
  "quadrature": [
    1024,
    2048
  ],
  "delta": 1,
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
  }
};
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return(((t^(t>>>14))>>>0)+.5)/4294967296;};}

function shocks(c,r){const next=rng((c.seed+Math.imul(r+1,0x9E3779B9))>>>0),n=c.batches*c.batch*c.n,z=new Float64Array(n),g=new Float64Array(n);for(let i=0;i<n;i+=2){const u=next(),v=next(),m=Math.sqrt(-2*Math.log(u));z[i]=m*Math.cos(2*Math.PI*v);if(i+1<n)z[i+1]=m*Math.sin(2*Math.PI*v);}for(let i=0;i<n;i++)g[i]=-Math.log(-Math.log(next()));return {z,g};}

function near(a,b,tol=1e-10){if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("HOLD_NUMERIC "+a+" "+b);}

function stat(a){const m=a.reduce((v,x)=>v+x,0)/a.length,sd=Math.sqrt(a.reduce((v,x)=>v+(x-m)**2,0)/(a.length-1));return {mean:m,mc95:[m-1.96*sd/Math.sqrt(a.length),m+1.96*sd/Math.sqrt(a.length)],sd};}

function bank(c){const next=rng(c.quadratureSeed),z=new Float64Array(c.n*c.quadrature.at(-1));for(let i=0;i<z.length;i+=2){const a=next(),b=next(),m=Math.sqrt(-2*Math.log(a));z[i]=m*Math.cos(2*Math.PI*b);z[i+1]=m*Math.sin(2*Math.PI*b);}return z;}

function response(c,x,theta,alpha,tau,z,draws,test=false){
 const n=c.n,L=tau===0?1:draws,mu=x.map((v,i)=>c.b*theta[i]+alpha*Math.log(v)),p=new Float64Array(n),w=new Float64Array(n);
 const groups=new Map();for(let i=0;i<n;i++){const k=String(theta[i]);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(i);}
 const focal=groups.get(String(theta[0])),k=focal.length,pairN=k*(k-1)/2;
 if(!focal.includes(1)||k<2)throw Error("HOLD_SYMMETRY");
 for(const ids of groups.values())for(const i of ids)near(x[i],x[ids[0]]);
 let diffSq=0,fd=0;
 // Match the reference's permutation projection in BOTH the first moment
 // and pairwise derivative. Average squared differences over every pair
 // of the exchangeable focal group, including all 28 pairs in equal field.
 for(let r=0;r<L;r++){let mx=-Infinity;for(let i=0;i<n;i++){w[i]=mu[i]+tau*z[r*n+i];if(w[i]>mx)mx=w[i];}let s=0;for(let i=0;i<n;i++){w[i]=Math.exp(w[i]-mx);s+=w[i];}for(let i=0;i<n;i++){w[i]/=s;p[i]+=w[i];}
  let total=0,sq=0;for(const i of focal){total+=w[i];sq+=w[i]*w[i];}diffSq+=Math.max(0,k*sq-total*total)/pairN;
  if(test){const e=1e-5;for(let i=0;i<k;i++)for(let j=i+1;j<k;j++){const a=w[focal[i]],b=w[focal[j]],f=u=>{const ap=a*Math.pow(1+u,alpha),bp=b*Math.pow(1-u,alpha);return (ap-bp)/(1-a-b+ap+bp);};fd+=(f(e)-f(-e))/(2*e*pairN);}}
 }
 for(let i=0;i<n;i++)p[i]/=L;
 for(const ids of groups.values()){const mean=ids.reduce((s,i)=>s+p[i],0)/ids.length;for(const i of ids)p[i]=mean;}
 near(p.reduce((a,b)=>a+b,0),1);
 const P=p[0]+p[1],K=(P-diffSq/L)/P;
 if(!(P>0&&K>=-1e-10&&K<=1+1e-10))throw Error("HOLD_RESPONSE");
 let derivativeError=0;if(test){derivativeError=Math.abs(fd/L-alpha*P*K);near(fd/L,alpha*P*K,2e-8);}
 return {p:Array.from(p),P,K,derivativeError};
}

function sign(a,b){return a>b+1e-10?"GROW":a<b-1e-10?"SHRINK":"NEUTRAL";}

function classMC(z){return z.mc95[0]>1?"GROW":z.mc95[1]<1?"SHRINK":"UNRESOLVED";}

function ref(c,theta,a,tau,z,draws,tests=false){
 let x=Array(c.n).fill(10),D=1,R=1,maxIdentity=0,maxDerivative=0;const records=[],steps=[],joint={};
 for(let t=0;t<c.batches;t++){
  const T=80+t*c.batch,M=(x[0]+x[1])/T;near(x[0],x[1]);near(x.reduce((s,v)=>s+v,0),T);
  const resp=response(c,x,theta,a,tau,z,draws,tests&&[0,29,59].includes(t)),P=resp.P,K=resp.K;
  maxDerivative=Math.max(maxDerivative,resp.derivativeError);
  const gd=(T+c.batch*a*K*P/M)/(T+c.batch),gr=(T*M+c.batch*a*K*P)/(T*M+c.batch*P),mn=(T*M+c.batch*P)/(T+c.batch);
  const ident=Math.abs(gd-(mn/M)*gr);maxIdentity=Math.max(maxIdentity,ident);near(gd,(mn/M)*gr);
  const sd=sign(gd,1),sr=sign(gr,1),sm=sign(mn,M),key=sd+"/"+sr;joint[key]=(joint[key]||0)+1;
  D*=gd;R*=gr;x=x.map((v,i)=>v+c.batch*resp.p[i]);near(D,R*mn/.25,1e-8*Math.max(1,Math.abs(D)));
  const row={batch:t+1,mass_before:M,new_pair_probability:P,kappa:K,flow_ratio:P/M,within_condition:a*K,aggregate_condition:a*K*P/M,D_step:gd,R_step:gr,pair_mass:mn,D_gain:D,R_gain:R,aggregate:sd,internal:sr,mass_change:sm};
  steps.push(row);if(c.checkpoints.includes(t+1))records.push(row);
 }
 return {checkpoints:records,first:steps[0],last:steps.at(-1),joint_steps:joint,maxIdentity,maxDerivative,steps};
}

function measure(a,b,mass){const ma=(a[0]+a[1])/mass,mb=(b[0]+b[1])/mass,ra=(a[0]-a[1])/(a[0]+a[1]),rb=(b[0]-b[1])/(b[0]+b[1]),D=((a[0]-a[1])-(b[0]-b[1]))/(2*mass),R=(ra-rb)/2,M=(ma+mb)/2;near(D,M*R+(ra+rb)/2*(ma-mb)/2);return {D,R,M};}

function sim(c,sh,theta,alpha,tau,swap=true){
 const a=[11,9,10,10,10,10,10,10],b=a.slice(),n=c.n,mu=theta.map(x=>c.b*x),out=[];if(swap)[b[0],b[1]]=[b[1],b[0]];
 for(let t=0;t<c.batches;t++){const sa=a.map(x=>alpha*Math.log(x)),sb=b.map(x=>alpha*Math.log(x));for(let j=0;j<c.batch;j++){let ia=-1,ib=-1,ma=-Infinity,mb=-Infinity,off=(t*c.batch+j)*n;for(let i=0;i<n;i++){const v=mu[i]+tau*sh.z[off+i]+sh.g[off+i],va=v+sa[i],vb=v+sb[i];if(va>ma){ma=va;ia=i;}if(vb>mb){mb=vb;ib=i;}}a[ia]++;b[ib]++;}if(c.checkpoints.includes(t+1)){const mass=80+(t+1)*c.batch;near(a.reduce((x,y)=>x+y,0),mass);near(b.reduce((x,y)=>x+y,0),mass);out.push(measure(a,b,mass));}}
 return out;
}

function run(c){
 const z=bank(c),cells=[],samples=new Map(),refPaths=[],sh0=shocks(c,0);
 for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const t of c.tau){const key=[f,a,t].join("|");samples.set(key,[]);
  const r=ref(c,theta,a,t,z,c.quadrature.at(-1),a===1.5),l=t===0?r:ref(c,theta,a,t,z,c.quadrature[0]);
  const sensitivity=r.checkpoints.map((q,i)=>({batch:q.batch,D_gain_difference:q.D_gain-l.checkpoints[i].D_gain,R_gain_difference:q.R_gain-l.checkpoints[i].R_gain,pair_mass_difference:q.pair_mass-l.checkpoints[i].pair_mass}));
  if(a===0){for(const q of r.checkpoints)near(q.D_gain,80/(80+q.batch*c.batch));}
  if(f==="equal"&&t===0){for(const q of r.checkpoints){near(q.pair_mass,.25);near(q.kappa,1);near(q.D_gain,q.R_gain);}}
  if(a===1.5)refPaths.push({field:f,alpha:a,tau:t,steps:r.steps});
  cells.push({field:f,alpha:a,tau:t,reference:{checkpoints:r.checkpoints,first:r.first,last:r.last,joint_steps:r.joint_steps,max_identity_error:r.maxIdentity,max_derivative_error:r.maxDerivative},quadrature_sensitivity:sensitivity});
  const zero=sim(c,sh0,theta,0,t),same=sim(c,sh0,theta,a,t,false);for(let i=0;i<c.checkpoints.length;i++){near(zero[i].D,2/(80+c.checkpoints[i]*c.batch));near(same[i].D,0);near(same[i].R,0);}
 }
 for(let r=0;r<c.reps;r++){const sh=shocks(c,r);for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const t of c.tau)samples.get([f,a,t].join("|")).push(sim(c,sh,theta,a,t));}
 let compare={both_conclusive:0,both_correct:0,D_conclusive:0,D_correct:0,R_conclusive:0,R_correct:0,opposite_ABM:0,opposite_correct:0},byAlpha={};
 for(const row of cells){const a=samples.get([row.field,row.alpha,row.tau].join("|"));row.abm=c.checkpoints.map((b,i)=>{const x=a.map(v=>v[i]),D=stat(x.map(v=>v.D/.025)),R=stat(x.map(v=>v.R/.1)),M=stat(x.map(v=>v.M));return {batch:b,D_gain:D,R_gain:R,pair_mass:M,D_status:classMC(D),R_status:classMC(R)};});
  const x=row.abm.at(-1),v=row.reference.last,d=sign(v.D_gain,1),r=sign(v.R_gain,1);
  row.terminal_comparison={local_D:d,local_R:r,ABM_D:x.D_status,ABM_R:x.R_status,D_ratio_error:v.D_gain-x.D_gain.mean,R_ratio_error:v.R_gain-x.R_gain.mean};
  if(x.D_status!=="UNRESOLVED"){compare.D_conclusive++;if(d===x.D_status)compare.D_correct++;}
  if(x.R_status!=="UNRESOLVED"){compare.R_conclusive++;if(r===x.R_status)compare.R_correct++;}
  if(x.D_status!=="UNRESOLVED"&&x.R_status!=="UNRESOLVED"){compare.both_conclusive++;if(d===x.D_status&&r===x.R_status)compare.both_correct++;if(x.D_status!==x.R_status){compare.opposite_ABM++;if(d===x.D_status&&r===x.R_status)compare.opposite_correct++;}}
  const k=String(row.alpha);if(!byAlpha[k])byAlpha[k]={D_conclusive:0,D_correct:0,R_conclusive:0,R_correct:0};if(x.D_status!=="UNRESOLVED"){byAlpha[k].D_conclusive++;if(d===x.D_status)byAlpha[k].D_correct++;}if(x.R_status!=="UNRESOLVED"){byAlpha[k].R_conclusive++;if(r===x.R_status)byAlpha[k].R_correct++;}
 }
 return {status:"SYNTHETIC_PAIR_LOCAL_DYNAMICS",config:c,qa:{zero_feedback:true,identical_world:true,conservation:true,exact_reference_factorization:true,finite_difference_checked_alpha_1_5:true,max_step_identity_error:Math.max(...cells.map(x=>x.reference.max_identity_error)),max_checked_derivative_error:Math.max(...cells.map(x=>x.reference.max_derivative_error))},cells,refPaths,compare,byAlpha,limits:["Local derivative around deterministic exchange-symmetric reference, not a global threshold or the stochastic expected trajectory.","Gaussian expectation approximated by a fixed nested bank of 1024/2048 draws; imposed exact permutation symmetry for equal-strength reference groups in both first moments and pair derivatives. Quadrature sensitivity not an empirical CI.","ABM small but finite initial difference, 128 replicates from PR121 same seed; local sign comparison conditional on 96 chosen cells, not independent prediction evidence.","The pair share and derivative depend on time, competing latent strengths, and alpha itself; a state-specific inequality is not a single exogenous critical alpha.","Synthetic aggregate support counts only, no real market or participant identification, causal or genetic claim, actual prices or wagering."]};
}
const result=run(cfg);
const p=JSON.parse(readFileSync(process.argv[3],"utf8"));let parentN=0;for(const row of result.cells){const prior=p.rows.find(x=>x.field===row.field&&x.alpha===row.alpha&&x.tau===row.tau&&x.delta===1);if(!prior)throw Error("HOLD_PARENT_CELL");for(let i=0;i<row.abm.length;i++){const z=row.abm[i],q=prior.checkpoints[i];for(const k of ["D_gain","R_gain","pair_mass"])for(const field of ["mean","sd","mc95"]){const a=z[k][field],b=q[k][field];if(Array.isArray(a)){a.forEach((v,j)=>near(v,b[j]));parentN+=a.length;}else{near(a,b);parentN++;}}}}if(parentN!==96*3*3*4)throw Error("HOLD_PARENT_COUNT");
const out=process.argv[2]||"tmp/market-pair-mass-local-dynamics.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");const orig=JSON.parse(readFileSync(process.argv[4],"utf8"));let max=0,n=0;function same(a,b){if(typeof a==="number"){near(a,b,1e-8*Math.max(1,Math.abs(a)));max=Math.max(max,Math.abs(a-b));n++;}else if(a!==null&&typeof a==="object"){if(!b||JSON.stringify(Object.keys(a))!==JSON.stringify(Object.keys(b)))throw Error("HOLD_KEYS");for(const k of Object.keys(a))same(a[k],b[k]);}else if(a!==b)throw Error("HOLD_VALUE");}same(orig,result);console.log(JSON.stringify({status:"SYNTHETIC_PAIR_DYNAMICS_REPLAY",parent_numeric_values:parentN,numeric_values:n,max_abs_diff:max,rows:result.cells.length,qa:result.qa,compare:result.compare}));
