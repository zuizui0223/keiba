// Replay only archived anonymous moments; no source download or empirical fit.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const source_commit="f84f8b3c0c320b88cc7a6968a520f8335081bb4b";
const inputs=[
  {
    "path": "docs/evidence/japan-context-within-individual-20261124.json",
    "git_blob_sha": "435bc5135f4745eb16c287debbfadad58c397373"
  },
  {
    "path": "docs/evidence/japan-context-information-substitution-20261124.json",
    "git_blob_sha": "4023a6f85add0336cc81848d8434db9df5a25009"
  }
];
function analyze(z,g){
 const tol=1e-12, rows=[], checks=[];
 const assert=(label,a,b)=>{if(!Number.isFinite(a)||!Number.isFinite(b)||Math.abs(a-b)>tol)throw Error("HOLD "+label+" "+a+" "+b);checks.push(label)};
 function moments(q){
   const A=q.alignment,E=q.correction_energy;
   if(!(Number.isFinite(A)&&Number.isFinite(E)&&E>0))throw Error("HOLD moments");
   const raw=A/E,w=Math.max(0,Math.min(1,raw)),opt=2*w*A-w*w*E,unbounded=A*A/E;
   assert("full_gain",q.gain,2*A-E);assert("archived_optimal_weight",q.descriptive_oracle_weight_0_1,w);
   return {alignment:A,energy:E,unconstrained_weight:raw,bounded_weight:w,positive_gain_boundary:A>0?2*A/E:null,full_gain:q.gain,optimum_gain:opt,unbounded_optimum:unbounded,clipping_penalty:E*(w-raw)**2,full_weight_regret:opt-q.gain};
 }
 for(const [seed,v] of Object.entries(z.results))for(const y of ["2022","2023","2024"])for(const profile of ["fresh_own_stale_profile","fresh_own_fresh_profile"]){
   const q=v.annual[y],all=moments(q.all[profile]),n=q.all.horses;
   const groups=["no_prior_A","prior_A"].map(k=>({group:k,n:q[k].horses,p:q[k].horses/n,...moments(q[k][profile])}));
   const sum=key=>groups.reduce((a,x)=>a+x.p*x[key],0);
   assert("partition_count",groups.reduce((a,x)=>a+x.n,0),n);
   assert("partition_alignment",sum("alignment"),all.alignment);
   assert("partition_energy",sum("energy"),all.energy);
   assert("partition_full_gain",sum("full_gain"),all.full_gain);
   const strat=sum("optimum_gain"),heterogeneity=strat-all.optimum_gain;
   const weighted_variance=groups.reduce((a,x)=>a+x.p*x.energy*(x.unconstrained_weight-all.unconstrained_weight)**2,0);
   const clipping_cost_delta=sum("clipping_penalty")-all.clipping_penalty;
   assert("bounded_variance_identity",heterogeneity,weighted_variance-clipping_cost_delta);
   if(heterogeneity< -tol)throw Error("HOLD negative heterogeneity");
   let gate=null;
   if(profile==="fresh_own_fresh_profile"){
     const k=g.results[seed].B[y].refreshed.contrasts;assert("full_refreshed_PR87_parity",all.full_gain,k.N_minus_F.MSE_gain);
     gate={gain:k.N_minus_G.MSE_gain,ci:k.N_minus_G.CI95_pointwise,gain_minus_two_stratum_oracle:k.N_minus_G.MSE_gain-strat};
   }
   rows.push({seed,year:Number(y),profile,horses:n,all,groups,stratified_oracle_gain:strat,heterogeneity_gain:heterogeneity,unbounded_weight_variance_component:weighted_variance,extra_clipping_penalty:clipping_cost_delta,earlier_A_count_gate:gate});
 }
 const patterns=[];
 for(const seed of Object.keys(z.results))for(const profile of ["fresh_own_stale_profile","fresh_own_fresh_profile"]){
   const a=rows.filter(q=>q.seed===seed&&q.profile===profile);
   patterns.push({seed,profile,intermediate_peak:a[1].heterogeneity_gain>a[0].heterogeneity_gain&&a[1].heterogeneity_gain>a[2].heterogeneity_gain,threshold_crossing:a[0].all.positive_gain_boundary>1&&a[1].all.positive_gain_boundary<1&&a[2].all.positive_gain_boundary<1,late_heterogeneity_reduction:1-a[2].heterogeneity_gain/a[1].heterogeneity_gain});
 }
 return {status:"DESCRIPTIVE_AGGREGATE_OUTCOME_DEPENDENT_SCALAR_ORACLES",rows,patterns,arithmetic_checks:checks.length,limitations:["Weights and positive-gain boundaries use evaluation outcomes, not forecasting parameters.","Two groups defined by pre-2022 eligible source-A history, not contemporary no-history or debut status.","Annual cohorts change, no time-moderator or biological inference; splits overlap.","No new sampling intervals for oracles, thresholds or heterogeneity. Earlier-A fitted gate is distinct and retains original pointwise intervals.","2022 stale and refreshed profiles are identical, not independent conditions."]};
}
const src=inputs.map(f=>{const b=fs.readFileSync(path.join(root,f.path));const sha=crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");if(sha!==f.git_blob_sha)throw Error("HOLD source hash "+f.path);return JSON.parse(b).stdout_aggregate;});
const out={source_commit,inputs,...analyze(...src)};
const target=path.join(root,"docs/evidence/information-weight-boundary-heterogeneity-20261125.json");
const contents=JSON.stringify(out,null,2)+"\n";
if(process.argv.includes("--check")){if(fs.readFileSync(target,"utf8")!==contents)throw Error("HOLD receipt mismatch");}else fs.writeFileSync(target,contents);
console.log(JSON.stringify({status:out.status,checks:out.arithmetic_checks,rows:out.rows.length,patterns:out.patterns}));
