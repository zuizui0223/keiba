// Synthetic popularity dynamics, research only. Node >= 18.
import {writeFileSync,mkdirSync} from 'node:fs';
import {dirname} from 'node:path';
const cfg={
  "seed": 20261127,
  "reps": 256,
  "horses": 8,
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
  "beta": 2,
  "feedback": [
    -0.5,
    0,
    0.5,
    1,
    1.25,
    1.5
  ],
  "sigma": [
    0.25,
    1,
    3
  ],
  "evidence": [
    "posterior",
    "raw"
  ],
  "primaryFeedback": [
    0.5,
    1,
    1.5
  ]
};
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)|0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return(((t^(t>>>14))>>>0)+.5)/4294967296;};}

function shocks(c,r){const next=rng((c.seed+Math.imul(r+1,0x9E3779B9))>>>0),n=c.batches*c.batch*c.horses,z=new Float64Array(n),g=new Float64Array(n);for(let i=0;i<n;i+=2){let u=next(),v=next(),m=Math.sqrt(-2*Math.log(u));z[i]=m*Math.cos(2*Math.PI*v);if(i+1<n)z[i+1]=m*Math.sin(2*Math.PI*v);}for(let i=0;i<n;i++)g[i]=-Math.log(-Math.log(next()));return {z,g};}

function avg(a){return a.reduce((x,y)=>x+y,0)/a.length;}

function stat(a){const m=avg(a),sd=Math.sqrt(a.reduce((x,y)=>x+(y-m)**2,0)/(a.length-1));return {mean:m,mc95:[m-1.96*sd/Math.sqrt(a.length),m+1.96*sd/Math.sqrt(a.length)],sd};}

function softmax(a){const m=Math.max(...a),w=a.map(x=>Math.exp(x-m)),s=w.reduce((x,y)=>x+y,0);return w.map(x=>x/s);}

function simulate(c,sh,alpha,sigma,mode,delta=0,swap=true){const n=c.horses,theta=c.theta.slice();theta[0]+=delta/2;theta[1]-=delta/2;let a=c.initial.slice(),b=c.initial.slice();if(swap)[b[0],b[1]]=[b[1],b[0]];const initialTotal=a.reduce((x,y)=>x+y,0),mass=initialTotal+c.batches*c.batch,scale=mode==="posterior"?1/(1+sigma*sigma):1;let tv=0;for(let t=0;t<c.batches;t++){const sa=a.map(x=>alpha*Math.log(x)),sb=b.map(x=>alpha*Math.log(x));for(let j=0;j<c.batch;j++){let ia=-1,ib=-1,ma=-Infinity,mb=-Infinity,off=(t*c.batch+j)*n;for(let i=0;i<n;i++){const v=c.beta*scale*(theta[i]+sigma*sh.z[off+i])+sh.g[off+i],va=v+sa[i],vb=v+sb[i];if(va>ma){ma=va;ia=i;}if(vb>mb){mb=vb;ib=i;}}a[ia]++;b[ib]++;}if(t===c.batches-1)tv=a.reduce((v,x,i)=>v+Math.abs(x-b[i]),0)/(2*mass);}
if(a.reduce((x,y)=>x+y,0)!==mass||b.reduce((x,y)=>x+y,0)!==mass||a.some(x=>x<=0)||b.some(x=>x<=0))throw Error("MASS");const d=((a[0]-a[1])-(b[0]-b[1]))/(2*mass),q=softmax(theta.map(x=>c.beta*x));const err=x=>x.reduce((v,y,i)=>v+(y/mass-q[i])**2,0);return {d,tv,initialFavA:(a[0]>a[1]?1:a[0]===a[1]?.5:0),initialFavB:(b[1]>b[0]?1:b[1]===b[0]?.5:0),aWinsReversed:(b[0]>b[1]?1:b[0]===b[1]?.5:0),distanceToLatent:(err(a)+err(b))/2};}

function checks(c){const sh=shocks(c,0),mass=c.initial.reduce((x,y)=>x+y,0)+c.batches*c.batch,d=(c.initial[0]-c.initial[1])/mass;for(const mode of c.evidence)for(const sigma of c.sigma){const a=simulate(c,sh,0,sigma,mode);if(Math.abs(a.d-d)>1e-12||Math.abs(a.tv-d)>1e-12)throw Error("NO_FEEDBACK");const b=simulate(c,sh,1.5,sigma,mode,0,false);if(b.d!==0||b.tv!==0)throw Error("NO_INTERVENTION");const x=simulate(c,sh,1.25,sigma,mode),y=simulate(c,shocks(c,0),1.25,sigma,mode);if(JSON.stringify(x)!==JSON.stringify(y))throw Error("REPRO");}return {mass:true,no_feedback_mechanical_retention:true,identical_world:true,reproducible:true};}

function run(c){const qa=checks(c),cells=[],samples=new Map(),unequal=[];for(const mode of c.evidence)for(const a of c.feedback)for(const s of c.sigma)samples.set([mode,a,s].join("|"),[]);const gap=.3,other=new Map();for(const a of c.primaryFeedback)for(const s of c.sigma)other.set([a,s].join("|"),[]);for(let r=0;r<c.reps;r++){const sh=shocks(c,r);for(const mode of c.evidence)for(const a of c.feedback)for(const s of c.sigma)samples.get([mode,a,s].join("|")).push(simulate(c,sh,a,s,mode));for(const a of c.primaryFeedback)for(const s of c.sigma)other.get([a,s].join("|")).push(simulate(c,sh,a,s,"posterior",gap));}const mass=c.initial.reduce((x,y)=>x+y,0)+c.batches*c.batch,mechanical=(c.initial[0]-c.initial[1])/mass;for(const mode of c.evidence)for(const a of c.feedback)for(const s of c.sigma){const x=samples.get([mode,a,s].join("|"));cells.push({mode,alpha:a,sigma:s,terminal_intervention:stat(x.map(v=>v.d)),excess_over_mechanical:stat(x.map(v=>v.d-mechanical)),tv:stat(x.map(v=>v.tv)),initial_favorite_retention:stat(x.map(v=>(v.initialFavA+v.initialFavB)/2)),distance_to_latent:stat(x.map(v=>v.distanceToLatent))});}const moderation=[];for(const mode of c.evidence)for(const a of c.feedback){const low=samples.get([mode,a,c.sigma.at(-1)].join("|")),high=samples.get([mode,a,c.sigma[0]].join("|"));moderation.push({mode,alpha:a,low_minus_high_precision:stat(low.map((v,i)=>v.d-high[i].d))});}for(const a of c.primaryFeedback)for(const s of c.sigma){const x=other.get([a,s].join("|"));unequal.push({alpha:a,sigma:s,latent_log_ability_gap:gap,better_individual_recovers_rank:stat(x.map(v=>v.aWinsReversed)),terminal_intervention:stat(x.map(v=>v.d))});}return {status:"SYNTHETIC_POPULARITY_COUNTERFACTUAL",config:c,qa,mechanical_retention:mechanical,initial_intervention:(c.initial[0]-c.initial[1])/c.initial.reduce((x,y)=>x+y,0),cells,moderation,unequal,limits:["Synthetic latent abilities and equal-size count increments, not actual horse prices, votes or calibrated market model.","Feedback alpha is net response to aggregate popularity; separate imitation and price response not identified.","Private signal precision changes posterior mean and heterogeneity through stated normal-prior model. Raw-signal sensitivity is not a normative belief model.","Paired common shocks across worlds, precision levels and alpha grid; MC intervals describe simulation sampling only.","No validated link from observed horse history to sigma; no real individual ID joins, causal social inference, or wagering recommendations."]};}
const result=run(cfg);
const out=process.argv[2]||"tmp/market-popularity-counterfactual.json";mkdirSync(dirname(out),{recursive:true});writeFileSync(out,JSON.stringify(result,null,2)+"\n");console.log(JSON.stringify(result));
