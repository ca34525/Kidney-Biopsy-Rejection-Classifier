import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { addTechnicalSlides } from './technical_slides.mjs';

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
const CODE_FONT = resolvePresentationFont({ fontFamily: 'Consolas' });
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
const screening=(await csv('results/reproduction/baseline/biopsy_screen.csv')).filter(x=>x.target==='any_rejection');
const screenCat=screening.find(x=>x.model===cat.model);
const screenLog=screening.find(x=>x.model===log.model);
const bins=(await csv('results/analysis/20260915_baseline/reliability_bins.csv')).filter(x=>x.model===cat.model);
const stability=JSON.parse(await fs.readFile(path.join(root,'results/followup/20260917_stability/summary.json'),'utf8'));
const recallDifference=(await csv('results/analysis/20260915_baseline/paired_differences.csv')).find(row=>row.model===cat.model && row.minus_model===log.model && row.metric==='sensitivity');
const modelLabels={ifng:'IFNG only\n(Logistic regression)',logistic:'All RNA\n(Logistic Regression)'};
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
 definition(s,'Rejection: ','The recipient’s immune system attacks the donated kidney.',177,{h:60});
 definition(s,'Kidney biopsy: ','A small tissue sample collected from the kidney for examination.',257,{h:93});
 definition(s,'Histology: ','A microscopic examination that reveals injury and inflammation, which can support a rejection diagnosis.',377,{nested:true,h:92});
 definition(s,'Molecular measurements: ','Counts of selected RNA types that reflect gene activity in the mix of cells in the tissue.',493,{nested:true,h:116});
}
// Practical motivation followed by equally prominent analysis and software aims.
{
 const s=slide('Purpose of this project','Clinical rationale: Zhang et al. (2024), Discussion, p. 13; KDIGO (2009).');
 text(s,'Whether rejection is present can affect decisions about further treatment to suppress the immune system.',64,164,1152,80,31,C.teal);
 text(s,'Model comparison',64,271,1152,47,33,C.ink,true);
 text(s,'How do logistic regression and CatBoost compare in classifying any recorded rejection versus no rejection from B-HOT biopsy RNA, particularly in missed cases and incorrect flags?',64,320,1152,128,30);
 text(s,'Software engineering',64,468,1152,47,33,C.ink,true);
 text(s,'Make preprocessing, training and evaluation reproducible. Build a tested scoring service and prototype application that let a user submit a specimen’s RNA counts and inspect its model score, threshold and rejection flag.',64,517,1152,126,30);
}
{
 const s=slide('Clinical and research context','Sources: Banff Reference Guide (2026); Zhang et al. (2024); KDIGO (2009), recommendation 6.1');
 text(s,'Banff diagnostic\nframework',64,170,274,90,29,C.ink,true);
 text(s,'Validated biopsy transcript tests have a defined role\nin antibody-mediated rejection assessment.',365,170,851,90,30);
 line(s,64,282,1152);
 text(s,'Published B-HOT study\nZhang, 2024',64,310,274,90,29,C.ink,true);
 text(s,'Four-class study compared regression and boosting.\nSelected LASSO for similar accuracy with fewer features.',365,300,851,113,30);
 line(s,64,433,1152);
 text(s,'Biopsy and\ntreatment',64,455,274,103,29,C.ink,true);
 text(s,'KDIGO recommends biopsy before treating acute rejection,\nunless waiting would substantially delay treatment.',365,448,851,151,30);
}
datasetSlide();
// Give the biological labels their own visual explanation.
{
 const s=slide('Outcome: rejection versus no rejection','Sources: Zhang et al. (2024), Tables 5–6 and Discussion, p. 11; project diagnosis mapping');
 text(s,'The model combines the three rejection categories in the public dataset.',64,166,1152,70,32,C.teal);
 table(s,[['Recorded diagnosis','Meaning','Model label'],['Antibody-mediated rejection','Antibodies: immune proteins','Rejection'],['T-cell-mediated rejection','T cells: immune cells','Rejection'],['Mixed rejection','Both rejection processes','Rejection'],['No rejection','No recorded rejection','No rejection']],{y:255,h:325,widths:[485,407,260],size:28});
 text(s,'The authors excluded some diagnostic categories from the dataset.',64,598,1152,44,26,C.muted);
}
// Define the laboratory vocabulary in the order it is used.
function assaySlide(){
 const s=slide('Backup: measuring biopsy RNA with NanoString nCounter','Sources: Zhang et al. (2024), Methods; Bruker nCounter documentation; GSE212160');
 bullets(s,[
  'RNA includes messages cells make when genes are active.',
  'An assay is a laboratory test. B-HOT is the fixed panel of RNA types measured in the public dataset.',
  'The laboratory extracts RNA from preserved tissue. Probes recognize selected RNAs, and NanoString nCounter counts their identifying barcodes.'
 ],64,179,1152,372,34,C.ink,22);
 text(s,'Example: IFNG count = 4 in one public specimen',94,548,1122,58,34,C.ink,true);
}
// Separate what is measured from what is predicted.
{
 const s=slide('The measurements used to build the features','Sources: GSE212160; B-HOT panel consensus; NanoString analysis guidance; shared preprocessing');
 text(s,'770 RNA counts per specimen, one for each RNA type measured.',64,170,1152,81,34,C.teal);
 text(s,'758',64,269,535,70,64,C.ink,true);
 text(s,'Model measurements',64,351,535,49,34,C.ink,true);
 bullets(s,['Selected human and viral RNA measurements.','Signals reflect gene activity and the mixture of cells in the biopsy.','Normalized values become the model’s inputs.'],64,410,540,234,29,C.ink,10);
 text(s,'12',687,269,529,70,64,C.ink,true);
 text(s,'Housekeeping references',687,351,529,49,34,C.ink,true);
 bullets(s,['Relatively stable RNAs provide a reference for each specimen.','Help adjust for differences in overall measurable RNA input.','Used for normalization, then excluded from the model.'],687,410,529,234,29,C.ink,10);
}
// Explain the identifier by showing what it joins.
function datasetSlide(){
 const s=slide('What the dataset contains','Sources: GSE212160; Zhang et al. (2024), Methods and Tables 5–6; project data reader');
 text(s,'1,395 biopsy specimens, with one row per specimen in each table.',64,165,1152,81,33,C.teal);
 text(s,'RNA counts',64,246,502,47,34,C.ink,true);
 text(s,'Specimen information',716,246,500,47,34,C.ink,true);
 table(s,[['Column','Example'],['Specimen ID (key)','GSM6510425'],['IFNG','4'],['GUSB (reference)','260'],['Other RNA counts','…']],{x:64,y:314,w:502,h:239,widths:[265,237],size:25,padY:6});
 table(s,[['Column','Example'],['Specimen ID (key)','GSM6510425'],['Recorded diagnosis','No rejection'],['Study group','Discovery'],['Other details','…']],{x:716,y:314,w:500,h:239,widths:[270,230],size:25,padY:6});
 line(s,566,386,150,C.muted);
 text(s,'1 : 1',574,344,134,34,25,C.ink,true,'center');
 text(s,'Same ID',574,394,134,35,24,C.ink,false,'center');
 bullets(s,['Includes 1,193 transplant biopsies and 202 native-kidney controls.','The study does not document separation by patient or referring center between study groups.'],64,574,1152,76,25,C.ink,8);
}
// One concrete example, with the reason for each preparation step.
{
 const s=slide('Preparing counts for the model','Source: shared preprocessing; public specimen GSM6510425. Values rounded for display.');
 table(s,[['For each of the 758 RNA counts','IFNG example'],['1. Start with the raw count','4'],['2. Calculate log₂(count + 1)','2.322'],['3. Average log₂(count + 1) for the 12 reference RNAs','7.900'],['4. Subtract that reference','2.322 − 7.900 = −5.578']],{y:183,h:333,widths:[806,346],size:29});
}
// Cohort names and their jobs, before discussing model choices.
{
 const s=slide('Development and evaluation specimens','Sources: Zhang et al. (2024), Methods; saved project split, seed 20260915');
 bullets(s,['I used the authors’ two study groups: discovery and validation cohorts.','My training / screening split kept diagnosis proportions similar.'],64,166,1152,126,31,C.ink,13);
 const disc=node(s,'Discovery Cohort\n1,050 specimens',64,322,699,103,{size:33});
 const train=node(s,'Training: 787\nFit the models',64,496,316,110,{size:31});
 const screen=node(s,'Screening: 263\nChoose model and threshold',430,496,333,110,{size:29});
 connect(s,disc,train,'bottom','top');connect(s,disc,screen,'bottom','top');
 node(s,'Validation Cohort\n345 specimens\n\nEvaluate the selected\nmodel and threshold',820,322,396,284,{fill:C.ink,color:C.white,size:30});
}
// Model names now come with an explanation.
{
 const s=slide('Models compared','Sources: primary configuration and analysis; Zhang et al., Table S2; CatBoost documentation');
 text(s,'Each model produces a score for rejection versus no rejection.',64,165,1152,75,33,C.teal);
 table(s,[['Model','Approach and rationale'],['Constant baseline','One score: the training rejection fraction'],[modelLabels.ifng,'One immune-related RNA measurement\nas a simple benchmark'],[modelLabels.logistic,'A weighted combination of 758 measurements.\nRegularization limits the size of the weights.'],['CatBoost','Can capture nonlinear RNA patterns and interactions.\nShallow trees help limit overfitting.']],{y:250,h:388,rowHeights:[50,60,86,96,96],widths:[354,798],size:29});
}
// Define the decision and error vocabulary before reporting results.
{
 const s=slide('Selecting the model and threshold','Reference: recorded biopsy diagnoses. Source: saved discovery screening results, 15 Sep 2026');
 text(s,'Recall',64,155,544,43,35,C.orange,true);
 text(s,'Correctly flagged rejection cases',64,204,544,43,28,C.ink,false,'center');
 line(s,76,252,520,C.ink);
 text(s,'All cases diagnosed as rejection',64,261,544,43,28,C.ink,false,'center');
 text(s,'(False negatives are missed cases.)',64,313,544,43,27,C.orange);
 text(s,'Precision',704,155,512,43,35,C.teal,true);
 text(s,'Correctly flagged rejection cases',704,204,512,43,28,C.ink,false,'center');
 line(s,716,252,488,C.ink);
 text(s,'All rejection flags',704,261,512,43,28,C.ink,false,'center');
 text(s,'(False positives are incorrect flags.)',704,313,512,43,27,C.teal);
 text(s,'Screening rule: detect at least 90% of recorded rejection cases,\nthen minimize false positives. ROC-AUC breaks ties.',64,373,1152,73,28,C.ink,true);
 table(s,[['Screening result','CatBoost','All-RNA logistic'],['Rejection detected',`${screenCat.tp} / ${screenCat.positives}`,`${screenLog.tp} / ${screenLog.positives}`],['False positives',`${screenCat.fp} / ${+screenCat.n-screenCat.positives}`,`${screenLog.fp} / ${+screenLog.n-screenLog.positives}`]],{y:464,h:126,rowHeights:[42,42,42],widths:[500,326,326],size:27,padY:3});
 text(s,'One fewer false positive selected CatBoost.\nThe model and threshold then stayed fixed for evaluation.',64,601,1152,48,25);
}
// Editable data and explicit denominators.
{
 const s=slide('Validation results','Sources: primary evaluation (15 Sep) and discovery-only stability follow-up (17 Sep 2026).');
 text(s,'Same 345 specimens: 169 rejection and 176 no rejection',64,145,1152,48,32);
 // Single-line categories let chart viewers reserve the full label width.
 chart(s,'bar',{position:{left:56,top:202,width:1170,height:290},categories:[modelLabels.ifng.replace('\n',' '),modelLabels.logistic.replace('\n',' '),'CatBoost'],series:[{name:'Missed cases / 169',values:[+ifng.fn,+log.fn,+cat.fn],fill:C.orange},{name:'Incorrect flags / 176',values:[+ifng.fp,+log.fp,+cat.fp],fill:C.teal}],barOptions:{direction:'bar',grouping:'clustered',gapWidth:95},hasLegend:false,xAxis:{textStyle:axisText,majorGridlines:null},yAxis:{min:0,max:80,majorUnit:20,textStyle:axisText,majorGridlines:{fill:C.rule,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:labelText},chartFill:C.bg,plotAreaFill:C.bg});
 // Explicit editable keys preserve top-to-bottom bar order across slide viewers.
 for (const [label,color,x,width] of [['Incorrect flags / 176',C.teal,402,244],['Missed cases / 169',C.orange,656,250]]) {
  s.shapes.add({geometry:'rect',position:{left:x,top:505,width:10,height:10},fill:color,line:{fill:'none',width:0}});
  text(s,label,x+16,490,width,40,25);
 }
 bullets(s,[`Constant baseline: ${constant.fn} missed cases, ${constant.fp} incorrect flags. It flags everyone.`],64,546,1152,60,29,C.ink,11);
 // Use the same teal emphasis as the deck's other summary statements.
 text(s,`Across ${stability.repetitions} discovery splits: CatBoost selected ${stability.selection_counts.catboost} times, logistic ${stability.selection_counts.logistic}.`,64,614,1152,35,25,C.teal,true);
}
// The browser demonstration sits between one transition and the closing slide.
await addTechnicalSlides({root,slide,text,bullets,table,line,node,connect,C,codeFont:CODE_FONT});

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
const result=await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:process.env.RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[...new Set(nativeTables)].flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:[...new Set(nativeTables)],requiredNativeChartOwnerSlides:[...new Set(nativeCharts)],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT,CODE_FONT]},verifyArtifactToolImport:true,receiptPath:path.join(build,`${path.basename(finalPath)}.${Date.now()}.validation.json`)});
console.log(JSON.stringify(result));
