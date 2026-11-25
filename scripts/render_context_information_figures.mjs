// Rebuild figure SVGs from pinned anonymous receipts; Node.js standard library only.
import fs from "node:fs";
import crypto from "node:crypto";
import path from "node:path";
import {fileURLToPath} from "node:url";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const INPUTS=[
  {
    "id": "parent-context-equalization",
    "path": "docs/evidence/japan-parent-context-equalization-20261124.json",
    "git_blob_sha": "58dfb6f0c2ebf1228addcfeca09883e5e0febd34"
  },
  {
    "id": "sire-first-context-assignment",
    "path": "docs/evidence/japan-sire-first-context-assignment-20261124.json",
    "git_blob_sha": "50e89420fe5cc3b355e7dbe93bddedcf77353af4"
  },
  {
    "id": "sire-context-exposure-transfer",
    "path": "docs/evidence/japan-sire-context-exposure-transfer-20261124.json",
    "git_blob_sha": "4690752d9f2723794ad47d722349fbf37d829b06"
  },
  {
    "id": "sire-context-time-transfer",
    "path": "docs/evidence/japan-sire-context-time-transfer-20261124.json",
    "git_blob_sha": "824b940a08cdf45e7e8e28d1a7c833a212d14b61"
  },
  {
    "id": "context-occupancy-refresh",
    "path": "docs/evidence/japan-context-occupancy-refresh-20261124.json",
    "git_blob_sha": "a699763f6f3ccf3c01e1bcb081d437b178b541cb"
  },
  {
    "id": "context-within-individual",
    "path": "docs/evidence/japan-context-within-individual-20261124.json",
    "git_blob_sha": "435bc5135f4745eb16c287debbfadad58c397373"
  },
  {
    "id": "context-alignment-identity-control",
    "path": "docs/evidence/japan-context-alignment-identity-control-20261124.json",
    "git_blob_sha": "9f5e27e24073a318d07b5cf645ef781bbbbb56ad"
  },
  {
    "id": "context-distance-generalization",
    "path": "docs/evidence/japan-context-distance-generalization-20261124.json",
    "git_blob_sha": "5918ce018c5fb9e3304e0831d552de5096833a87"
  },
  {
    "id": "context-opportunity-diversity",
    "path": "docs/evidence/japan-context-opportunity-diversity-20261124.json",
    "git_blob_sha": "31dee4ae476855f9c23c607b4a7d8c73f68eb415"
  },
  {
    "id": "context-information-substitution",
    "path": "docs/evidence/japan-context-information-substitution-20261124.json",
    "git_blob_sha": "4023a6f85add0336cc81848d8434db9df5a25009"
  },
  {
    "id": "context-seasonal-transfer-2025",
    "path": "docs/evidence/japan-context-seasonal-transfer-2025-20261125.json",
    "git_blob_sha": "6ef4eb8f33a924231e8d602e034f57829538e5e0"
  }
];
function renderFigures(receipts){
 const z=Object.fromEntries(Object.entries(receipts).map(([k,v])=>[k,v.stdout_aggregate])),seed="20261124";
 const parent=z["parent-context-equalization"].results[seed]["2021"].groups.equal_supported;
 const first=z["sire-first-context-assignment"].primary_subgroups;
 const later=z["sire-first-context-assignment"].all_groups[seed].later["2021"];
 const annualA=z["sire-context-exposure-transfer"].results.horse_disjoint[seed].own_history["2021"].all_targets;
 const perf=z["sire-context-time-transfer"].results.horse_disjoint[seed].years["2021"].all_targets;
 const cold=z["context-occupancy-refresh"].results[seed].years["2022"].no_prior_A_eligible;
 const within=z["context-within-individual"].results[seed],pair=within.pairs["2022-2024"].pair_intersection;
 const bands=["1200-1599","1600-1999","2000-2399"],short=["1200–1599","1600–1999","2000–2399"];
 const align=bands.map(k=>z["context-alignment-identity-control"].results[k][seed]);
 const dist=bands.map(k=>z["context-distance-generalization"].results[k].results[seed].pair_intersections["2022-2024"]);
 const opp=z["context-opportunity-diversity"].results[seed].fits.adjusted;
 const ann=z["context-information-substitution"].results[seed].B;
 const season=z["context-seasonal-transfer-2025"].results[seed].years;
 const coverage=z["context-seasonal-transfer-2025"].source_2025_gate;
 const check=[];
 function near(name,actual,expected,tol=0.0000006){if(typeof actual!=="number"||!Number.isFinite(actual)||Math.abs(actual-expected)>tol)throw Error("HOLD numeric parity: "+name+" actual "+actual+" expected "+expected);check.push({name,actual,expected,tolerance:tol})}
 near("A annual n",annualA.horses,7276,0);near("A annual gain",annualA.contrasts.M0_minus_M1.MSE_gain,.014711);
 near("A annual baseline RMSE",annualA.RMSE.M0,.423246);near("A annual family RMSE",annualA.RMSE.M1,.405495);
 near("parent donor sire mean",parent.mean_sire_peers,190.6572725);near("parent donor dam mean",parent.mean_dam_peers,2.0780989);
 near("parent equal support",parent.horses,4187,0);near("parent full gap",parent.contrasts.FD_minus_FS.MSE_gain,.008982);near("parent equal gap",parent.contrasts.ED_minus_ES.MSE_gain,.001258);
 near("parent gap reduction",100*(1-parent.contrasts.ED_minus_ES.MSE_gain/parent.contrasts.FD_minus_FS.MSE_gain),86.0,.05);
 near("first gain",first.all.C_minus_F.MSE_gain,.013751);near("later gain",later.C_minus_F.MSE_gain,.002085);
 near("paired response gain",perf.contrasts.M0_minus_M1.MSE_gain,.000806);near("cold B2022 gain",cold.contrasts.B00_minus_M00.MSE_gain,.019780);
 near("common horses",pair.common_horses,599,0);near("common early",pair.common_early_gain,.011712);near("common late",pair.common_late_gain,-.015866);
 near("own update",pair.own_information_update_shift.MSE_gain,-.016106);near("outcome shift",pair.observed_occupancy_shift.MSE_gain,-.011472);
 near("membership",pair.membership_remainder,.010497);near("full change",pair.full_population_gain_change,-.017081);
 near("decomposition exact closure",pair.own_information_update_shift.MSE_gain+pair.observed_occupancy_shift.MSE_gain+pair.membership_remainder,pair.full_population_gain_change,1e-12);
 near("within common exact closure",pair.common_late_gain-pair.common_early_gain,pair.within_common_total.MSE_gain,1e-12);
 near("primary alignment",align[1].alignment_true_minus_equal_magnitude_swap.MSE_gain,.012457);near("primary matched n",align[1].matched_nonzero_horses,565,0);
 align.forEach((a,i)=>near("matched magnitude "+bands[i],a.true.correction_rms,a.equal_magnitude_swap.correction_rms,1e-12));
 near("short own update",dist[0].own_information_update_shift.MSE_gain,-.015038);near("long own update",dist[2].own_information_update_shift.MSE_gain,-.001588);
 near("opportunity adjusted",opp.beta_per_0_1,.000441);
 near("annual 2024 gated",ann["2024"].refreshed.contrasts.N_minus_G.MSE_gain,.002282);
 near("annual 2024 full",ann["2024"].refreshed.contrasts.N_minus_F.MSE_gain,-.009304);
 near("season 2025 gated",season["2025"].refreshed.season_calibrated.contrasts.N_minus_G.MSE_gain,.000427);
 near("season 2025 full vs gate",season["2025"].refreshed.season_calibrated.contrasts.F_minus_G.MSE_gain,.010336);
 near("strict horses",coverage.strict_exact.native_horses,2839,0);near("anchored horses",coverage.anchored.native_horses,194,0);near("archive-first horses",coverage.strict_exact.first_valid_B_record_in_2025_horses,664,0);
 near("coverage count closure",coverage.anchored.native_horses+coverage.unanchored_strict.native_horses,coverage.strict_exact.native_horses,0);
 const out={};const ink="#17222d",muted="#596875",blue="#285e84",teal="#177d72",rust="#a45139",gray="#9daab4",grid="#dce3e8";
 const esc=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
 const n=x=>Number(x).toFixed(3).replace(/\.?0+$/,"")||"0";
 const text=(x,y,t,o={})=>`<text x="${x}" y="${y}" font-family="Arial, Helvetica, sans-serif" font-size="${o.size||16}" fill="${o.color||ink}" font-weight="${o.bold?700:400}" text-anchor="${o.anchor||"start"}">${esc(t)}</text>`;
 const ln=(x1,y1,x2,y2,col=ink,w=1,dash="")=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${col}" stroke-width="${w}"${dash?` stroke-dasharray="${dash}"`:""}/>`;
 const rect=(x,y,w,h,color,stroke="none")=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${color}" stroke="${stroke}"/>`;
 const dot=(x,y,color=blue,open=false,shape="circle")=>shape==="square"?`<rect x="${x-5}" y="${y-5}" width="10" height="10" fill="${open?"white":color}" stroke="${color}" stroke-width="2"/>`:`<circle cx="${x}" cy="${y}" r="5.5" fill="${open?"white":color}" stroke="${color}" stroke-width="2"/>`;
 const group=(x,y,letter,title,sub,body)=>`<g transform="translate(${x} ${y})">${text(0,18,letter,{size:21,bold:true})}${text(28,18,title,{size:19,bold:true})}${text(28,41,sub,{size:14,color:muted})}${body}</g>`;
 function forest(rows,{min,max,ticks,axis,scale=1,margin=204,w=575,h=300}){
   const x=v=>margin+(v*scale-min)/(max-min)*(w-margin-18), y0=68,step=Math.min(49,(h-112)/rows.length),bottom=y0+step*rows.length;
   let a=ticks.map(t=>ln(x(t/scale),y0-13,x(t/scale),bottom,grid)+text(x(t/scale),bottom+19,n(t),{size:14,anchor:"middle",color:muted})).join("");
   if(min<=0&&max>=0)a+=ln(x(0),y0-13,x(0),bottom,muted,1.3,"4 4");
   rows.forEach((r,i)=>{const y=y0+step*(i+.5),col=r.color||blue;
     a+=text(0,y+5,r.label,{size:15});
     if(r.ci){a+=ln(x(r.ci[0]),y,x(r.ci[1]),y,col,2)+ln(x(r.ci[0]),y-4,x(r.ci[0]),y+4,col,1.6)+ln(x(r.ci[1]),y-4,x(r.ci[1]),y+4,col,1.6)}
     a+=dot(x(r.v),y,col,!r.ci,r.shape||"circle");
   });
   return a+ln(margin,bottom,w-18,bottom,ink)+text((margin+w-18)/2,bottom+41,axis,{size:15,anchor:"middle"});
 }
 function series(rows,{min,max,ticks,axis,labels,scale=1,w=575,h=300,legend=true}){
   const L=66,R=w-38,T=63,B=h-64, X=i=>L+(R-L)*(i+.5)/labels.length,Y=v=>B-(v*scale-min)/(max-min)*(B-T);
   let a=ticks.map(t=>ln(L,Y(t/scale),R,Y(t/scale),grid)+text(L-9,Y(t/scale)+5,n(t),{anchor:"end",size:14,color:muted})).join("");
   if(min<=0&&max>=0)a+=ln(L,Y(0),R,Y(0),muted,1.2,"4 4");
   labels.forEach((t,i)=>a+=text(X(i),B+21,t,{anchor:"middle",size:15}));
   a+=ln(L,T,L,B,ink)+ln(L,B,R,B,ink);
   a+=`<g transform="translate(16 ${(T+B)/2}) rotate(-90)">${text(0,0,axis,{anchor:"middle",size:15})}</g>`;
   rows.forEach((r,k)=>{const c=r.color||blue;const xx=i=>X(i)+(rows.length>1?(k-(rows.length-1)/2)*12:0);
     if(r.line)a+=r.values.slice(1).map((v,i)=>ln(xx(i),Y(r.values[i].v),xx(i+1),Y(v.v),c,2,r.dash||"")).join("");
     r.values.forEach((v,i)=>{const y=Y(v.v),x=xx(i);if(v.ci)a+=ln(x,Y(v.ci[0]),x,Y(v.ci[1]),c,2)+ln(x-4,Y(v.ci[0]),x+4,Y(v.ci[0]),c)+ln(x-4,Y(v.ci[1]),x+4,Y(v.ci[1]),c);a+=dot(x,y,c,!v.ci&&!!r.open,r.shape||"circle")});
     if(legend){const x=L+k*235,y=B+47;a+=dot(x,y-4,c,!!r.open,r.shape||"circle")+text(x+12,y,r.name,{size:14});}
   });
   return a;
 }
 function bars(rows,{max,w=575,h=300,axis="Count",margin=178,log=false}){
   const x=v=>margin+(log?Math.log10(v)/Math.log10(max):v/max)*(w-margin-90),base=margin;
   let a=ln(base,65,base,h-48,ink);
   rows.forEach((r,i)=>{const y=74+i*Math.min(58,(h-125)/rows.length),val=r.v; a+=text(0,y+17,r.label,{size:15})+rect(base,y,Math.max(0,x(val)-base),24,r.color||blue)+text(x(val)+8,y+17,r.display||n(val),{size:15,bold:true});});
   return a+text(margin,h-29,axis,{size:14,color:muted});
 }
 const gain=(label,x,color=blue)=>({label,v:x.MSE_gain,ci:x.CI95_pointwise||x.whole_sire_bootstrap_pointwise_CI95,color});
 const sGain=x=>({v:x.MSE_gain,ci:x.CI95_pointwise});
 function fig(num,title,subtitle,panels,foot){return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="820" viewBox="0 0 1280 820" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><rect width="1280" height="820" fill="white"/>${text(42,36,"FIGURE "+num,{size:15,bold:true,color:muted})}${text(42,68,title,{size:27,bold:true})}${text(42,94,subtitle,{size:16,color:muted})}${panels.join("")}${ln(42,775,1238,775,grid)}${text(42,798,foot,{size:14,color:muted})}</svg>\n`}
 const coords=[[42,119],[665,119],[42,444],[665,444]];
 const groupAt=(i,...args)=>group(...coords[i],...args);
 const pc=parent.contrasts;
 const parentRows=[["Full: sire resample",pc.FD_minus_FS,"sire"],["Full: dam resample",pc.FD_minus_FS,"dam"],["Equal: sire resample",pc.ED_minus_ES,"sire"],["Equal: dam resample",pc.ED_minus_ES,"dam"]].map(([label,q,k],i)=>({label,v:q.MSE_gain,ci:q[k].CI95_pointwise,color:i<2?rust:teal,shape:k==="dam"?"square":"circle"}));
 out["figure_1_observation_structure.svg"]=fig(1,"Observation structure and early allocation","2021 source A, primary split; distinct endpoints retain their own denominators.",[
 groupAt(0,"a","Historical donor counts","4,187 targets supported on both parent channels",bars([{label:"Paternal",v:parent.mean_sire_peers,display:parent.mean_sire_peers.toFixed(1),color:blue},{label:"Maternal",v:parent.mean_dam_peers,display:parent.mean_dam_peers.toFixed(2),color:teal},{label:"Equalized per side",v:parent.mean_equal_peers,display:parent.mean_equal_peers.toFixed(2),color:gray}],{max:250,axis:"Log10 donor count (origin = 1)",log:true})),
 groupAt(1,"b","Paternal minus maternal gain","Same targets; separate sire / dam resampling",forest(parentRows,{min:-4,max:16,ticks:[-4,0,4,8,12,16],axis:"MSE difference × 1,000",scale:1000,margin:202})),
 groupAt(2,"c","Allocation prediction","Annual / first / later outcomes (not interaction tests)",forest([gain("Annual (n=7,276)",annualA.contrasts.M0_minus_M1),gain("First (n=7,276)",first.all.C_minus_F),gain("Later (n=4,477)",later.C_minus_F)],{min:-5,max:25,ticks:[-5,0,5,10,15,20,25],axis:"MSE gain × 1,000",scale:1000,margin:175})),
 groupAt(3,"d","Paired rank response","Different response and support; n = 985",forest([gain("Turf–dirt rank residual",perf.contrasts.M0_minus_M1,rust)],{min:-3,max:4,ticks:[-3,-2,-1,0,1,2,3,4],axis:"MSE gain × 1,000",scale:1000,margin:205}))
 ],"Points and intervals: conditional pointwise 95% cluster intervals. Not independent replicates or genetic effect estimates.");
 const years=["2022","2023","2024"],mom=years.map(y=>within.annual[y].common_three_years.fresh_own_stale_profile);
 const weights=mom.map(q=>Math.max(0,Math.min(1,q.alignment/q.correction_energy))),opt=mom.map((q,i)=>2*weights[i]*q.alignment-weights[i]**2*q.correction_energy);
 near("scalar optimum primary 2022",opt[0],.014298);near("scalar optimum primary 2024",opt[2],.001240);
 out["figure_2_longitudinal_substitution.svg"]=fig(2,"Individual history and sample membership","Fixed source-A family correction; primary seed. Positive gain = lower squared error.",[
 groupAt(0,"a","Within the same 527 horses","Full correction versus sample-optimal common weight",series([{name:"Full correction",color:rust,line:true,values:mom.map(q=>({v:q.gain}))},{name:"Sample optimum*",color:teal,line:true,open:true,shape:"square",values:opt.map(v=>({v}))}],{min:-20,max:20,ticks:[-20,-10,0,10,20],axis:"MSE gain × 1,000",labels:years,scale:1000})),
 groupAt(1,"b","2022–2024 change: 599 common horses","Arithmetic components and membership remainder",forest([gain("Own-history update",pair.own_information_update_shift,rust),gain("Allocation shift",pair.observed_occupancy_shift,rust),gain("Within-horse total",pair.within_common_total,blue),{label:"Membership remainder",v:pair.membership_remainder,color:teal,shape:"square"},{label:"Full cohort change",v:pair.full_population_gain_change,color:blue,shape:"square"}],{min:-45,max:15,ticks:[-45,-30,-15,0,15],axis:"Change in MSE gain × 1,000",scale:1000,margin:205})),
 groupAt(2,"c","Sample-optimal scalar weight*","Same 527 horses; fixed correction magnitude",series([{name:"Post-hoc optimum",color:teal,line:true,open:true,values:weights.map(v=>({v}))}],{min:0,max:1,ticks:[0,.25,.5,.75,1],axis:"Common weight",labels:years})),
 groupAt(3,"d","Interpretation","The within-horse and full-cohort changes are distinct.",text(0,87,"58.4%",{size:40,bold:true,color:rust})+text(0,112,"of within-horse decline: own-history update",{size:16})+text(0,165,"38.1%",{size:40,bold:true,color:teal})+text(0,190,"of within-horse decline offset by membership",{size:16})+text(0,235,"*Sample optimum uses evaluated outcomes.",{size:15,color:muted})+text(0,257,"No forecast or confidence interval for this optimum.",{size:15,color:muted}))
 ],"Solid intervals: observed pointwise sire intervals. Open marks: descriptive arithmetic only; no inferential interval.");
 out["figure_3_identity_alignment.svg"]=fig(3,"Recorded-sire correspondence and context boundaries","Primary split; bands share horses and are not independent replications.",[
 groupAt(0,"a","Magnitude-matched direction contrast","True sire minus alternative-sire sign; matched cohorts",forest(align.map((a,i)=>gain(short[i]+" (n="+a.matched_nonzero_horses+")",a.alignment_true_minus_equal_magnitude_swap,teal)),{min:-5,max:25,ticks:[-5,0,5,10,15,20,25],axis:"2 mean[(d − e)u] × 1,000",scale:1000,margin:194})),
 groupAt(1,"b","Directional alignment","Same correction RMS within each matched band",series([{name:"Recorded sire",color:blue,values:align.map(a=>({v:a.true.cosine}))},{name:"Alternative sire sign",color:rust,shape:"square",values:align.map(a=>({v:a.equal_magnitude_swap.cosine}))}],{min:-.1,max:.4,ticks:[-.1,0,.1,.2,.3,.4],axis:"Cosine (descriptive)",labels:["Short","Middle","Long"]})),
 groupAt(2,"c","Own-history update by band","2022–2024 common horses, fixed correction",forest(dist.map((a,i)=>gain(short[i]+" (n="+a.common_horses+")",a.own_information_update_shift,rust)),{min:-30,max:10,ticks:[-30,-20,-10,0,10],axis:"Change in MSE gain × 1,000",scale:1000,margin:194})),
 groupAt(3,"d","Historical opportunity proxy","Adjusted slope; 1,389 horse × band rows",forest([{label:"Supply balance (+0.1)",v:opp.beta_per_0_1,ci:opp.CI95_pointwise,color:gray}],{min:-2,max:3,ticks:[-2,-1,0,1,2,3],axis:"Slope × 1,000",scale:1000,margin:204}))
 ],"Separate estimands and axes. Matched alternative sire is not verified genomic nonkin; supply moderation unsupported.");
 const ar=years.map(y=>ann[y].refreshed.contrasts),ys=["2022","2023","2024","2025"],sr=ys.map(y=>season[y].refreshed.season_calibrated);
 const late=sr[3];
 out["figure_4_transfer_and_coverage.svg"]=fig(4,"Later transfer and the identity coverage limit","Primary split; yearly target cohorts differ. Positive MSE gain favors the added correction.",[
 groupAt(0,"a","Annual transfer","Refreshed own and donor profiles, earlier-A weights",series([{name:"Full correction (N−F)",color:rust,shape:"square",values:ar.map(q=>sGain(q.N_minus_F))},{name:"History-dependent (N−G)",color:teal,values:ar.map(q=>sGain(q.N_minus_G))}],{min:-20,max:20,ticks:[-20,-10,0,10,20],axis:"MSE gain × 1,000",labels:years,scale:1000})),
 groupAt(1,"b","Same-season transfer","Jan 1–Mar 27, seasonal calibration from A only",series([{name:"Full correction (N−F)",color:rust,shape:"square",values:sr.map(q=>sGain(q.contrasts.N_minus_F))},{name:"History-dependent (N−G)",color:teal,values:sr.map(q=>sGain(q.contrasts.N_minus_G))}],{min:-25,max:20,ticks:[-25,-15,-5,0,10,20],axis:"MSE gain × 1,000",labels:ys,scale:1000})),
 groupAt(2,"c","2025 strict native cohort","2,839 horses / 280 complete classified races",bars([{label:"Strict native horses",v:coverage.strict_exact.native_horses,display:"2,839",color:gray},{label:"Old parent anchors",v:coverage.anchored.native_horses,display:"194 (6.8%)",color:blue},{label:"First valid 2025 record",v:coverage.strict_exact.first_valid_B_record_in_2025_horses,display:"664 (0 linked)",color:rust}],{max:3200,axis:"Native horse count; last row is not official debut",margin:183})),
 groupAt(3,"d","2025 model comparison","Same 194 horses; 81 sires, refreshed season profiles",forest(["N","F","P","H","G"].map(k=>({label:({N:"N: no family",F:"F: full",P:"P: common weight",H:"H: zero-history only",G:"G: history-dependent"})[k],v:late.RMSE[k],color:k==="G"?teal:k==="F"?rust:blue,shape:"square"})),{min:.30,max:.35,ticks:[.30,.31,.32,.33,.34,.35],axis:"RMSE (lower is better)",margin:194}))
 ],"Later calibrated gain over no-family baseline is uncertain in 2024–25. All intervals pointwise; open marks descriptive.");
 return {out,audit:{status:"MANUSCRIPT_SELECTED_NUMERIC_PARITY_AND_FIGURE_DATA",primary_seed:Number(seed),checks:check,checks_passed:check.length,scope:"Selected manuscript claims and plotted data only; archived aggregate receipts, not independent raw-data or ZIP reproduction."}};
}
const receipts={};
for(const f of INPUTS){const b=fs.readFileSync(path.join(ROOT,f.path));const sha=crypto.createHash("sha1").update(Buffer.from("blob "+b.length+"\0")).update(b).digest("hex");if(f.git_blob_sha&&sha!==f.git_blob_sha)throw Error("HOLD receipt blob drift "+f.path);receipts[f.id]=JSON.parse(b);}
const result=renderFigures(receipts);const dir=path.join(ROOT,"docs/research/figures/context-information");fs.mkdirSync(dir,{recursive:true});const outputs={...result.out,"numeric_parity.json":JSON.stringify(result.audit,null,2)+"\n"};
for(const [name,content] of Object.entries(outputs)){const dest=path.join(dir,name);if(process.argv.includes("--check")){if(fs.readFileSync(dest,"utf8")!==content)throw Error("HOLD figure drift: "+name);}else fs.writeFileSync(dest,content);}
console.log(JSON.stringify({status:"FIGURES_MATCH_PINNED_RECEIPTS",figures:Object.keys(result.out).length,checks:result.audit.checks_passed}));
