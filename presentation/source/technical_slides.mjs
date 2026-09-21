import fs from 'node:fs/promises';
import path from 'node:path';

// Technical section only. The established first twelve slides remain in build_deck.mjs.
export async function addTechnicalSlides({ root, slide, text, bullets, table, line, node, connect, C, codeFont }) {
  const sourceText = await fs.readFile(path.join(root, 'src/kidney_biopsy/prediction.py'), 'utf8');
  const predictorCode = sourceText.match(/    def predict\(self, counts: pd\.DataFrame\) -> pd\.DataFrame:[\s\S]*?(?=\n    def predict_normalized)/)?.[0].trimEnd();
  if (!predictorCode) throw new Error('Prediction excerpt no longer matches its source');
  const predictionExcerpt = predictorCode.split('\n').map(s => s.slice(4)).join('\n');
  const verifierText = await fs.readFile(path.join(root, 'scripts/verify_http_service.py'), 'utf8');
  const verifierCode = verifierText.match(/                np\.testing\.assert_allclose\(\r?\n                    actual\.rejection_score, cli\.rejection_score, rtol=0, atol=1e-12\r?\n                \)/)?.[0];
  if (!verifierCode) throw new Error('Verification excerpt no longer matches its source');
  const verificationExcerpt = verifierCode.split(/\r?\n/).map(s => s.slice(16)).join('\n');
  const code = (s, value, x, y, w, h, size=25) => {
    const shape = text(s, value, x, y, w, h, size);
    shape.text.style = {typeface:codeFont,fontSize:size,color:C.ink,autoFit:'none',verticalAlignment:'middle',wrap:false};
    return shape;
  };

  // Live report stop: the report itself supplies the evidence on screen.
  {
    const s=slide('Inspecting the analysis report','Source: saved primary analysis, 15 Sep 2026');
    text(s,'Saved analysis for another analyst to inspect',64,187,1152,70,39,C.ink,true);
    bullets(s,['Full model comparisons','Errors by recorded diagnosis','Score reliability and uncertainty'],64,304,1152,212,35,C.ink,25);
    text(s,'Live walkthrough of the preserved report',94,566,1122,54,30,C.teal);
  }
  // This holding slide also supports the existing captured-demo fallback.
  {
    const s=slide('One public specimen through the service','Source: public discovery-screen example and saved application checks');
    bullets(s,['GSM6510425: recorded no rejection.'],64,163,1152,61,34);
    table(s,[['Model score','Selected threshold','Rejection flag'],['0.274934','0.876588','False (below cutoff)']],{y:249,h:138,widths:[346,366,440],size:31});
    text(s,'Model: 20260915_shared:any_rejection:catboost_all_depth4',64,399,1152,34,24,C.muted);
    bullets(s,['The complete input produces a flag that agrees with the recorded diagnosis.','Removing IFNG clears the previous result and returns no new score.'],64,459,1152,127,30,C.ink,18);
    text(s,'“Missing required assay targets: IFNG”',94,592,1122,44,30,C.ink,true);
  }
  {
    const s=slide('Shared preparation and scoring','Sources: prediction.py, Predictor.predict; shared preprocessing; training workflow');
    text(s,'The analysis and application use the same preparation code.',64,161,1152,62,33,C.ink,true);
    const raw=node(s,'Raw RNA counts',64,252,330,78,{size:29});
    const normalized=node(s,'Check and normalize',473,252,334,78,{size:29});
    const score=node(s,'Saved model and threshold',886,252,330,78,{size:28});
    connect(s,raw,normalized);connect(s,normalized,score);
    text(s,'Application entry point',64,368,1152,40,28,C.teal,true);
    code(s,predictionExcerpt,64,425,1152,140,24);
    text(s,'The web page and command line both use this prediction path.',64,590,1152,52,29);
  }
  {
    const s=slide('An interface other software can call','Source: implemented POST /predict contract and public demonstration response');
    text(s,'API: a documented way for software to send data and receive results.',64,161,1152,67,32);
    const input=node(s,'CSV\nSpecimen ID + 770 counts',64,265,438,112,{size:29});
    const request=node(s,'POST /predict',598,277,272,88,{size:29});
    const output=node(s,'JSON\nPrediction results',966,265,250,112,{size:27});
    connect(s,input,request);connect(s,request,output);
    text(s,'Each result identifies the calculation',64,421,1152,44,31,C.ink,true);
    table(s,[['Specimen','Score','Threshold','Flag'],['GSM6510425','0.274934','0.876588','False']],{y:487,h:111,rowHeights:[55,56],widths:[372,250,280,250],size:27,padY:7});
    text(s,'Each result includes versions for the model and expected input format.',64,614,1152,33,27);
  }
  {
    const s=slide('Checking the application against the analysis','Source: real HTTP verification and application tests, 17 Sep 2026');
    text(s,'All 345 validation specimens',64,160,1152,58,39,C.ink,true);
    text(s,'Saved results, command line and HTTP service had matching flags.\nScores agreed within 10⁻¹², including reordered measurement columns.',64,226,1152,90,30);
    text(s,'Example check: HTTP scores versus command-line scores',64,327,1152,34,25,C.teal,true);
    code(s,verificationExcerpt,64,364,1152,87,24);
    table(s,[['Failure checked','Expected response'],['Missing or duplicate measurements','No scores for the batch'],['Incompatible model metadata','Model does not load']],{y:472,h:161,rowHeights:[51,55,55],widths:[630,522],size:26,padY:6});
  }
  {
    const s=slide('Running and maintaining the application','Sources: setup guide, automated-check workflow and dated verification records');
    table(s,[['What another developer receives','Why it helps'],['Locked environment and run instructions','Install the recorded dependencies and start the service.'],['Automated checks on code changes','Catch changes that break scoring or input handling.'],['Tested local container','Run the packaged application with its saved model.']],{y:183,h:328,rowHeights:[58,90,90,90],widths:[587,565],size:28,padY:8});
    text(s,'Hosted checks passed for an earlier revision.\nThe current application and research container were checked locally.',64,548,1152,76,28);
    text(s,'Cloud deployment remains future work.',64,632,1152,25,23,C.muted);
  }
  {
    const s=slide('What this project accomplished','Public data: Zhang et al. (2024), GSE212160. Development and presentation used AI assistance.',true);
    text(s,'A reproducible model comparison',64,180,1152,54,37,C.white,true);
    text(s,'Combined measurements reduced false flags, with a tradeoff in missed cases.\nThe practical advantage over logistic regression remains uncertain.',64,249,1152,101,31,C.white);
    line(s,64,383,1152,'#78949B');
    text(s,'Working software that preserves the calculation',64,417,1152,53,36,C.white,true);
    text(s,'A versioned score, clear input errors and checks against the saved results.',64,489,1152,74,32,C.white);
    text(s,'Added value for uncertain biopsies still needs direct evaluation.',64,591,1152,48,28,C.white);
  }
}
