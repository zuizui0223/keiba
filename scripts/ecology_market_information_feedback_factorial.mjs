// Research-only synthetic aggregate support dynamics; Node >=18.
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {dirname} from 'node:path';
const c={
  "seed": 20261127,
  "reps": 128,
  "bridgeReps": 256,
  "batches": 60,
  "batch": 12,
  "initial": [
    20,
    8,
    9,
    9,
    9,
    9,
    8,
    8
  ],
  "theta": [
    0.35,
    0.35,
    -0.6,
    -0.35,
    -0.1,
    0.15,
    0.5,
    0.8
  ],
  "alpha": [
    -0.5,
    0,
    0.5,
    1,
    1.25,
    1.5
  ],
  "b": [
    0,
    0.2,
    1,
    2
  ],
  "tau": [
    0,
    0.5,
    2,
    6
  ],
  "bridgeAlpha": [
    0.5,
    1,
    1.5
  ],
  "stabilityDraws": 32768
};
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return(((t^(t>>>14))>>>0)+.5)/4294967296;};}

function shocks(c,r){const next=rng((c.seed+Math.imul(r+1,0x9E3779B9))>>>0),n=c.batches*c.batch*c.theta.length,z=new Float64Array(n),g=new Float64Array(n);for(let i=0;i<n;i+=2){const u=next(),v=next(),m=Math.sqrt(-2*Math.log(u));z[i]=m*Math.cos(2*Math.PI*v);if(i+1<n)z[i+1]=m*Math.sin(2*Math.PI*v);}for(let i=0;i<n;i++)g[i]=-Math.log(-Math.log(next()));return {z,g};}

function avg(a){return a.reduce((x,y)=>x+y,0)/a.length;}

function stat(a){const m=avg(a),sd=Math.sqrt(a.reduce((x,y)=>x+(y-m)**2,0)/(a.length-1));return {mean:m,mc95:[m-1.96*sd/Math.sqrt(a.length),m+1.96*sd/Math.sqrt(a.length)],sd};}

function near(a,b,tol=1e-10){if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("HOLD_NUMERIC_IDENTITY "+a+" "+b);}

function sim(c,sh,alpha,b,tau,swap=true){
 const n=c.theta.length,a=c.initial.slice(),d=c.initial.slice();if(swap)[d[0],d[1]]=[d[1],d[0]];
 const m0=a.reduce((x,y)=>x+y,0),mass=m0+c.batches*c.batch,mu=c.theta.map(x=>b*x);
 for(let t=0;t<c.batches;t++){
  const sa=a.map(x=>alpha*Math.log(x)),sb=d.map(x=>alpha*Math.log(x));
  for(let j=0;j<c.batch;j++){
   let ia=-1,ib=-1,ma=-Infinity,mb=-Infinity,off=(t*c.batch+j)*n;
   for(let i=0;i<n;i++){
    const v=mu[i]+tau*sh.z[off+i]+sh.g[off+i],va=v+sa[i],vb=v+sb[i];
    if(va>ma){ia=i;ma=va;}if(vb>mb){ib=i;mb=vb;}
   }
   a[ia]++;d[ib]++;
  }
 }
 if(a.reduce((x,y)=>x+y,0)!==mass||d.reduce((x,y)=>x+y,0)!==mass||a.some(x=>x<=0)||d.some(x=>x<=0))throw Error("HOLD_MASS");
 const ma=(a[0]+a[1])/mass,mb=(d[0]+d[1])/mass,ra=(a[0]-a[1])/(a[0]+a[1]),rb=(d[0]-d[1])/(d[0]+d[1]);
 const D=((a[0]-a[1])-(d[0]-d[1]))/(2*mass),R=(ra-rb)/2,M=(ma+mb)/2,internal=M*R,cross=(ra+rb)/2*(ma-mb)/2;
 near(D,internal+cross);
 return {D,R,M,internal,cross,tv:a.reduce((v,x,i)=>v+Math.abs(x-d[i]),0)/(2*mass),hhi:(a.reduce((v,x)=>v+(x/mass)**2,0)+d.reduce((v,x)=>v+(x/mass)**2,0))/2};
}

function summarize(x,c){const out={};for(const k of Object.keys(x[0]))out[k]=stat(x.map(v=>v[k]));const D0=(c.initial[0]-c.initial[1])/c.initial.reduce((a,b)=>a+b,0),R0=(c.initial[0]-c.initial[1])/(c.initial[0]+c.initial[1]);out.finite_horizon_D=out.D.mc95[0]>D0?"AMPLIFIES":out.D.mc95[1]<D0?"ATTENUATES":"UNRESOLVED";out.finite_horizon_R=out.R.mc95[0]>R0?"AMPLIFIES":out.R.mc95[1]<R0?"ATTENUATES":"UNRESOLVED";return out;}

function contrast(x,y){const out={};for(const k of ["D","R","M","internal","cross","hhi"])out[k]=stat(x.map((v,i)=>v[k]-y[i][k]));return out;}

function checks(c){const sh=shocks(c,0),D0=(c.initial[0]-c.initial[1])/(c.initial.reduce((a,b)=>a+b,0)+c.batches*c.batch);
 for(const b of c.b)for(const tau of c.tau){const x=sim(c,sh,0,b,tau);near(x.D,D0);near(x.tv,D0);const y=sim(c,sh,1.5,b,tau,false);near(y.D,0);near(y.R,0);near(y.tv,0);}
 const x=sim(c,sh,1.25,1,.5),y=sim(c,shocks(c,0),1.25,1,.5);if(JSON.stringify(x)!==JSON.stringify(y))throw Error("HOLD_REPRO");
 return {mass:true,exact_D_decomposition:true,zero_feedback_mechanical:true,identical_world:true,deterministic:true};
}

function stability(c){
 // Expected softmax response at symmetric uniform shares and equal true strengths.
 // Common independent normal vectors for all tau. Gumbel integrated analytically.
 const next=rng(20261201),n=c.theta.length,arr=new Map(c.tau.map(t=>[t,[]]));for(let r=0;r<c.stabilityDraws;r++){
  const z=[];while(z.length<n){const a=next(),b=next(),s=Math.sqrt(-2*Math.log(a));z.push(s*Math.cos(2*Math.PI*b),s*Math.sin(2*Math.PI*b));}
  for(const tau of c.tau){const x=z.map(v=>v*tau),mx=Math.max(...x),w=x.map(v=>Math.exp(v-mx)),s=w.reduce((a,b)=>a+b,0),hh=w.reduce((a,v)=>a+(v/s)**2,0);arr.get(tau).push(n/(n-1)*(1-hh));}
 }
 return c.tau.map(tau=>{const k=stat(arr.get(tau));return {tau,kappa:k,critical_alpha:1/k.mean,mc95_inverse:[1/k.mc95[1],1/k.mc95[0]],note:"local linear stability of uniform expected drift for equal strengths, not finite-horizon threshold"};});
}

function run(c){
 const qa=checks(c),cells=new Map(),bridge=new Map(),bH=2/(1+.25**2),bL=2/(1+3**2),tH=2*.25/(1+.25**2),tL=2*3/(1+3**2);
 for(const a of c.alpha)for(const b of c.b)for(const t of c.tau)cells.set([a,b,t].join("|"),[]);
 for(const a of c.bridgeAlpha)for(const name of ["HH","LH","HL","LL","rawH","rawL"])bridge.set([a,name].join("|"),[]);
 for(let r=0;r<Math.max(c.reps,c.bridgeReps);r++){
  const sh=shocks(c,r);
  if(r<c.reps)for(const a of c.alpha)for(const b of c.b)for(const t of c.tau)cells.get([a,b,t].join("|")).push(sim(c,sh,a,b,t));
  if(r<c.bridgeReps)for(const a of c.bridgeAlpha)for(const [name,b,t] of [["HH",bH,tH],["LH",bL,tH],["HL",bH,tL],["LL",bL,tL],["rawH",2,.5],["rawL",2,6]])bridge.get([a,name].join("|")).push(sim(c,sh,a,b,t));
 }
 const grid=[],effects=[],bridgeOut=[];
 for(const a of c.alpha)for(const b of c.b)for(const t of c.tau)grid.push({alpha:a,b,tau:t,...summarize(cells.get([a,b,t].join("|")),c)});
 for(const a of c.alpha){
  for(const t of c.tau)effects.push({alpha:a,kind:"weaker_mean",fixed_tau:t,...contrast(cells.get([a,c.b[0],t].join("|")),cells.get([a,c.b.at(-1),t].join("|")))});
  for(const b of c.b)effects.push({alpha:a,kind:"larger_dispersion",fixed_b:b,...contrast(cells.get([a,b,c.tau.at(-1)].join("|")),cells.get([a,b,c.tau[0]].join("|")))});
 }
 for(const a of c.bridgeAlpha){
  const get=k=>bridge.get([a,k].join("|")),HH=get("HH"),LH=get("LH"),HL=get("HL"),LL=get("LL");
  const parts={};for(const k of ["D","R","M","internal","cross"]){
   const m=HH.map((x,i)=>.5*((LH[i][k]-x[k])+(LL[i][k]-HL[i][k]))),t=HH.map((x,i)=>.5*((HL[i][k]-x[k])+(LL[i][k]-LH[i][k]))),total=HH.map((x,i)=>LL[i][k]-x[k]);
   for(let i=0;i<m.length;i++)near(total[i],m[i]+t[i]);
   parts[k]={weaker_mean:stat(m),changed_dispersion:stat(t),total:stat(total)};
  }
  bridgeOut.push({alpha:a,parameters:{bH,bL,tH,tL},corners:Object.fromEntries(["HH","LH","HL","LL","rawH","rawL"].map(k=>[k,summarize(get(k),c)])),shapley_two_factor:parts,raw_low_minus_high:contrast(get("rawL"),get("rawH"))});
 }
 return {status:"SYNTHETIC_MARKET_FACTORIAL",config:c,qa,initial_D:.15,initial_R:12/28,mechanical_D:.015,grid,effects,bridge:bridgeOut,local_uniform_stability:stability(c),limits:["Artificial support counts; not calibrated real participants, odds or horse outcomes.","Finite-horizon classifications compare MC95 means to starting D or R, not asymptotic phase boundaries.","Expected drift local stability calculation assumes all latent strengths equal, uniform shares, independent Gaussian heterogeneity and analytically integrated Gumbel noise; not applicable unmodified to heterogeneous fields.","Two-factor bridge decomposition is arithmetic conditional on four interventions; no real causal effect.","Grid fixes one artificial ability field, initial counts and batch size; net feedback cannot separate imitation and price response. No real horse-history-to-noise mapping.","MC intervals conditional on these scenarios and common shocks; no simultaneous multiplicity adjustment."]};
}
const result=run(c);
if(process.argv[3]){const p=JSON.parse(readFileSync(process.argv[3],"utf8"));for(const r of result.bridge){for(const [k,mode,sigma] of [["HH","posterior",.25],["LL","posterior",3],["rawH","raw",.25],["rawL","raw",3]]){const x=p.cells.find(v=>v.alpha===r.alpha&&v.mode===mode&&v.sigma===sigma);if(!x)throw Error("HOLD_PARENT_MISSING");near(r.corners[k].D.mean,x.terminal_intervention.mean);}}result.original_PR119_endpoint_mean_parity=true;}
const out=process.argv[2]||"tmp/market-information-feedback-factorial.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");console.log(JSON.stringify(result));
