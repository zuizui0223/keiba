// Research-only synthetic support dynamics; no real-market calibration.
import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {dirname} from 'node:path';
const cfg={
  "seed": 20261127,
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
  "delta": [
    1,
    4,
    8
  ],
  "checkpoints": [
    10,
    30,
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
  }
};
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return(((t^(t>>>14))>>>0)+.5)/4294967296;};}

function shocks(c,r){const next=rng((c.seed+Math.imul(r+1,0x9E3779B9))>>>0),n=c.batches*c.batch*c.n,z=new Float64Array(n),g=new Float64Array(n);for(let i=0;i<n;i+=2){const u=next(),v=next(),m=Math.sqrt(-2*Math.log(u));z[i]=m*Math.cos(2*Math.PI*v);if(i+1<n)z[i+1]=m*Math.sin(2*Math.PI*v);}for(let i=0;i<n;i++)g[i]=-Math.log(-Math.log(next()));return {z,g};}

function near(a,b,tol=1e-10){if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("HOLD_NUMERIC "+a+" "+b);}

function stat(a){const m=a.reduce((v,x)=>v+x,0)/a.length,sd=Math.sqrt(a.reduce((v,x)=>v+(x-m)**2,0)/(a.length-1));return {mean:m,mc95:[m-1.96*sd/Math.sqrt(a.length),m+1.96*sd/Math.sqrt(a.length)],sd};}

function measure(a,b,mass){const ma=(a[0]+a[1])/mass,mb=(b[0]+b[1])/mass,ra=(a[0]-a[1])/(a[0]+a[1]),rb=(b[0]-b[1])/(b[0]+b[1]);const D=((a[0]-a[1])-(b[0]-b[1]))/(2*mass),R=(ra-rb)/2,M=(ma+mb)/2,internal=M*R,cross=(ra+rb)/2*(ma-mb)/2;near(D,internal+cross);return {D,R,M,internal,cross,tv:a.reduce((v,x,i)=>v+Math.abs(x-b[i]),0)/(2*mass)};}

function sim(c,sh,theta,initial,alpha,tau,swap=true){const a=initial.slice(),b=initial.slice(),n=c.n,mu=theta.map(x=>c.b*x),m0=initial.reduce((x,y)=>x+y,0),out=[];if(swap)[b[0],b[1]]=[b[1],b[0]];for(let t=0;t<c.batches;t++){const sa=a.map(x=>alpha*Math.log(x)),sb=b.map(x=>alpha*Math.log(x));for(let j=0;j<c.batch;j++){let ia=-1,ib=-1,ma=-Infinity,mb=-Infinity,off=(t*c.batch+j)*n;for(let i=0;i<n;i++){const v=mu[i]+tau*sh.z[off+i]+sh.g[off+i],va=v+sa[i],vb=v+sb[i];if(va>ma){ma=va;ia=i;}if(vb>mb){mb=vb;ib=i;}}a[ia]++;b[ib]++;}if(c.checkpoints.includes(t+1)){const mass=m0+(t+1)*c.batch;if(a.reduce((x,y)=>x+y,0)!==mass||b.reduce((x,y)=>x+y,0)!==mass||a.some(x=>x<=0)||b.some(x=>x<=0))throw Error("HOLD_MASS");out.push(measure(a,b,mass));}}return out;}

function initial(d){return [10+d,10-d,10,10,10,10,10,10];}

function label(z){return z.mc95[0]>1?"AMPLIFIES":z.mc95[1]<1?"ATTENUATES":"UNRESOLVED";}

function aggregate(a,d,c){return c.checkpoints.map((n,i)=>{const p=a.map(v=>v[i]),D0=2*d/80,R0=2*d/20,z={batch:n,count:80+n*c.batch,D_gain:stat(p.map(x=>x.D/D0)),R_gain:stat(p.map(x=>x.R/R0)),pair_mass:stat(p.map(x=>x.M)),cross:stat(p.map(x=>x.cross)),tv:stat(p.map(x=>x.tv))};z.D_status=label(z.D_gain);z.R_status=label(z.R_gain);return z;});}

function linear(c,alpha,kappa){let x=1,results=[];for(let t=0;t<c.batches;t++){x*=1+c.batch/(80+(t+1)*c.batch)*(alpha*kappa-1);if(c.checkpoints.includes(t+1))results.push({batch:t+1,gain:x});}return results;}

function softmax(x){const mx=Math.max(...x),a=x.map(v=>Math.exp(v-mx)),s=a.reduce((u,v)=>u+v,0);return a.map(v=>v/s);}

function deterministic(c,theta,counts,alpha){let a=counts.slice(),b=counts.slice();[b[0],b[1]]=[b[1],b[0]];const m0=counts.reduce((x,y)=>x+y,0),D0=(counts[0]-counts[1])/m0,out=[];for(let t=0;t<c.batches;t++){const step=x=>{const p=softmax(x.map((v,i)=>c.b*theta[i]+alpha*Math.log(v)));return x.map((v,i)=>v+c.batch*p[i]);};a=step(a);b=step(b);if(c.checkpoints.includes(t+1)){const m=m0+(t+1)*c.batch;near(a.reduce((x,y)=>x+y,0),m);near(b.reduce((x,y)=>x+y,0),m);out.push({batch:t+1,gain:measure(a,b,m).D/D0});}}return out;}

function checks(c,p){const sh=shocks(c,0);for(const theta of Object.values(c.fields))for(const d of c.delta)for(const tau of c.tau){const a=sim(c,sh,theta,initial(d),0,tau),b=sim(c,sh,theta,initial(d),1.5,tau,false);for(let i=0;i<c.checkpoints.length;i++){near(a[i].D,2*d/(80+c.checkpoints[i]*c.batch));near(a[i].tv,a[i].D);near(b[i].D,0);near(b[i].R,0);near(b[i].tv,0);}}const a=sim(c,sh,c.fields.heterogeneous,initial(4),1.5,2),b=sim(c,shocks(c,0),c.fields.heterogeneous,initial(4),1.5,2);if(JSON.stringify(a)!==JSON.stringify(b))throw Error("HOLD_REPRO");const bridge=[];for(const [alpha,tau] of [[0,0],[1,2],[1.5,0],[1.5,6]]){const target=p.grid.find(v=>v.alpha===alpha&&v.b===c.b&&v.tau===tau);if(!target)throw Error("HOLD_PARENT_CELL");const z=[];for(let r=0;r<c.reps;r++)z.push(sim(c,shocks(c,r),c.fields.heterogeneous,[20,8,9,9,9,9,8,8],alpha,tau).at(-1));const means={D:stat(z.map(x=>x.D)).mean,R:stat(z.map(x=>x.R)).mean,M:stat(z.map(x=>x.M)).mean};for(const k of Object.keys(means))near(means[k],target[k].mean);bridge.push({alpha,tau,means});}let maxRelative=0;const e=1e-6,small=[10+e,10-e,10,10,10,10,10,10];for(const alpha of c.alpha){const x=deterministic(c,c.fields.equal,small,alpha),y=linear(c,alpha,1);for(let i=0;i<x.length;i++){const rel=Math.abs(x[i].gain-y[i].gain)/Math.max(1,Math.abs(y[i].gain));maxRelative=Math.max(maxRelative,rel);near(x[i].gain,y[i].gain,1e-6*Math.max(1,Math.abs(y[i].gain)));}}return {mass:true,exact_D_decomposition:true,zero_feedback_retention:true,identical_world:true,reproducible:true,PR120_bridge:bridge,tau0_local_linearization:true,tiny_perturbation:e,max_scaled_linearization_error:maxRelative};}

function run(c,p){const qa=checks(c,p),cells=new Map(),rows=[];for(const field of Object.keys(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta)cells.set([field,a,t,d].join("|"),[]);for(let r=0;r<c.reps;r++){const sh=shocks(c,r);for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta)cells.get([f,a,t,d].join("|")).push(sim(c,sh,theta,initial(d),a,t));}for(const f of Object.keys(c.fields))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta)rows.push({field:f,alpha:a,tau:t,delta:d,initial_D:2*d/80,initial_R:2*d/20,checkpoints:aggregate(cells.get([f,a,t,d].join("|")),d,c)});
const amplitude=[],fieldEffects=[];for(const f of Object.keys(c.fields))for(const a of c.alpha)for(const t of c.tau){const l=cells.get([f,a,t,c.delta.at(-1)].join("|")),s=cells.get([f,a,t,c.delta[0]].join("|"));amplitude.push({field:f,alpha:a,tau:t,large_minus_small_normalized_D:stat(l.map((x,i)=>x.at(-1).D/(2*c.delta.at(-1)/80)-s[i].at(-1).D/(2*c.delta[0]/80))),large_minus_small_normalized_R:stat(l.map((x,i)=>x.at(-1).R/(2*c.delta.at(-1)/20)-s[i].at(-1).R/(2*c.delta[0]/20)))});}for(const f of Object.keys(c.fields).filter(x=>x!=="equal"))for(const a of c.alpha)for(const t of c.tau)for(const d of c.delta){const l=cells.get([f,a,t,d].join("|")),s=cells.get(["equal",a,t,d].join("|"));fieldEffects.push({field:f,alpha:a,tau:t,delta:d,field_minus_equal_D_gain:stat(l.map((x,i)=>(x.at(-1).D-s[i].at(-1).D)/(2*d/80))),field_minus_equal_R_gain:stat(l.map((x,i)=>(x.at(-1).R-s[i].at(-1).R)/(2*d/20))),field_minus_equal_pair_mass:stat(l.map((x,i)=>x.at(-1).M-s[i].at(-1).M))});}const theory=[];for(const a of c.alpha)for(const t of c.tau){const k=p.local_uniform_stability.find(x=>x.tau===t);if(!k)throw Error("HOLD_KAPPA");theory.push({alpha:a,tau:t,kappa:k.kappa.mean,drift_coefficient:a*k.kappa.mean-1,linear_gain:linear(c,a,k.kappa.mean)});}const expected0=[];for(const [f,theta] of Object.entries(c.fields))for(const a of c.alpha)for(const d of c.delta)expected0.push({field:f,alpha:a,delta:d,checkpoints:deterministic(c,theta,initial(d),a)});return {status:"SYNTHETIC_POPULARITY_PERTURBATION_FIELD_STABILITY",config:c,qa,rows,amplitude,fieldEffects,theory,expected_tau0:expected0,limits:["Synthetic counts and common-shock artificial worlds; no participant or real price calibration.","Finite horizon D and R normalized by their own initial perturbations, not asymptotic phase or empirical threshold.","Uniform local linear recursion uses PR120 kappa only for equal strengths; deterministic tau=0 recursion is expected conditional update along a deterministic path, not stochastic expectation.","Equal initial pair mass across fields, not equal final mass. All field contrasts confound differences in alternative latent strengths by design.","Monte Carlo intervals conditional on fixed scenarios, no joint adjustment or empirical uncertainty; no real-world ability to popularity mapping, no wagering."]};}
const parent=JSON.parse(readFileSync(process.argv[3],"utf8"));const result=run(cfg,parent);
const out=process.argv[2]||"tmp/market-perturbation-field-stability.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");
if(process.argv[4]){const original=JSON.parse(readFileSync(process.argv[4],"utf8"));let max=0,n=0;function same(a,b){if(typeof a==="number"){near(a,b);max=Math.max(max,Math.abs(a-b));n++;}else if(a!==null&&typeof a==="object"){if(!b||JSON.stringify(Object.keys(a))!==JSON.stringify(Object.keys(b)))throw Error("HOLD_KEYS");for(const k of Object.keys(a))same(a[k],b[k]);}else if(a!==b)throw Error("HOLD_VALUE");}same(original,result);console.log(JSON.stringify({status:"SYNTHETIC_PERTURBATION_FULL_REPLAY",max_abs_diff:max,numeric_values:n,rows:result.rows.length,qa:result.qa}));}
