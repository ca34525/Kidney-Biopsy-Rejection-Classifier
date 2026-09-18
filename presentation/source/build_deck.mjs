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
const analysis='Source: frozen primary evaluation, 15 Sep 2026. Same 345 specimens.';
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
  if(source)text(s,source,64,657,1090,38,18,dark?'#D6E8E5':C.muted);
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

// Main sequence. Each script topic has a corresponding label or visual.
// 1. Title and research question only.
{
 const s=slide('', '',true);
 text(s,'Classifying rejection\nfrom kidney biopsy RNA',64,156,1136,194,68,C.white,true);
 text(s,'Can molecular measurements classify\nthe recorded biopsy diagnosis?',68,416,1100,121,42,'#CDE6DF');
 sources[0].title='Classifying rejection from kidney biopsy RNA';
}
// 2. Tissue provides measurements and a recorded diagnosis.
{
 const s=slide('Kidney biopsy and transplant rejection','Sources: NIDDK, Kidney Transplant and Kidney Biopsy; Zhang et al. (2024)');
 text(s,'Rejection: the recipient’s immune system attacks the donated kidney.',64,150,1152,85,36);
 const a=node(s,'',64,302,336,154);
 text(s,'Biopsy tissue:',80,323,304,47,36,C.ink,true,'center');
 text(s,'A small sample\nfrom the kidney',80,375,304,65,31,C.ink,false,'center');
 const b=node(s,'',535,255,681,127);
 text(s,'Microscopic examination (histology)',552,272,647,42,32,C.ink,true,'center');
 text(s,'Recorded diagnosis',552,320,647,42,34,C.ink,false,'center');
 const c=node(s,'',535,422,681,127);
 text(s,'Molecular measurements',552,438,647,42,34,C.ink,true,'center');
 text(s,'Inputs to the model',552,485,647,42,32,C.ink,false,'center');
 connect(s,a,b);connect(s,a,c);
 text(s,'Research use: compare measurements with the diagnosis\nof tissue already collected.',64,568,1152, 72,30,C.teal,true);
}
// 3. Give the biological labels their own visual explanation.
{
 const s=slide('Recorded diagnoses','Source: Zhang et al. (2024), GSE212160; project diagnosis mapping');
 table(s,[['Recorded diagnosis','Meaning','Model label'],['Antibody-mediated rejection','Antibodies: immune proteins','Rejection'],['T-cell-mediated rejection','T cells: immune cells','Rejection'],['Mixed rejection','Both rejection processes','Rejection'],['No rejection','No recorded rejection','No rejection']],{y:181,h:367,widths:[485,407,260],size:28});
 text(s,'The main question combines all three forms of rejection.',64,566,1152,43,33,C.teal,true);
 text(s,'“No rejection” does not mean an otherwise healthy biopsy.',64,611,1152,34,27);
}
// 4. Define the laboratory vocabulary in the order it is used.
{
 const s=slide('Measuring RNA in biopsy tissue','Sources: Bruker nCounter documentation; GSE212160');
 text(s,'RNA includes messages cells make when genes are active.',64,151,1152,65,36);
 text(s,'Assay: a laboratory test     Panel: a fixed list of molecules to measure',64,225,1152,62,31);
 const a=node(s,'RNA from\nbiopsy tissue',64,331,305,126,{size:34});
 const b=node(s,'Probes recognize\nspecific RNA',487,331,305,126,{size:32});
 const c=node(s,'Barcodes identify\nsignals to count',910,331,305,126,{size:32});
 connect(s,a,b);connect(s,b,c);
 text(s,'NanoString nCounter, using the B-HOT panel',64,488,1152,53,36,C.teal,true);
 text(s,'Example output: IFNG count = 4 in one public specimen',64,568,1152,51,32);
}
// 5. Separate what is measured from what is predicted.
{
 const s=slide('The measurements used by the model','Sources: GSE212160; B-HOT panel consensus (2020); project data contract');
 text(s,'770 RNA measurements per specimen',64,155,1152,75,48,C.teal,true);
 text(s,'758',64,250,470,91,70,C.teal,true);
 text(s,'Measurements used as model inputs\nIncludes some viral RNA signals',64,349,648,90,32);
 text(s,'12',807,250,409,91,70,C.teal,true);
 text(s,'Housekeeping references\nPrepare the other counts',807,349,409,90,30);
 line(s,64,469,1152);
 text(s,'Assay “target”: a molecule a probe recognizes',64,485,1152,45,31);
 text(s,'Counts reflect gene activity and the mixture of cells in the tissue.',64,541,1152,51,33);
 text(s,'The 12 reference measurements are removed after normalization.',64,606,1152,37,28);
}
// 6. Explain the identifier by showing what it joins.
{
 const s=slide('One row describes one biopsy specimen','Source: project data audit, 15 Sep 2026');
 text(s,'1,395 specimens included. No exclusions.',64,156,1152,65,43,C.teal,true);
 text(s,'Specimen ID: GSM6510425',64,243,1152,53,35,true);
 const a=node(s,'RNA count record\nIFNG = 4, …',64,332,330,125,{size:32});
 const b=node(s,'Match the same\nspecimen ID',487,332,306,125,{size:32});
 const c=node(s,'Diagnosis record\nNo rejection',886,332,330,125,{size:32});
 connect(s,a,b);connect(s,b,c);
 text(s,'Only the prepared RNA measurements enter the model.',64,487,1152,51,34,C.teal,true);
 text(s,'IDs, diagnosis and cohort stay separate. No duplicate normalized profiles.',64,547,1152,42,28);
 text(s,'Specimen counts do not establish the number of independent patients.',64,598,1152,43,28);
}
// 7. One concrete example, with the reason for each preparation step.
{
 const s=slide('Preparing counts for the model','Source: shared preprocessing; public specimen GSM6510425. Values rounded for display.');
 text(s,'Add 1 to allow zero counts. Take log₂ to compress the range.',64,153,1152,64,34);
 table(s,[['IFNG in this specimen','Value'],['Raw count','4'],['log₂(count + 1)','2.322'],['Mean of 12 housekeeping log counts','7.900'],['Normalized input: 2.322 − 7.900','−5.578']],{y:247,h:287,widths:[891,261],size:30});
 text(s,'Each specimen supplies its own reference. Keep 758 prepared inputs.',64,553,1152,44,30,C.teal,true);
 text(s,'Fit any later learned scaling on training specimens only.',64,606,1152,36,29);
}
// 8. Cohort names and their jobs, before discussing model choices.
{
 const s=slide('Development and evaluation specimens','Source: authors’ cohorts and saved project split, seed 20260915');
 const disc=node(s,'Development: 1,050 specimens\nAuthors’ discovery cohort',64,178,699,107,{size:34});
 const train=node(s,'Training: 787\nFit the models',64,370,316,119,{size:32});
 const screen=node(s,'Screening: 263\nChoose model + threshold',430,370,333,119,{size:30});
 connect(s,disc,train,'bottom','top');connect(s,disc,screen,'bottom','top');
 node(s,'Evaluation: 345\nAuthors’ technical validation\n\nCompare frozen choices',820,178,396,311,{fill:C.ink,color:C.white,size:30});
 text(s,'The saved split keeps the original diagnosis proportions similar.',64,533,1152,45,31,C.teal,true);
 text(s,'Patient and center independence are unverified.',64,598,1152,42,31);
}
// 9. Model names now come with an explanation.
{
 const s=slide('Four model comparisons','Source: frozen primary configuration and analysis, 15 Sep 2026');
 table(s,[['Model','What it learns'],['Constant baseline','One score: the training rejection fraction'],['IFNG only','A relationship using one RNA measurement'],['Logistic regression','A weighted combination of 758 measurements'],['CatBoost','A combination of decision trees']],{y:185,h:351,widths:[354,798],size:30});
 text(s,'Logistic regularization limits how large the weights can become.',64,551,1152,43,30);
 text(s,'Same specimen preparation. Same evaluation specimens.',64,607,1152,38,32,C.teal,true);
}
// 10. Define the decision and error vocabulary before reporting results.
{
 const s=slide('Turning a score into a rejection flag','Source: discovery screening rule and frozen model metadata');
 const a=node(s,'Model score',64,171,330, 80,{size:34});
 const b=node(s,'Compare with threshold',482,171,376,80,{size:32});
 const c=node(s,'Rejection flag',946,171,270,80,{size:32});
 connect(s,a,b);connect(s,b,c);
 text(s,'Missed rejection',64,292,530,42,33,C.orange,true);
 text(s,'Recorded rejection, score below threshold',64,344,535,75,30);
 text(s,'False flag',686,292,530,42,33,C.teal,true);
 text(s,'Recorded no rejection, score at or above threshold',686,344,530,75,30);
 line(s,64,446,1152);
 text(s,'Screening: detect at least 90% of rejection, then minimize false flags.',64,465,1152,75,34);
 text(s,'Freeze the model and threshold together. CatBoost cutoff: 0.876588',64,548,1152,44,30,C.teal,true);
 text(s,'90% is an experiment choice. A score is not a calibrated probability.',64,604,1152,40,28);
}
// 11. Editable data and explicit denominators.
{
 const s=slide('Several measurements reduced false flags','Source: frozen primary evaluation, 15 Sep 2026. Each model keeps its chosen threshold.');
 text(s,'Same 345 specimens: 169 rejection and 176 no rejection',64,145,1152,48,32);
 chart(s,'bar',{position:{left:56,top:202,width:1170,height:327},categories:['IFNG only','Logistic regression','CatBoost'],series:[{name:'Missed rejection / 169',values:[+ifng.fn,+log.fn,+cat.fn],fill:C.orange},{name:'False flags / 176',values:[+ifng.fp,+log.fp,+cat.fp],fill:C.teal}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:95},hasLegend:true,legend:{position:'bottom',textStyle:{...axisText,fontSize:25}},xAxis:{textStyle:axisText,majorGridlines:null},yAxis:{min:0,max:80,majorUnit:20,textStyle:axisText,majorGridlines:{fill:C.rule,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:labelText},chartFill:C.bg,plotAreaFill:C.bg});
 text(s,`Constant: ${constant.fn} / 169 missed, ${constant.fp} / 176 false flags. It flags everyone.`,64,541,1152,42,29);
 text(s,'CatBoost versus IFNG: 67 fewer false flags, 11 more misses.',64,599,1152,45,33,C.teal,true);
}
// 12. Group counts and detection shortfall.
{
 const s=slide('Most CatBoost misses were T-cell rejection','Source: frozen primary evaluation and screening results, 15 Sep 2026');
 text(s,'144 / 169',64,177,450,86,70,C.teal,true);
 text(s,'rejection cases detected',64,269,470,43,32);
 text(s,'85.2% sensitivity',64,337,470,56,43,C.orange,true);
 text(s,'Screening: 157 / 174 (90.2%)\nEvaluation falls below\nthe 90% selection target',64,424,470,142,30);
 table(s,[['Recorded rejection','Missed / total'],['Antibody-mediated','6 / 56'],['T-cell-mediated','18 / 95'],['Mixed','1 / 18']],{x:558,y:183,w:658,h:357,widths:[420,238],size:29});
 text(s,'Errors describe disagreements with recorded diagnoses.',64,592,1152,49,32);
}
// 13. Keep both sources of uncertainty visible and distinct.
{
 const s=slide('The advantage over logistic regression is uncertain','Sources: paired bootstrap analysis; discovery stability follow-up, 17 Sep 2026');
 text(s,'Fixed models, same evaluation specimens',64,155,1152,46,32,C.teal,true);
 text(s,'8 fewer misses among 169 rejection specimens',64,214,1152,68,44,true);
 text(s,'Both make 8 / 176 false flags. The 95% interval for the\ndetection advantage includes zero (2,000 specimen resamples).',64,289,1152,88,31);
 line(s,64,400,1152);
 text(s,'Model choice across 20 development splits',64,407,1152,49,33,C.teal,true);
 table(s,[['CatBoost','Logistic regression'],['13 selections','7 selections']],{y:465,h:128,widths:[576,576],size:30});
 text(s,'The repetitions overlap. Logistic regression remains a simpler alternative.',64,611,1152,38,29);
}
// 14. Shared implementation and failures that stop scoring.
{
 const s=slide('Training and serving share the same preprocessing','Source: shared preprocessing and Predictor; application contract');
 text(s,'CSV through the command line or web application',64,155,1152,54,35,C.teal,true);
 const labels=['Read counts','Check names\nand numbers','Normalize\n758 inputs','Score with\nfrozen model'];
 let prev;labels.forEach((v,i)=>{const n=node(s,v,64+i*298,253,256,130,{size:31});if(prev)connect(s,prev,n);prev=n;});
 text(s,'Response: specimen ID, score, threshold, flag and model version',64,409,1152,65,33,C.teal,true);
 text(s,'Missing or duplicate names, negative or non-finite counts: stop scoring.',64,499,1152,72,30);
 text(s,'Only the configured model can load. Scores remain research scores.',64,594,1152,44,29);
}
// 15. The slide also works when the presenter uses the static fallback.
{
 const s=slide('One public specimen through the service','Source: public discovery-screen example and saved application checks');
 text(s,'GSM6510425: recorded no rejection',64,148,1152,51,36,C.teal,true);
 table(s,[['Model score','Frozen threshold','Rejection flag'],['0.274934','0.876588','False (below cutoff)']],{y:216,h:133,widths:[346,366,440],size:31});
 text(s,'IFNG: log₂(4 + 1) = 2.322. Housekeeping reference: 7.900',64,367,1152,45,30);
 text(s,'Normalized input = −5.578',64,416,1152,42,33,C.teal,true);
 text(s,'Remove IFNG: “Missing required assay targets: IFNG”',64,474,1152,59,32,C.orange,true);
 text(s,'Previous result clears. No new score returns.',64,535,1152,41,30);
 text(s,'Model: 20260915_shared:any_rejection:catboost_all_depth4',64,592,1152,34,25,C.muted);
}
// 16. Consistency, input failures, and the actual deployment status.
{
 const s=slide('The service reproduces all 345 saved scores','Source: local verification, 17 Sep 2026. Software consistency check.');
 text(s,'345 / 345',64,158,1120,90, 76,C.teal,true);
 text(s,'API, command line and saved evaluation agree within 10⁻¹².',64,256,1152,78,35);
 line(s,64,359,1152);
 text(s,'94 tests passed',64,386,1152,57,42,true);
 text(s,'Reordered columns: same score. Invalid counts: no score.\nIncompatible model metadata: model does not load.',64,452,1152,89,31);
 text(s,'Local research container checked. Cloud deployment remains deferred.',64,580,1152,63,31,C.teal,true);
}
// 17. Each limitation named in the script is visible here.
{
 const s=slide('The result applies to one deposited study','Sources: GSE212160; project research context and primary analysis');
 text(s,'Established: agreement with recorded biopsy diagnoses',64,155,1152,62,38,C.teal,true);
 text(s,'Patient and center independence: unverified\nAssay groups: tied to cohort membership\nFile checks: do not establish laboratory assay quality',64,246,1152,176,34);
 line(s,64,444,1152);
 text(s,'Next: a new cohort with known patient and center IDs,\nand documented laboratory quality checks',64,464,1152,107,36,C.teal,true);
 text(s,'Specify models and thresholds first. Keep logistic in the comparison.',64,600,1152,44,29);
}
// 18. Results belong here, after the question and evidence.
{
 const s=slide('Molecular counts can classify recorded rejection','Public data: Zhang et al. (2024), GSE212160. Presentation prepared with AI assistance.',true);
 text(s,'CatBoost, 345 evaluation specimens',64,156,1152,43,31,'#CDE6DF');
 text(s,'25 / 169 misses. 8 / 176 false flags.',64,219,1152,84,56,C.white,true);
 text(s,'Logistic regression remains a credible simpler alternative.',64,330,1152,87,37,'#CDE6DF');
 text(s,'Shared preprocessing supports a tested research service.',64,448,1152,81,37,'#CDE6DF');
 text(s,'Next: test the fixed comparison on a new cohort.',64,562,1152,61,35,'#CDE6DF');
}
// 19-24. Backup material is outside the 20-minute plan.
{
 const s=slide('Backup: complete primary comparison',analysis);
 const names=['CatBoost','Logistic','IFNG only','Constant'];
 table(s,[['Model','Misses','False flags','Sensitivity','Specificity','ROC-AUC'],...[cat,log,ifng,constant].map((m,i)=>[names[i],m.fn,m.fp,(+m.sensitivity*100).toFixed(1)+'%',(+m.specificity*100).toFixed(1)+'%',(+m.roc_auc).toFixed(3)])],{y:198,h:344,widths:[244,136,168,201,205,198],size:26});
 text(s,'Denominators: 169 rejection; 176 no rejection. Fixed thresholds per model.',64,575,1152,66,29);
}
{
 const s=slide('Backup: normalization and threshold selection','Sources: preprocessing.py; saved configuration and screening results in results/reproduction/baseline.');
 text(s,'Normalized measurement = log₂(raw count + 1)\n− mean of the 12 housekeeping log₂(count + 1) values',64,173,1140,120,36,C.teal,true);
 text(s,'Logistic: scaling fitted on training rows; regularization C = 0.1.\nCatBoost: 300 trees, depth 4, learning rate 0.04.',64,332,1140,109,32);
 text(s,'Both detected 157 / 174 screening rejection cases.\nFalse flags: CatBoost 5 / 89, logistic 6 / 89.',64,478,1140,95,34);
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
 text(s,'Four-class logistic recognized 10 / 18 mixed diagnoses,\nwith 5 false mixed calls among 327 non-mixed specimens.',64,555,1140,80,30);
}
{
 const s=slide('Backup: study, assay and deployment limits','Sources: primary analysis, research context, and current verification guide.');
 table(s,[['Question','What the project establishes'],['Patient / center independence?','Independence not verified'],['Laboratory assay quality?','File checks only; lab quality unverified'],['Individual probabilities?','Calibration remains limited'],['Cloud deployment?','Local container tested; cloud work deferred']],{y:179,h:390,widths:[456,696],size:27});
 text(s,'Biopsy-level resampling may understate uncertainty if specimens are related.',64,588,1152,48,27);
}
{
 const s=slide('Backup: sources and contributions','');
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
const finalPath=path.join(out,process.env.DECK_FILENAME||'unos_kidney_biopsy_second_pass.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[...new Set(nativeTables)].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[...new Set(nativeTables)],requiredNativeChartOwnerSlides:[...new Set(nativeCharts)],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,`${path.basename(finalPath)}.${Date.now()}.validation.json`)});
console.log(JSON.stringify(result));
