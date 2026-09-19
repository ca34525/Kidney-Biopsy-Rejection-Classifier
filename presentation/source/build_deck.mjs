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
const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation, makeNativeBulletParagraphs } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
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
const analysis='Source: primary evaluation, 15 Sep 2026. Same 345 specimens.';
function text(s, value, x, y, w, h, size=34, color=C.ink, bold=false, align='left') {
  if (typeof color === 'boolean') { bold=color; color=C.ink; }
  const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=value;
  sh.text.style={typeface:FONT,fontSize:size,color,bold,alignment:align,autoFit:'none',verticalAlignment:'middle',wrap:true};
  return sh;
}
function line(s,x,y,w,color=C.rule){s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:0},line:{fill:color,width:1.2}});}
function bullets(s, items, x=64, y=165, w=1152, h=110, size=32, color=C.ink, gap=12) {
  const sh=text(s,'',x,y,w,h,size,color);
  sh.text=makeNativeBulletParagraphs(items,{marginLeftPoints:22,hangingPoints:12,spaceAfterPoints:gap});
  sh.text.style={typeface:FONT,fontSize:size,color,autoFit:'none',verticalAlignment:'top',wrap:true};
  return sh;
}
function definition(s, label, body, y, {nested=false,h=100}={}) {
  const x=nested?111:64, w=nested?1105:1152;
  const sh=bullets(s,[label+body],x,y,w,h,nested?32:34);
  const paragraph=makeNativeBulletParagraphs([label+body],{marginLeftPoints:22,hangingPoints:12,spaceAfterPoints:0})[0];
  paragraph.runs=[{run:label,textStyle:{bold:true}},body];
  sh.text=[paragraph];
  return sh;
}
function example(s,label,body,y,h) {
  s.shapes.add({geometry:'rect',position:{left:94,top:y,width:1122,height:h},fill:C.light,line:{fill:C.rule,width:1}});
  text(s,label,113,y+9,1084,37,28,C.teal,true);
  text(s,body,113,y+48,1084,h-55,30);
}
function slide(title,source='',dark=false,number=true){
  const s=p.slides.add(); const i=p.slides.items?.length || sources.length+1;
  s.background.fill=dark?C.ink:C.bg;
  if(title)text(s,title,64,43,1152,105,46,dark?C.white:C.ink,true);
  if(source)text(s,source,64,657,1090,38,18,dark?'#D6E8E5':C.muted);
  if(number)text(s,String(i).padStart(2,'0'),1167,662,48,30,18,dark?'#D6E8E5':C.muted,false,'right');
  sources.push({slide:i,title,source}); return s;
}
function table(s,values,{x=64,y=180,w=1152,h=360,widths,rowHeights,size=30,padY=11}={}){
  const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,...(widths?{columnWidths:widths}:{})});
  t.borders.assign({fill:C.rule,width:1,style:'solid'});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2===0?'#EDF3F0':C.white);
    cell.text.style={typeface:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0,autoFit:'none'};
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:18,right:15,top:padY,bottom:padY},anchor:'center'});
  if(rowHeights)rowHeights.forEach((height,index)=>{t.rows[index].height=height;});
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
// The user's title-only opening.
{
 const s=slide('', '',true,false);
 text(s,'Classifying Kidney\nTransplant Rejection\nfrom Biopsy RNA',64,181,1152,318,70,C.white,true);
 sources[0].title='Classifying Kidney Transplant Rejection from Biopsy RNA';
}
// Definitions and the two forms of biopsy evidence.
{
 const s=slide('Transplant rejection and kidney biopsy','Sources: NIDDK, Kidney Transplant and Kidney Biopsy; Zhang et al. (2024)');
 definition(s,'Rejection: ','The recipient’s immune system attacks the donated kidney.',177,{h:87});
 definition(s,'Kidney biopsy: ','A small tissue sample collected from the kidney for examination.',296,{h:88});
 definition(s,'Histology: ','Microscopic examination reveals injury and inflammation and supports the recorded diagnosis.',419,{nested:true,h:92});
 definition(s,'Molecular measurements: ','Counts of selected RNA types provide the model’s inputs.',548,{nested:true,h:87});
}
// A clearly hypothetical case illustrates the proposed purpose.
{
 const s=slide('Possible Use: Molecular Second Opinion for Ambiguous Biopsies','Source: Banff reference guide (updated Apr 2026).');
 bullets(s,['Sometimes the microscopic findings are borderline or conflict with other clinical evidence.'],64,172,1152,86,31);
 example(s,'Hypothetical Example:','A biopsy shows mild inflammation, but the microscopic findings do not clearly establish rejection.',270,135);
 bullets(s,['This project tests how well RNA classifies recorded rejection diagnoses.'],64,425,1152,71,31);
 example(s,'Hypothetical Example, continued:','A high rejection score could add evidence for specialist review of this biopsy. That use needs direct validation.',507,135);
}
{
 const s=slide('Evidence for a molecular second opinion');
 text(s,'Banff guidance\n2026',64,167,274,96,32,C.ink,true);
 text(s,'Considers validated molecular tests\nfor difficult biopsy interpretations',365,161,851,104,33);
 line(s,64,293,1152);
 text(s,'B-HOT study\nRosales, 2022',64,322,274,90,31,C.ink,true);
 text(s,'Higher initial molecular scores in patients who\nlater developed chronic active antibody-mediated\nrejection, despite no initial diagnosis of it',365,311,851,140,31);
 line(s,64,480,1152);
 text(s,'This project measures agreement with recorded diagnoses.\nIts value in ambiguous biopsies needs direct evaluation.',64,514,1152,114,33,C.teal,true);
}
datasetSlide();
// Give the biological labels their own visual explanation.
{
 const s=slide('Outcome: rejection versus no rejection','Source: Zhang et al. (2024), GSE212160; project diagnosis mapping');
 table(s,[['Recorded diagnosis','Meaning','Model label'],['Antibody-mediated rejection','Antibodies: immune proteins','Rejection'],['T-cell-mediated rejection','T cells: immune cells','Rejection'],['Mixed rejection','Both rejection processes','Rejection'],['No rejection','No recorded rejection','No rejection']],{y:181,h:367,widths:[485,407,260],size:28});
 text(s,'The main question combines all three forms of rejection.',64,585,1152,60,32,C.teal);
}
// Define the laboratory vocabulary in the order it is used.
function assaySlide(){
 const s=slide('Backup: measuring biopsy RNA with NanoString nCounter','Sources: Zhang et al. (2024), Methods; Bruker nCounter documentation; GSE212160');
 bullets(s,[
  'RNA includes messages cells make when genes are active.',
  'An assay is a laboratory test. B-HOT is the fixed panel of RNA types measured in this study.',
  'The laboratory extracts RNA from preserved tissue. Probes recognize selected RNAs, and NanoString nCounter counts their identifying barcodes.'
 ],64,179,1152,372,34,C.ink,22);
 text(s,'Example: IFNG count = 4 in one public specimen',94,548,1122,58,34,C.ink,true);
}
// Separate what is measured from what is predicted.
{
 const s=slide('The measurements used to build the features','Sources: GSE212160; B-HOT panel consensus (2020); project data contract');
 text(s,'770 RNA counts per specimen, one for each RNA type measured.',64,170,1152,81,34,C.teal);
 text(s,'758',64,285,535,80,64,C.ink,true);
 text(s,'Model measurements',64,369,535,49,34,C.ink,true);
 bullets(s,['Normalized counts are the model inputs.','Include human and viral RNA.','Signals depend on gene activity and the cell mixture.'],64,430,540,200,29,C.ink,12);
 text(s,'12',687,285,529,80,64,C.ink,true);
 text(s,'Housekeeping references',687,369,529,49,34,C.ink,true);
 bullets(s,['12 different reference RNAs.','Used to normalize the other counts.','Excluded as separate model inputs.'],687,430,529,200,29,C.ink,12);
}
// Explain the identifier by showing what it joins.
function datasetSlide(){
 const s=slide('What the dataset contains','Sources: GSE212160; Zhang et al. (2024), Tables 5–6; project data reader');
 text(s,'1,395 biopsy specimens, with one row per specimen in each table.',64,165,1152,81,33,C.teal);
 text(s,'RNA counts',64,276,502,47,34,C.ink,true);
 text(s,'Specimen information',716,276,500,47,34,C.ink,true);
 table(s,[['Column','Example'],['Specimen ID (key)','GSM6510425'],['IFNG','4'],['GUSB (reference)','260'],['Other RNA counts','…']],{x:64,y:350,w:502,h:239,widths:[265,237],size:25,padY:6});
 table(s,[['Column','Example'],['Specimen ID (key)','GSM6510425'],['Recorded diagnosis','No rejection'],['Study group','Discovery'],['Other details','…']],{x:716,y:350,w:500,h:239,widths:[270,230],size:25,padY:6});
 line(s,566,422,150,C.muted);
 text(s,'1 : 1',574,380,134,34,25,C.ink,true,'center');
 text(s,'Same ID',574,430,134,35,24,C.ink,false,'center');
 text(s,'Includes 1,193 transplant biopsies and 202 native-kidney controls.',64,610,1152,39,27);
}
// One concrete example, with the reason for each preparation step.
{
 const s=slide('Preparing counts for the model','Source: shared preprocessing; public specimen GSM6510425. Values rounded for display.');
 table(s,[['For each of the 758 RNA counts','IFNG example'],['1. Start with the raw count','4'],['2. Calculate log₂(count + 1)','2.322'],['3. Average log₂(count + 1) for the 12 reference RNAs','7.900'],['4. Subtract that reference','2.322 − 7.900 = −5.578']],{y:183,h:333,widths:[806,346],size:29});
 text(s,'Housekeeping RNAs help account for differences in how much RNA a specimen supplies.',64,557,1152,89,30,C.teal);
}
// Cohort names and their jobs, before discussing model choices.
{
 const s=slide('Development and evaluation specimens','Sources: Zhang et al. (2024), Methods; saved project split, seed 20260915');
 bullets(s,['We use the authors’ two study groups: discovery and validation cohorts.','Our training / screening split keeps diagnosis proportions similar.'],64,166,1152,126,31,C.ink,13);
 const disc=node(s,'Discovery Cohort\n1,050 specimens',64,322,699,103,{size:33});
 const train=node(s,'Training: 787\nFit the models',64,496,316,110,{size:31});
 const screen=node(s,'Screening: 263\nChoose model and threshold',430,496,333,110,{size:29});
 connect(s,disc,train,'bottom','top');connect(s,disc,screen,'bottom','top');
 node(s,'Validation Cohort\n345 specimens\n\nEvaluate the selected\nmodel and threshold',820,322,396,284,{fill:C.ink,color:C.white,size:30});
 text(s,'*Patient and referring-center separation are not documented in the study.',64,614,1152,36,26);
}
// Model names now come with an explanation.
{
 const s=slide('Models compared','Sources: primary configuration and analysis, 15 Sep 2026; Zhang et al., Supplementary Table S2');
 text(s,'Each model produces a score for rejection versus no rejection.',64,165,1152,75,33,C.teal);
 table(s,[['Model','What it learns'],['Constant baseline','One score: the training rejection fraction'],['IFNG only','One immune-related RNA measurement\nas a simple benchmark'],['Logistic regression','A weighted combination of 758 measurements.\nRegularization limits the size of the weights.'],['CatBoost','A combination of decision trees']],{y:254,h:372,rowHeights:[53,61,78,110,70],widths:[354,798],size:29});
}
// Define the decision and error vocabulary before reporting results.
{
 const s=slide('Choosing a rejection threshold','Source: discovery screening rule and selected model metadata');
 text(s,'Recall',64,167,544,45,35,C.orange,true);
 text(s,'Proportion of recorded rejection\ncases detected',64,224,544,81,30);
 text(s,'(False negatives are missed cases.)',64,323,544,67,28,C.orange);
 text(s,'Precision',704,167,512,45,35,C.teal,true);
 text(s,'Proportion of positive flags\nwith recorded rejection',704,224,512,81,30);
 text(s,'(False positives are incorrect flags.)',704,323,512,67,28,C.teal);
 text(s,'Selection using screening specimens',64,420,1152,40,32,C.ink,true);
 table(s,[['Step','Rule'],['1','Detect at least 90% of recorded rejection cases.*'],['2','Among qualifying choices, minimize false positives.'],['3','Keep the chosen model and threshold for evaluation.']],{y:473,h:151,rowHeights:[37,38,38,38],widths:[112,1040],size:25,padY:2});
 text(s,'*90% is an experimental target.',64,632,1152,27,23,C.muted);
}
// Editable data and explicit denominators.
{
 const s=slide('Validation results','Source: primary evaluation, 15 Sep 2026. Errors are against recorded diagnoses.');
 text(s,'Same 345 specimens: 169 rejection and 176 no rejection',64,145,1152,48,32);
 chart(s,'bar',{position:{left:56,top:202,width:1170,height:327},categories:['IFNG only','Logistic regression','CatBoost'],series:[{name:'False negatives / 169',values:[+ifng.fn,+log.fn,+cat.fn],fill:C.orange},{name:'False positives / 176',values:[+ifng.fp,+log.fp,+cat.fp],fill:C.teal}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:95},hasLegend:true,legend:{position:'bottom',textStyle:{...axisText,fontSize:25}},xAxis:{textStyle:axisText,majorGridlines:null},yAxis:{min:0,max:80,majorUnit:20,textStyle:axisText,majorGridlines:{fill:C.rule,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:labelText},chartFill:C.bg,plotAreaFill:C.bg});
 bullets(s,[`Constant baseline: ${constant.fn} false negatives, ${constant.fp} false positives. It flags everyone.`,'CatBoost versus IFNG: 67 fewer false positives, 11 more false negatives.'],64,546,1152,103,29,C.ink,11);
}
// Group counts and detection shortfall.
{
 const s=slide('Most CatBoost misses were T-cell rejection','Source: primary evaluation and screening results, 15 Sep 2026');
 text(s,'144 / 169 detected',64,190,490,70,47,C.ink,true);
 text(s,'85.2% recall (sensitivity)\nin evaluation',64,273,490,84,33);
 bullets(s,['Screening: 157 / 174 detected (90.2%).','Evaluation falls below the 90% selection target.'],64,393,474,180,30,C.ink,18);
 text(s,'Misses by recorded diagnosis',595,175,621,48,31,C.ink,true);
 table(s,[['Recorded rejection','Missed / total'],['Antibody-mediated','6 / 56'],['T-cell-mediated','18 / 95'],['Mixed','1 / 18']],{x:595,y:250,w:621,h:325,widths:[397,224],size:28});
}
// Keep both sources of uncertainty visible and distinct.
{
 const s=slide('The advantage over logistic regression is uncertain','Sources: paired bootstrap analysis; discovery stability follow-up, 17 Sep 2026');
 text(s,'CatBoost versus logistic regression',64,169,1152,48,33,C.ink,true);
 bullets(s,['8 fewer misses among the same 169 rejection specimens.','Both make 8 false flags among 176 no-rejection specimens.','The 95% interval for the detection advantage includes zero.'],64,230,1152,150,31,C.ink,9);
 text(s,'Model choice across 20 development splits',64,412,1152,48,33,C.ink,true);
 table(s,[['CatBoost','Logistic regression'],['13 selections','7 selections']],{y:479,h:112,widths:[576,576],size:30});
 text(s,'The splits overlap. These counts describe variation in model choice.',64,620,1152,31,27);
}
// Shared implementation and failures that stop scoring.
{
 const s=slide('Training and prediction use the same preparation','Source: shared preprocessing and Predictor; application contract');
 bullets(s,['CSV input through the command line or web application.'],64,165,1152,60,33);
 const labels=['Read counts','Check names\nand numbers','Normalize\n758 inputs','Score with\nsaved model'];
 let prev;labels.forEach((v,i)=>{const n=node(s,v,64+i*298,253,256,130,{size:31});if(prev)connect(s,prev,n);prev=n;});
 bullets(s,['A valid request returns the specimen ID, model score, threshold, flag and model version.','Missing or duplicate measurements, negative counts or non-finite values stop scoring.'],64,439,1152,176,32,C.ink,22);
}
// The slide also works when the presenter uses the static fallback.
{
 const s=slide('One public specimen through the service','Source: public discovery-screen example and saved application checks');
 bullets(s,['GSM6510425: recorded no rejection.'],64,163,1152,61,34);
 table(s,[['Model score','Selected threshold','Rejection flag'],['0.274934','0.876588','False (below cutoff)']],{y:249,h:138,widths:[346,366,440],size:31});
 text(s,'Model: 20260915_shared:any_rejection:catboost_all_depth4',64,399,1152,34,24,C.muted);
 bullets(s,['The complete input produces a flag that agrees with the recorded diagnosis.','Removing IFNG clears the previous result and returns no new score.'],64,459,1152,127,30,C.ink,18);
 text(s,'“Missing required assay targets: IFNG”',94,592,1122,44,30,C.ink,true);
}
// Consistency, input failures, and the actual deployment status.
{
 const s=slide('The service reproduces all 345 saved scores','Source: local verification, 17 Sep 2026. Software consistency check.');
 bullets(s,['API, command line and saved evaluation agree within 10⁻¹².'],64,165,1152,62,33);
 table(s,[['Check','Observed behavior'],['Reordered columns','Same model score'],['Invalid or incomplete counts','No score'],['Incompatible model metadata','Model does not load']],{y:257,h:250,widths:[575,577],size:30});
 bullets(s,['94 tests passed, including these failure cases.','The local container was checked. Cloud deployment is deferred.'],64,546,1152,102,29,C.ink,13);
}
// Next evidence connects classification to the proposed clinical purpose.
{
 const s=slide('Testing the proposed use in ambiguous biopsies','Sources: project research context; primary analysis; Banff work plan (2024). Proposed evaluation.');
 bullets(s,['This project establishes classification performance in one deposited study.'],64,167,1152,85,32);
 table(s,[['Question','Proposed evaluation'],['Does performance hold in a new study?','New transplant biopsies with patient and center IDs and lab quality records.\nUse the chosen models and thresholds.'],['Does the score help with ambiguous biopsies?','Compare usual assessment with and without the molecular score.\nUse independent review and follow-up outcomes.']],{y:270,h:320,rowHeights:[54,140,126],widths:[427,725],size:28,padY:8});
}
// Results belong here, after the question and evidence.
{
 const s=slide('Molecular counts can classify recorded rejection','Public data: Zhang et al. (2024), GSE212160. Presentation prepared with AI assistance.',true);
 text(s,'CatBoost, 345 evaluation specimens',64,171,1152,43,31,C.white);
 text(s,'25 / 169 misses. 8 / 176 false flags.',64,219,1152,84,56,C.white,true);
 bullets(s,['Logistic regression remains a credible simpler alternative.','The project provides a reproducible classifier and a tested prediction service.','Next: test added value in ambiguous biopsies in a new study.'],64,355,1152,255,34,C.white,25);
}
// Backup material is outside the 20-minute plan.
assaySlide();
{
 const s=slide('Backup: complete primary comparison',analysis);
 const names=['CatBoost','Logistic','IFNG only','Constant'];
 table(s,[['Model','Misses','False flags','Sensitivity','Specificity','ROC-AUC'],...[cat,log,ifng,constant].map((m,i)=>[names[i],m.fn,m.fp,(+m.sensitivity*100).toFixed(1)+'%',(+m.specificity*100).toFixed(1)+'%',(+m.roc_auc).toFixed(3)])],{y:198,h:344,widths:[244,136,168,201,205,198],size:26});
 text(s,'Denominators: 169 rejection; 176 no rejection. Fixed thresholds per model.',64,575,1152,66,29);
}
{
 const s=slide('Backup: normalization and model settings','Sources: shared preprocessing; primary model configuration');
 text(s,'Normalized measurement = log₂(raw count + 1)\n− mean of the 12 housekeeping log₂(count + 1) values',64,169,1152,110,34,C.ink,true);
 table(s,[['Model','Additional preparation and settings'],['Logistic regression','Subtract each feature’s training mean, then divide by its training standard deviation. Reuse these values for later specimens.\nRegularization: C = 0.1.'],['CatBoost','No extra feature scaling.\n300 trees, depth 4, learning rate 0.04.']],{y:305,h:292,rowHeights:[54,142,96],widths:[300,852],size:28,padY:8});
}
{
 const s=slide('Backup: interpreting model scores','Source: reliability_bins.csv. The highlighted bin has a Wilson 95% interval. No recalibration fitted.');
 text(s,'CatBoost on 345 validation specimens',64,152,1152,41,30,C.ink,true);
 chart(s,'scatter',{position:{left:59,top:215,width:726,height:393},series:[{name:'Agreement',xValues:[0,1],values:[0,1],line:{fill:C.muted,width:1.4},marker:{symbol:'none'}},{name:'Observed bins',xValues:bins.map(x=>Number(Number(x.mean_score).toFixed(6))),values:bins.map(x=>Number(Number(x.observed_fraction).toFixed(6))),line:{fill:'none',width:0},marker:{symbol:'circle',size:9},fill:C.teal}],scatterOptions:{style:'lineWithMarkers'},hasLegend:false,xAxis:{min:0,max:1,majorUnit:.2,title:{text:'Mean model score',textStyle:axisText},textStyle:axisText,numberFormatCode:'0.0',majorGridlines:null},yAxis:{min:0,max:1,majorUnit:.2,title:{text:'Recorded rejection fraction',textStyle:axisText},textStyle:axisText,numberFormatCode:'0.0',majorGridlines:{fill:C.rule,width:1}},chartFill:C.bg,plotAreaFill:C.bg});
 text(s,'Score bin 0.8–0.9',837,226,379,50,31,C.ink,true);
 bullets(s,['Mean score: 0.847','Recorded rejection: 7 / 16','Observed fraction: 43.8%\n95% interval: 23.1–66.8%'],837,303,379,270,28,C.ink,20);
 text(s,'Diagonal: score equals observed rejection fraction',94,619,1122,31,24);
}
{
 const s=slide('Backup: rejection subtype follow-up','Source: subtype follow-up, 15 Sep 2026. Reuses the examined validation cohort; needs independent confirmation.');
 table(s,[['Model','Any-rejection misses','False flags'],['Binary CatBoost','25 / 169','8 / 176'],['Four-class CatBoost','29 / 169','8 / 176'],['Four-class logistic','28 / 169','10 / 176'],['Separate component models','24 / 169','15 / 176']],{y:200,h:325,widths:[532,342,278],size:28});
 bullets(s,['Four-class logistic recognized 10 / 18 mixed diagnoses, with 5 false mixed calls among 327 non-mixed specimens.'],64,555,1152,88,30);
}
{
 const s=slide('Backup: study, assay and deployment limits','Sources: Zhang et al. (2024), Methods and Tables 5–6; primary analysis; verification guide.');
 table(s,[['Question','Evidence and remaining limits'],['Patient / center separation?','Not documented. All specimens were processed at one laboratory.'],['Study population?','Includes 202 native-kidney controls.\nSelected ambiguous diagnoses were excluded.'],['Laboratory assay quality?','File checks were tested. Laboratory quality was not independently reassessed.'],['Individual probabilities?','Score calibration remains limited.'],['Cloud deployment?','Local container tested. Cloud work deferred.']],{y:179,h:453,rowHeights:[49,85,94,101,62,62],widths:[385,767],size:26,padY:7});
}
{
 const s=slide('Backup: sources and contributions','');
 text(s,'Public study',64,171,1152,44,32,C.ink,true);
 bullets(s,['Zhang et al., Laboratory Investigation (2024): GSE212160 raw NanoString B-HOT measurements.'],64,225,1152,91,32);
 text(s,'This project',64,351,1152,44,32,C.ink,true);
 bullets(s,['Binary model comparisons and runs produced here, shared preparation code, and a tested local prediction service.'],64,405,1152,99,32);
 text(s,'Presentation guidance',64,545,1152,43,30,C.ink,true);
 text(s,'Bourne (2007), Kosslyn et al. (2012), Garner and Alley (2013), Rougier et al. (2014)',64,595,1152,45,25);
}
{
 const s=slide('Backup: UNOS research connection','Source: UNOS, Using AI to identify kidney anatomy issues (2 Jun 2026)');
 bullets(s,['UNOS researchers studied anatomical issues in donor kidney photographs.','Labels came from records of transplantation or refusal because of anatomy concerns.','The intended use is to support clinical assessment and improve consistency.','The connection: use recorded assessments to develop additional evidence for specialists.'],64,178,1152,377,33,C.ink,21);
 text(s,'This is a different clinical task and does not validate our classifier.',94,590,1122,46,28);
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
