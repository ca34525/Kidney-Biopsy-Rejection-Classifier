import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';

// Run from the repository root. Runtime paths are supplied by the build command.
const root = process.cwd();
const build = path.join(root, 'build/presentation');
const out = path.join(root, 'presentation');
const skill = process.env.PRESENTATION_SKILL_DIR;
if (!skill || !process.env.RUNTIME_PYTHON) throw new Error('Set PRESENTATION_SKILL_DIR and RUNTIME_PYTHON');
const require = createRequire(path.join(build, 'runtime.mjs'));
const { Presentation, PresentationFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const FONT = resolvePresentationFont({ fontFamily: 'Arial' });
const C = { ink:'#16343E', teal:'#007C78', orange:'#B55730', muted:'#52656B', bg:'#F7F8F5', light:'#E4EFEB', rule:'#CEDBD7', white:'#FFFFFF' };
const p = Presentation.create({slideSize:{width:1280,height:720}});
const nativeTables=[], nativeCharts=[];
const sources=[];
const csv = async file => {
  const lines=(await fs.readFile(path.join(root,file),'utf8')).trim().split(/\r?\n/);
  const headers=lines.shift().split(',');
  return lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[headers[i],v])));
};
const metrics=await csv('results/analysis/20260915_baseline/model_metrics.csv');
const cat=metrics.find(x=>x.model==='catboost_all_depth4');
const log=metrics.find(x=>x.model==='logistic_all');
const ifng=metrics.find(x=>x.model==='single_gene_IFNG');
const constant=metrics.find(x=>x.model==='training_prevalence');
const bins=(await csv('results/analysis/20260915_baseline/reliability_bins.csv')).filter(x=>x.model===cat.model);
const analysis='Source: frozen primary analysis, 15 Sep 2026. Same 345 author technical-validation specimens.';
function text(s, value, x, y, w, h, size=34, color=C.ink, bold=false, align='left') {
  if (typeof color === 'boolean') { bold=color; color=C.ink; }
  const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=value;
  sh.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,autoFit:'none',verticalAlignment:'middle',wrap:true};
  return sh;
}
function line(s,x,y,w,color=C.rule){s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:0},line:{fill:color,width:1.2}});}
function slide(title,source='',dark=false){
  const s=p.slides.add(); const i=p.slides.items?.length || sources.length+1;
  s.background.fill=dark?C.ink:C.bg;
  if(title)text(s,title,64,43,1152,105,46,dark?C.white:C.ink,true);
  if(source)text(s,source,64,657,1090,38,15,dark?'#D6E8E5':C.muted);
  text(s,String(i).padStart(2,'0'),1167,662,48,30,18,dark?'#D6E8E5':C.muted,false,'right');
  sources.push({slide:i,title,source}); return s;
}
function table(s,values,{x=64,y=180,w=1152,h=360,widths,size=30}={}){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,...(widths?{columnWidths:widths}:{})});
  t.borders.assign({fill:C.rule,width:1,style:'solid'});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2===0?'#EDF3F0':C.white);
    cell.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0,autoFit:'none'};
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:18,right:15,top:12,bottom:10},anchor:'center'});
  nativeTables.push(sources.length);return t;
}
function node(s,label,x,y,w,h,{fill=C.light,size=32,color=C.ink}={}){
  const n=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.rule,width:1}});
  n.text=label;n.text.style={typeface:FONT,fontSize:size,color,alignment:'center',verticalAlignment:'middle',autoFit:'none'};return n;
}
function connect(s,a,b,from='right',to='left'){
  s.shapes.connect(a,b,{kind:'elbow',fromSide:from,toSide:to,line:{fill:C.muted,width:2.5},tail:{type:'arrow',width:'med',length:'med'}});
}
function chart(s,type,config){const ch=s.charts.add(type,config);applyPresentationChartFont(ch,{fontFamily:FONT});nativeCharts.push(sources.length);return ch;}
const axisText={typeface:FONT,fontSize:24,fill:C.ink};
const labelText={typeface:FONT,fontSize:25,bold:true,fill:C.ink};

// 1. Question and an early, bounded finding.
{
 const s=slide('', 'Independent research project for the UNOS Associate Data Scientist interview',true);
 text(s,'Classifying rejection\nfrom kidney biopsy RNA',64,108,1120,190,66,C.white,true);
 text(s,'Can molecular measurements classify\nthe recorded biopsy diagnosis?',68,330,1080,115,39,'#CDE6DF');
 text(s,'25 missed rejection cases and 8 false flags',68,504,1120,56,39,C.white,true);
 text(s,'CatBoost on 345 author technical-validation specimens',68,566,1100,42,27,'#CDE6DF');
 sources[0].title='Classifying rejection from kidney biopsy RNA';
}
// 2. Editable conceptual diagram makes input versus reference label explicit.
{
 const s=slide('Kidney biopsy and transplant rejection','Sources: NIDDK, Kidney Transplant and Kidney Biopsy; Zhang et al., 2024. Full links in the HTML script.');
 text(s,'Rejection: the recipient’s immune system attacks the donated kidney.',64,160,1152,86,36);
 const a=node(s,'Biopsy tissue\nA small tissue sample',64,318,328,150,{size:34});
 const b=node(s,'Microscopic examination\nRecorded diagnosis',531,265,650,123,{size:33});
 const c=node(s,'RNA measurements\nInputs to this model',531,448,650,123,{size:33});
 connect(s,a,b);connect(s,a,c);
 text(s,'The prediction concerns this existing specimen.',64,596,1140,43,30,C.teal,true);
}
// 3. Lab terms are defined before the machine-learning vocabulary.
{
 const s=slide('An assay measures specified molecules','Sources: GSE212160; Bruker nCounter technology documentation. This project uses the deposited raw RNA counts.');
 text(s,'RNA is made as genes are expressed.\nThe assay counts signals for selected RNA targets.',64,167,1130,99,37);
 const a=node(s,'RNA from\nbiopsy tissue',64,319,300,124);
 const b=node(s,'Target-specific\nbarcoded probes',491,319,300,124);
 const c=node(s,'Digital counts\nfor each target',918,319,300,124);
 connect(s,a,b);connect(s,b,c);
 text(s,'770 measured targets',66,500,560,61,48,C.teal,true);
 text(s,'758 model inputs + 12 housekeeping targets',66,573,1140,46,32);
}
// 4. Observation and target definition.
{
 const s=slide('One row describes one biopsy specimen','Source: project data audit and diagnosis mapping. “No rejection” does not mean an otherwise healthy biopsy.');
 text(s,'1,395 archived kidney transplant biopsies',64,159,1152,58,42,C.teal,true);
 table(s,[['Recorded diagnosis','Binary label'],['No rejection','0'],['Antibody-mediated rejection','1'],['T-cell-mediated rejection','1'],['Mixed rejection','1']],{y:252,h:310,widths:[878,274],size:31});
 text(s,'Inputs: assay counts     Reference label: recorded diagnosis',64,592,1152,48,29);
}
// 5. Actual arithmetic from a prepared public specimen.
{
 const s=slide('Normalization uses each specimen’s reference targets','Source: shared preprocessing and public specimen GSM6510425. Rounded values shown; computation uses full precision.');
 text(s,'Housekeeping targets provide a within-specimen reference.',64,164,1152,70,34);
 table(s,[['IFNG in this specimen','Value'],['Raw count','4'],['log₂(count + 1)','2.322'],['Mean of 12 housekeeping log counts','7.900'],['Normalized input: 2.322 − 7.900','−5.578']],{y:259,h:293,widths:[891,261],size:29});
 text(s,'Apply to all 758 inputs. Fit later learned steps on training data.',64,577,1152,47,29,C.teal,true);
}
// 6. Cohort and development split, retained from the authors.
{
 const s=slide('Model choice and thresholds use discovery data','Source: saved split, seed 20260915. Cohorts follow the authors; patient and center independence are unverified.');
 const disc=node(s,'Discovery cohort\n1,050 specimens',64,176,670,95,{size:32});
 const train=node(s,'Training\n787 specimens',64,341,306,104);
 const screen=node(s,'Screening\n263 specimens',428,341,306,104);
 connect(s,disc,train,'bottom','top');connect(s,disc,screen,'bottom','top');
 node(s,'Author technical validation\n345 specimens\nEvaluate frozen choices',805,176,411,269,{fill:C.ink,color:C.white,size:32});
 text(s,'Screening rule',64,488,430,43,30,C.teal,true);
 text(s,'Retain at least 90% of rejection cases, then minimize false flags.',64,536,1152,66,34);
}
// 7. Native chart data come directly from the preserved analysis CSV.
{
 const s=slide('Several measurements reduced false flags','Source: frozen primary analysis. Each learned model retains its discovery-selected threshold; constant cutoff is 0.5.');
 text(s,'Same 345 specimens: 169 rejection and 176 no rejection',64,155,1152,46,30);
 chart(s,'bar',{position:{left:56,top:223,width:1170,height:350},categories:['IFNG only','Logistic regression','CatBoost'],series:[{name:'Missed rejection / 169',values:[+ifng.fn,+log.fn,+cat.fn],fill:C.orange},{name:'False flags / 176',values:[+ifng.fp,+log.fp,+cat.fp],fill:C.teal}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:95},hasLegend:true,legend:{position:'bottom',textStyle:{...axisText,fontSize:23}},xAxis:{textStyle:axisText,majorGridlines:null},yAxis:{min:0,max:80,majorUnit:20,textStyle:axisText,majorGridlines:{fill:C.rule,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:labelText},chartFill:C.bg,plotAreaFill:C.bg});
 text(s,`Constant baseline: ${constant.fn} misses and ${constant.fp} false flags. It flags every specimen.`,64,589,1152,47,29);
}
// 8. Denominators and the threshold shortfall remain visible.
{
 const s=slide('Most CatBoost misses were T-cell rejection',analysis);
 text(s,'144 / 169',64,186,450,91,70,C.teal,true);
 text(s,'rejection cases detected',64,285,464,46,32);
 text(s,'85.2%',64,365,460,70,58,C.orange,true);
 text(s,'Below the 90%\nscreening target',64,452,455,92,31);
 table(s,[['Recorded rejection','Missed / total'],['Antibody-mediated','6 / 56'],['T-cell-mediated','18 / 95'],['Mixed','1 / 18']],{x:558,y:195,w:658,h:344,widths:[420,238],size:29});
 text(s,'Errors mean disagreement with the recorded diagnosis.',64,590,1152,44,30);
}
// 9. Candid practical comparison, with descriptive follow-up separated.
{
 const s=slide('The advantage over logistic regression is uncertain','Sources: paired bootstrap analysis (2,000 specimen resamples); discovery-only stability follow-up, 17 Sep 2026.');
 text(s,'8 fewer misses',64,182,1110,84,64,C.teal,true);
 text(s,'Same 8 false flags. The paired miss-difference interval includes zero.',64,279,1138,93,33);
 text(s,'Model selected across 20 discovery splits',64,408,1110,52,34,true);
 table(s,[['CatBoost','Logistic regression'],['13 selections','7 selections']],{y:477,h:122,widths:[576,576],size:30});
 text(s,'Overlapping repetitions describe split variability.',64,606,1130,38,26,C.muted);
}
// 10. Editable software diagram.
{
 const s=slide('Training and serving share the same preprocessing','Source: src/kidney_biopsy/preprocessing.py and prediction.py; CLI and FastAPI use the shared Predictor.');
 const labels=['Read counts','Check targets\nand numbers','Normalize\n758 inputs','Score with\nfrozen model'];
 let prev;labels.forEach((v,i)=>{const n=node(s,v,64+i*298,245,256,150,{size:32});if(prev)connect(s,prev,n);prev=n;});
 text(s,'CSV input',64,180,380,49,34,C.teal,true);
 text(s,'Versioned score + threshold flag',64,459,1152,62,43,C.teal,true);
 text(s,'Diagnosis, specimen ID, cohort and assay batch stay out of the predictors.',64,553,1152,66,31);
}
// 11. Exact measured output, editable, backed by saved browser captures.
{
 const s=slide('One public specimen through the service','Discovery-screen example GSM6510425, recorded no rejection. Demonstrates software; it adds no new validation evidence.');
 text(s,'Public example: GSM6510425',64,166,1140,51,37,C.teal,true);
 table(s,[['Model score','Frozen threshold','Result'],['0.274934','0.876588','Below threshold']],{y:248,h:154,widths:[347,366,439],size:33});
 text(s,'Remove IFNG from the same file',64,455,1140,53,33,true);
 text(s,'“Missing required assay targets: IFNG”',64,521,1140,48,37,C.orange,true);
 text(s,'Model: 20260915_shared:any_rejection:catboost_all_depth4',64,602,1140,35,23,C.muted);
}
// 12. Measured software evidence, with dated scope.
{
 const s=slide('The service reproduces all 345 saved scores','Source: local application checks, 17 Sep 2026. Score agreement is a software check, not new classifier validation.');
 text(s,'345 / 345',64,174,1120,92,76,C.teal,true);
 text(s,'API, command line and saved evaluation agree\nwithin a tolerance of 10⁻¹².',64,292,1120,105,37);
 line(s,64,429,1152);
 text(s,'94 tests passed',64,465,575,67,42,true);
 text(s,'Local research container checked',650,468,566,99,36,true);
 text(s,'Missing targets stop scoring. Incompatible model metadata stops loading.',64,579,1152,61,29);
}
// 13. One measured scope and one next research step.
{
 const s=slide('The result applies to one deposited study','Sources: GSE212160; study and assay review in docs/RESEARCH_CONTEXT.md; primary analysis limitations.');
 text(s,'Established',64,176,500,54,34,C.teal,true);
 text(s,'Agreement with recorded diagnoses\nfor existing transplant biopsies',64,248,1100,97,43);
 line(s,64,374,1152);
 text(s,'Next evidence needed',64,415,700,53,34,C.teal,true);
 text(s,'An independent cohort with known patient and center IDs,\nand documented laboratory quality checks',64,485,1137,105,36);
}
// 14. Clean closing slide, Q&A follows the full talk.
{
 const s=slide('Molecular counts can classify recorded rejection','This presentation was drafted with AI assistance. Public data and study methods are credited in the backup slides.',true);
 text(s,'25 / 169 misses. 8 / 176 false flags.',64,194,1145,87,57,C.white,true);
 text(s,'Logistic regression remains a credible simpler alternative.',64,329,1135,101,39,'#CDE6DF');
 text(s,'The same preprocessing powers a tested research service.',64,478,1135,99,39,'#CDE6DF');
}
// 15-20. Backup material is outside the 20-minute plan.
{
 const s=slide('Backup: complete primary comparison',analysis);
 const names=['CatBoost','Logistic','IFNG only','Constant'];
 table(s,[['Model','Misses','False flags','Sensitivity','Specificity','ROC-AUC'],...[cat,log,ifng,constant].map((m,i)=>[names[i],m.fn,m.fp,(+m.sensitivity*100).toFixed(1)+'%',(+m.specificity*100).toFixed(1)+'%',(+m.roc_auc).toFixed(3)])],{y:198,h:344,widths:[244,136,168,201,205,198],size:26});
 text(s,'Denominators: 169 rejection; 176 no rejection. Fixed thresholds per model.',64,575,1152,66,29);
}
{
 const s=slide('Backup: normalization and threshold selection','Sources: preprocessing.py; saved configuration and screening results in results/reproduction/baseline.');
 text(s,'Normalized target = log₂(raw count + 1)\n− mean of the 12 housekeeping log₂(count + 1) values',64,173,1140,120,36,C.teal,true);
 text(s,'Logistic: scaling fitted on training rows; regularization C = 0.1.\nCatBoost: 300 trees, depth 4, learning rate 0.04.',64,332,1140,109,32);
 text(s,'Both detected 157 / 174 screening rejection cases.\nCatBoost made 5 false flags; logistic made 6.',64,478,1140,95,34);
 text(s,'Flag when score ≥ 0.8765880870219778 for the frozen service.',64,599,1140,39,26,C.muted);
}
{
 const s=slide('Backup: ranking does not guarantee calibrated scores','Source: reliability_bins.csv. Fixed bins; Wilson interval shown for the highlighted descriptive example. No recalibration fitted.');
 chart(s,'scatter',{position:{left:59,top:165,width:726,height:455},series:[{name:'Agreement',xValues:[0,1],values:[0,1],line:{fill:C.muted,width:1.4},marker:{symbol:'none'}},{name:'Observed bins',xValues:bins.map(x=>Number(Number(x.mean_score).toFixed(6))),values:bins.map(x=>Number(Number(x.observed_fraction).toFixed(6))),line:{fill:'none',width:0},marker:{symbol:'circle',size:9},fill:C.teal}],scatterOptions:{style:'lineWithMarkers'},hasLegend:false,xAxis:{min:0,max:1,majorUnit:.2,title:{text:'Mean model score',textStyle:axisText},textStyle:axisText,numberFormatCode:'0.0',majorGridlines:null},yAxis:{min:0,max:1,majorUnit:.2,title:{text:'Recorded rejection fraction',textStyle:axisText},textStyle:axisText,numberFormatCode:'0.0',majorGridlines:{fill:C.rule,width:1}},chartFill:C.bg,plotAreaFill:C.bg});
 text(s,'Score bin 0.8–0.9',820,185,396,50,32,C.teal,true);
 text(s,'0.847',820,258,396,77,58,true);
 text(s,'mean score',820,331,396,42,29);
 text(s,'7 / 16',820,408,396,73,54,C.orange,true);
 text(s,'had recorded rejection\n43.8% (95% CI 23.1–66.8%)',820,493,396,108,27);
}
{
 const s=slide('Backup: subtype follow-up retained the binary service','Source: subtype follow-up, 15 Sep 2026. Reuses an already examined validation cohort; independent confirmation remains needed.');
 table(s,[['Model','Any-rejection misses','False flags'],['Binary CatBoost','25 / 169','8 / 176'],['Four-class CatBoost','29 / 169','8 / 176'],['Four-class logistic','28 / 169','10 / 176'],['Separate component models','24 / 169','15 / 176']],{y:200,h:325,widths:[532,342,278],size:28});
 text(s,'Four-class logistic recognized 10 / 18 mixed diagnoses,\nwith 5 false mixed calls.',64,555,1140,80,30);
}
{
 const s=slide('Backup: study, assay and deployment limits','Sources: primary analysis, research context, and current verification guide.');
 table(s,[['Question','What the project establishes'],['Independent patients / centers?','Independence not verified'],['Laboratory assay quality?','File and numeric checks; assay QC not repeated'],['Individual probabilities?','Calibration remains limited'],['Cloud deployment?','Local container tested; cloud work deferred']],{y:194,h:379,widths:[456,696],size:27});
 text(s,'Biopsy-level resampling may understate uncertainty if specimens are related.',64,588,1152,48,27);
}
{
 const s=slide('Backup: sources and contributions','Full URLs and repository evidence paths appear beside each slide in the HTML speaking script.');
 text(s,'Public study',64,166,340,43,30,C.teal,true);
 text(s,'Zhang et al., Laboratory Investigation (2024)\nGSE212160 raw NanoString B-HOT measurements',64,218,1140,91,33);
 text(s,'This project',64,343,340,43,30,C.teal,true);
 text(s,'Binary comparison and runs produced in this repository,\nshared software and a tested local demonstration',64,393,1140,96,33);
 text(s,'Presentation approach',64,528,480,41,30,C.teal,true);
 text(s,'Bourne (2007); Kosslyn et al. (2012); Garner & Alley (2013); Rougier et al. (2014)',64,582,1140,52,24);
}

await fs.mkdir(build,{recursive:true});await fs.mkdir(path.join(out,'slides'),{recursive:true});
const exportedPath=path.join(build,'exported.pptx');
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(p)).save(exportedPath);
// No speaker notes are authored; even the exporter's blank notes parts are removed.
const notes=spawnSync(process.env.RUNTIME_PYTHON,[path.join(out,'source/remove_notes.py'),exportedPath,candidatePath],{encoding:'utf8'});
if(notes.status!==0)throw new Error(notes.stderr||'Removing empty notes failed');
await fs.writeFile(path.join(build,'slide_sources.json'),JSON.stringify(sources,null,2));
await fs.writeFile(path.join(build,'presentation.proto.json'),JSON.stringify(p.toProto()));
for(let i=0;i<sources.length;i++){
 const s=p.slides.getItem(i);
 const img=await p.export({slide:s,format:'png',scale:1.5});
 await fs.writeFile(path.join(out,'slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await img.arrayBuffer()));
 const layout=await s.export({format:'layout'});
 await fs.writeFile(path.join(build,`slide-${i+1}.layout.json`),await layout.text());
 console.log(`Rendered ${i+1}/${sources.length}`);
}
const finalPath=path.join(out,process.env.DECK_FILENAME||'unos_kidney_biopsy.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[...new Set(nativeTables)].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[...new Set(nativeTables)],requiredNativeChartOwnerSlides:[...new Set(nativeCharts)],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,`${path.basename(finalPath)}.${Date.now()}.validation.json`)});
console.log(JSON.stringify(result));
