// Create print-size derivatives without changing original data primitives.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const dir=path.join(root,"docs/research/figures/context-information");const inputs=[
  {
    "name": "figure_1_observation_structure.svg",
    "sha": "de7fb9bf7cbef2993a517290678715b4122a62a6"
  },
  {
    "name": "figure_2_longitudinal_substitution.svg",
    "sha": "85941ebaf0933007bbbe5082136b9cb7cde874d1"
  },
  {
    "name": "figure_3_identity_alignment.svg",
    "sha": "71900ddbf9d5a533c9fd3ad432abb68fe4e412f3"
  },
  {
    "name": "figure_4_transfer_and_coverage.svg",
    "sha": "6005d425c0f317af92ae6b6064577481bc3d8466"
  }
];
function transform(s){
 let i=0;
 const labels={
 "2021 source A, primary split; distinct endpoints retain their own denominators.":"Source A (2021); each endpoint has its own denominator.",
 "Points and intervals: conditional pointwise 95% cluster intervals. Not independent replicates or genetic effect estimates.":"Conditional pointwise 95% cluster intervals; not independent replicates or genetic effects.",
 "Solid intervals: observed pointwise sire intervals. Open marks: descriptive arithmetic only; no inferential interval.":"Pointwise sire intervals where shown; other values are descriptive, with no new interval.",
 "Separate estimands and axes. Matched alternative sire is not verified genomic nonkin; supply moderation unsupported.":"Separate estimands; alternative sire is not verified nonkin. Supply moderation unsupported.",
 "Later calibrated gain over no-family baseline is uncertain in 2024–25. All intervals pointwise; open marks descriptive.":"2024–25 gain over no-family is uncertain; intervals pointwise; open marks descriptive.",
 "First valid 2025 record":"Archive-first in 2025",
 "Native horse count; last row is not official debut":"Native horses; archive-first ≠ official debut",
 "History-dependent (N−G)":"History-weighted (N−G)",
 "Full correction (N−F)":"Full (N−F)",
 "Turf–dirt rank residual":"Surface rank residual",
 "Membership remainder":"Membership",
 "4,187 targets supported on both parent channels":"4,187 targets; both parents supported",
 "Annual / first / later outcomes (not interaction tests)":"Different endpoints; no interaction test",
 "True sire minus alternative-sire sign; matched cohorts":"Matched cohorts; same correction magnitude",
 "Refreshed own and donor profiles, earlier-A weights":"Updated profiles; earlier-A weights",
 "Same 194 horses; 81 sires, refreshed season profiles":"194 horses / 81 sires; updated profiles",
 "No forecast or confidence interval for this optimum.":"No forecast or interval for sample optima.",
 "Full correction versus sample-optimal common weight":"Full correction vs. sample optimum"
 };
 return s.replace('width="1280" height="820"','width="180mm" height="115.3125mm"').replace(/<text\b([^>]*)>([^<]*)<\/text>/g,(_,attr,label)=>{
  const a=attr.replace(/font-size="([\d.]+)"/,(_,v)=>`font-size="${Math.max(18,Number(v))}"`).replace("Arial, Helvetica, sans-serif","Liberation Sans, Arial, sans-serif");
  return `<text id="label-${++i}"${a}>${labels[label]||label}</text>`;
 });
}
function audit(s,t,name,sha){const geom=x=>[...x.matchAll(/<(?:line|rect|circle)\b[^>]*\/?>/g)].map(m=>m[0]);if(JSON.stringify(geom(s))!==JSON.stringify(geom(t)))throw Error("HOLD_GEOMETRY");const sizes=x=>[...x.matchAll(/<text\b[^>]*font-size="([\d.]+)"/g)].map(m=>Number(m[1]));const a=sizes(s),b=sizes(t);if(a.length!==b.length||Math.min(...b)*180/1280*72/25.4<7)throw Error("HOLD_FONT");return {name,source_blob:sha,text_count:b.length,old_minimum_pt:Math.min(...a)*180/1280*72/25.4,new_minimum_pt:Math.min(...b)*180/1280*72/25.4,plot_primitives_preserved:geom(s).length};}
const outDir=path.join(dir,"print180");fs.mkdirSync(outDir,{recursive:true});const rows=[];
function write(name,data){const dest=path.join(outDir,name);if(process.argv.includes("--check")){if(fs.readFileSync(dest,"utf8")!==data)throw Error("HOLD DERIVATIVE "+name);}else fs.writeFileSync(dest,data);}
for(const f of inputs){const b=fs.readFileSync(path.join(dir,f.name));const sha=crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");if(sha!==f.sha)throw Error("HOLD SOURCE "+f.name);const s=b.toString("utf8"),t=transform(s);rows.push(audit(s,t,f.name,sha));write(f.name,t);}
write("print_size_audit.json",JSON.stringify({status:"SIZE_AND_PRIMITIVE_PARITY_PASS_VISUAL_QA_PENDING",width_mm:180,figure_count:4,figures:rows},null,2)+"\n");console.log("4 print derivatives verified; rendered geometry audit separate.");
