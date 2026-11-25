// Deterministic replay of pinned aggregate receipts; no network or fitting.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const source_commit="801141637c0d86a9caf5709c0fe88a372d63fa70";
const inputs=[
  {
    "path": "docs/evidence/japan-context-within-individual-20261124.json",
    "git_blob_sha": "435bc5135f4745eb16c287debbfadad58c397373"
  },
  {
    "path": "docs/evidence/japan-context-transitional-heterogeneity-20261126.json",
    "git_blob_sha": "bc6cf12589a36a86db46da3d1715b59310a5639f"
  },
  {
    "path": "docs/evidence/information-weight-boundary-heterogeneity-20261125.json",
    "git_blob_sha": "300b719d2147148d2ff04774764770400d8db444"
  }
];
function analyze(a,b,c){
 const tol=1e-10;let checks=0;
 const check=(k,x)=>{if(!x)throw Error("HOLD "+k);checks++};
 const near=(k,x,y)=>check(k,Number.isFinite(x)&&Number.isFinite(y)&&Math.abs(x-y)<=tol);
 const clip=x=>Math.max(0,Math.min(1,x));
 const opt=(A,E)=>{check("positive energy",E>0);const w=clip(A/E);return 2*w*A-w*w*E};
 const sum=(x,k)=>x.groups.reduce((v,g)=>v+g.p*g[k],0);
 function state(groups){const n=groups.reduce((s,g)=>s+g.n,0);check("positive groups",groups.every(g=>g.n>0&&g.E>0));return {n,groups:groups.map(g=>({...g,p:g.n/n,r:g.A/g.E,w:clip(g.A/g.E)}))}}
 const factors=["p","E","r"],arr=x=>Object.fromEntries(factors.map(k=>[k,x.groups.map(g=>g[k])]));
 function value(x){let A=0,E=0,S=0;for(let i=0;i<2;i++){A+=x.p[i]*x.E[i]*x.r[i];E+=x.p[i]*x.E[i];S+=x.p[i]*opt(x.E[i]*x.r[i],x.E[i])}return S-opt(A,E)}
 function shapley(x,y){const X=arr(x),Y=arr(y),v=Array.from({length:8},(_,m)=>value(Object.fromEntries(factors.map((k,i)=>[k,m&(1<<i)?Y[k]:X[k]]))));const phi=factors.map((_,i)=>{let s=0;for(let m=0;m<8;m++)if(!(m&(1<<i))){const j=factors.filter((_,l)=>m&(1<<l)).length;s+=(j===1?1/6:1/3)*(v[m|(1<<i)]-v[m])}return s});const total=v[7]-v[0];near("Shapley closure",phi.reduce((a,b)=>a+b,0),total);return {proportions:phi[0],energy:phi[1],alignment_per_energy:phi[2],total,hybrid_values:v}}
 const rows=[];
 for(const v of c.rows){
   const {seed,year,profile}=v,i=year-2022,prof=profile==="fresh_own_stale_profile"?"fixed":"refreshed";
   const q=b.stdout_aggregate.results[seed].partitions.zero_vs_positive[prof],cohort=a.stdout_aggregate.results[seed].annual[String(year)].common_three_years,m=cohort[profile];
   const [w0,w1]=q.stratified_weights[i],N=cohort.horses,[n0,n1]=q.stratum_support.map(g=>g.horses),A=m.alignment,E=m.correction_energy,S=q.stratified_oracle_gain[i];
   check("identifiable reconstruction",w1>1e-6&&w1<1-1e-6&&Math.abs(w0-w1)>1e-6);near("common counts",n0+n1,N);
   const E1=(S-2*w0*A+w0*w0*E)/(w0-w1)**2,E0=E-E1,A1=w1*E1,A0=A-A1;
   check("positive reconstructed energy",E0>0&&E1>0);
   const common=state([{n:n0,A:A0*N/n0,E:E0*N/n0},{n:n1,A:A1*N/n1,E:E1*N/n1}]);
   const all=state(v.groups.map(g=>({n:g.n,A:g.alignment,E:g.energy})));
   const other=state(all.groups.map((g,j)=>{const h=common.groups[j],n=g.n-h.n;check("positive complement counts",n>0);return {n,A:(g.n*g.A-h.n*h.A)/n,E:(g.n*g.E-h.n*h.E)/n}}));
   near("common alignment",sum(common,"A"),A);near("common energy",sum(common,"E"),E);
   near("common w0",common.groups[0].w,w0);near("common w1",common.groups[1].w,w1);
   near("common separate optimum",common.groups.reduce((t,g)=>t+g.p*opt(g.A,g.E),0),S);
   near("common H",value(arr(common)),q.H[i]);near("annual H",value(arr(all)),v.heterogeneity_gain);
   near("annual A",sum(all,"A"),v.all.alignment);near("annual E",sum(all,"E"),v.all.energy);
   for(let j=0;j<2;j++){const x=common.groups[j],y=other.groups[j],z=all.groups[j];near("complement counts",x.n+y.n,z.n);near("complement A",(x.n*x.A+y.n*y.A)/z.n,z.A);near("complement E",(x.n*x.E+y.n*y.E)/z.n,z.E)}
   rows.push({seed,year,profile:prof,common,all,not_observed_all_three_years:other,H_common:value(arr(common)),H_all:value(arr(all)),decomposition:shapley(common,all)});
 }
 const contrasts=[];
 for(const seed of Object.keys(b.stdout_aggregate.results))for(const profile of ["fixed","refreshed"]){
   const v=rows.filter(x=>x.seed===seed&&x.profile===profile).sort((x,y)=>x.year-y.year);
   check("three years",v.length===3);
   const q=b.stdout_aggregate.results[seed].partitions.zero_vs_positive[profile];
   if(profile==="fixed")for(let i=1;i<3;i++)for(let j=0;j<2;j++)near("fixed common group energy",v[i].common.groups[j].E,v[0].common.groups[j].E);
   for(let i=0;i<2;i++){const u=v[i],w=v[i+1],prior=q.stratified_weights[i],W=q.pooled_weights[i];const gs=w.common.groups.reduce((s,g,j)=>s+g.p*(2*prior[j]*g.A-prior[j]**2*g.E),0),gp=2*W*sum(w.common,"A")-W*W*sum(w.common,"E");const saved=q.earlier_year_weight_transfer_selected_common_cohort[u.year+"_to_"+w.year];near("archived transfer parity stratified",gs,saved.two_stratum_gain);near("archived transfer parity pooled",gp,saved.pooled_gain)}
   const earlier=v[0],later=v[1],delta={};for(const k of ["proportions","energy","alignment_per_energy","total"])delta[k]=later.decomposition[k]-earlier.decomposition[k];
   const annual_change=later.H_all-earlier.H_all,common_change=later.H_common-earlier.H_common;
   near("peak discrepancy",annual_change-common_change,delta.total);near("peak discrepancy components",delta.proportions+delta.energy+delta.alignment_per_energy,delta.total);
   contrasts.push({seed,profile,annual_change,common_change,discrepancy:delta,alignment_share:delta.alignment_per_energy/delta.total});
 }
 return {status:"DESCRIPTIVE_AGGREGATE_RECOVERY_AND_SHAPLEY_NOT_CAUSAL",rows,contrasts,checks,limits:["Original primary common zero-history stratum HOLD (54<100 horses); no new inference or intervals.","Group moments reconstructed from archived pooled moments, bounded weights and stratified optimum; not raw-data reproduction.","Alignment per energy A/E is not a correlation, intrinsic trait, or causal channel.","Six-order average over synthetic moment hybrids is arithmetic allocation of interactions, not actual populations or interventions.","Shared sources/splits; complement means not lifetime exit."]};
}
const src=inputs.map(f=>{const b=fs.readFileSync(path.join(root,f.path));const sha=crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");if(sha!==f.git_blob_sha)throw Error("HOLD source hash "+f.path);return JSON.parse(b);});
const out={source_commit,inputs,...analyze(...src)};
const target=path.join(root,"docs/evidence/information-heterogeneity-membership-mechanics-20261126.json"),data=JSON.stringify(out,null,2)+"\n";
if(process.argv.includes("--check")){if(fs.readFileSync(target,"utf8")!==data)throw Error("HOLD receipt mismatch");}else fs.writeFileSync(target,data);
console.log(JSON.stringify({status:out.status,checks:out.checks,rows:out.rows.length,contrasts:out.contrasts.length}));
