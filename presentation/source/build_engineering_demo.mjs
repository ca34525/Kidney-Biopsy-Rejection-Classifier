// Build one portable browser demonstration from preserved evidence and actual code.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const require = createRequire(path.join(root, 'build/presentation/runtime.mjs'));
const { marked } = await import(pathToFileURL(require.resolve('marked')).href);
const read = name => fs.readFile(path.join(root, name), 'utf8');
const esc = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const digest = value => crypto.createHash('sha256').update(value).digest('hex');
function csv(text) {
  const lines = text.trim().split(/\r?\n/); const columns = lines.shift().split(',');
  return lines.map(line => {
    // These selected numeric evidence files contain no quoted or multiline fields.
    if (line.includes('"')) throw new Error('Use a full CSV reader for quoted evidence');
    const cells = line.split(',');
    if (cells.length !== columns.length) throw new Error('CSV field count changed');
    return Object.fromEntries(columns.map((name, i) => [name, cells[i]]));
  });
}
const definitions = [
  ['primary','Primary analysis report','Complete model comparison, paired uncertainty, subtype errors and score reliability.','results/analysis/20260915_baseline/REPORT.md'],
  ['stability','Discovery-split follow-up','The 20 repeated training, screening and assessment partitions.','results/followup/20260917_stability/REPORT.md'],
  ['api','Application and API guide','Input requirements, commands, response fields and the public-specimen walkthrough.','docs/API.md'],
  ['verification','Software verification guide','Dated local, HTTP, container and hosted CI evidence.','docs/VERIFICATION.md'],
  ['code','Complete code guide','The research and prediction workflows, functions and checks.','docs/CODE_GUIDE.md'],
  ['methods','Methodology review','This project’s analytical choices and differences from the source study.','docs/METHODOLOGY_REVIEW.md'],
  ['http','Recorded HTTP agreement check','All 345 specimens, reordered columns, numeric tolerance and source hashes.','results/checks/20260917_coherence/http/http.json'],
  ['container','Recorded local container check','Successful research-model container verification, 17 September 2026.','results/checks/20260917_coherence/container.json'],
  ['errors','Errors by recorded diagnosis','Original CSV for the displayed subtype error table.','results/analysis/20260915_baseline/errors_by_diagnosis.csv'],
  ['selections','All 20 model selections','Original CSV with repetition seeds and selected candidates.','results/followup/20260917_stability/selections.csv'],
  ['split-design','Discovery follow-up design','The saved 630/210/210 partitioning and selection procedure.','results/followup/20260917_stability/design.json'],
  ['configuration','Serving-run configuration','Recorded settings for the fixed reproduction run.','results/reproduction/20260915_shared/configuration.json'],
  ['prediction-code','Prediction source','The actual Predictor implementation used by command line and service.','src/kidney_biopsy/prediction.py'],
  ['preprocessing-code','Preprocessing source','The shared count validation and normalization functions.','src/kidney_biopsy/preprocessing.py'],
  ['training-code','Training source','The reproducible research procedure and training-only learned transforms.','experiments/rejection_public/run.py'],
  ['http-code','HTTP verification source','The actual comparison of HTTP, command-line and preserved scores.','scripts/verify_http_service.py'],
  ['workflow','Automated-check workflow','Installed-package tests and the synthetic-container check.','.github/workflows/checks.yml'],
];
const references = {};
const referenceByPath = Object.fromEntries(definitions.map(([id,,,source]) => [source, id]));
for (const [id,title,description,source] of definitions) {
  const raw = await read(source);
  let html;
  if (source.endsWith('.md')) {
    html = marked.parse(raw).replace(/href="([^"]+)"/g, (whole, href) => {
      if (/^https?:\/\//.test(href)) return whole;
      const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(source), href.split('#')[0]));
      return referenceByPath[resolved] ? `href="#reference" data-ref="${referenceByPath[resolved]}"` : `data-source-path="${esc(resolved)}"`;
    }).replace(/<img[^>]*alt="([^"]*)"[^>]*>/g, (_, alt) => `<p class="small">Figure in original source: ${alt}</p>`);
  } else if (source.endsWith('.csv')) {
    const rows = csv(raw); const columns = Object.keys(rows[0]);
    html = `<h1>${esc(title)}</h1><table><thead><tr>${columns.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>`<td>${esc(row[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  } else html = `<h1>${esc(title)}</h1><pre>${esc(raw)}</pre>`;
  references[id] = {title,description,path:source,raw,html,sha256:digest(await fs.readFile(path.join(root, source)))};
}
const snapshot = JSON.parse(await read('presentation/source/demo_snapshot.json'));
const errors = csv(references.errors.raw);
const selections = csv(references.selections.raw);
const stability = JSON.parse(await read('results/followup/20260917_stability/summary.json'));
const http = JSON.parse(references.http.raw);
if (!http.successful || http.specimens !== 345 || selections.length !== 20) throw new Error('Unexpected evidence contract');
const families = selections.reduce((counts, row) => { counts[row.selected_family] = (counts[row.selected_family] || 0) + 1; return counts; }, {});
if (families.catboost !== stability.selection_counts.catboost || families.logistic !== stability.selection_counts.logistic) throw new Error('Selection counts disagree');
const predictionCode = references['prediction-code'].raw.match(/    def predict\(self, counts: pd\.DataFrame\) -> pd\.DataFrame:[\s\S]*?(?=\n    def predict_normalized)/)?.[0].trimEnd().split(/\r?\n/).filter(line=>/^        (?:normalized = |return self\.predict_normalized)/.test(line)).map(s=>s.slice(8)).join('\n');
const trainingCode = references['training-code'].raw.split(/\r?\n/).filter(line=>/^    features = normalize_counts/.test(line)).map(s=>s.slice(4)).join('\n');
const verificationCode = references['http-code'].raw.match(/                np\.testing\.assert_allclose\(\r?\n                    actual\.rejection_score, cli\.rejection_score, rtol=0, atol=1e-12\r?\n                \)/)?.[0].split(/\r?\n/).map(s=>s.slice(16)).join('\n');
if (!predictionCode || !verificationCode || !trainingCode) throw new Error('Code excerpt no longer matches actual source');
const label = {'Antibody-mediated Rejection':'Antibody-mediated rejection','T cell-mediated Rejection':'T-cell-mediated rejection','Mixed Rejection':'Mixed rejection','No Rejection':'No rejection'};
const diagnoses = Object.keys(label);
const errorRows = diagnoses.map(diagnosis => {
  const cat = errors.find(x=>x.histology===diagnosis&&x.model==='catboost_all_depth4');
  const log = errors.find(x=>x.histology===diagnosis&&x.model==='logistic_all');
  const cls = diagnosis==='No Rejection'?'flag':'miss';
  return `<tr${diagnosis==='T cell-mediated Rejection'?' class="emphasis"':''}><td>${label[diagnosis]}</td><td>${cls==='miss'?'Missed cases':'Incorrect flags'}</td><td class="num ${cls}">${cat.errors} / ${cat.n}</td><td class="num ${cls}">${log.errors} / ${log.n}</td></tr>`;
}).join('');
const selectionRows = selections.map(row=>`<tr><td>${row.repeat}</td><td>${row.seed}</td><td>${row.selected_family==='catboost'?'CatBoost':'Logistic regression'}</td><td>${esc(row.selected_model)}</td></tr>`).join('');
const norm = snapshot.walkthrough.normalization;
const pred = snapshot.valid_response.predictions[0];
const fullResponse = esc(JSON.stringify(snapshot.valid_response, null, 2));
const continuation = String.fromCharCode(96);
const requestExample = [
  'Invoke-RestMethod ' + continuation,
  '  -Uri http://127.0.0.1:8766/predict ' + continuation,
  "  -Method Post -ContentType 'text/csv' " + continuation,
  '  -InFile no-rejection.csv',
].join('\n');
const source = (id, text) => `<button class="quiet" data-ref="${id}">${text}</button>`;
const css = await read('presentation/source/engineering_demo.css');
const js = await read('presentation/source/engineering_demo.js');
const payload = JSON.stringify({snapshot,references}).replace(/</g,'\\u003c');
const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#16343E"><title>Research software · Kidney biopsy classifier</title><style>${css}</style></head>
<body><a class="skip" href="#main">Skip to demonstration</a><header><div class="topline"><div><p class="brand">Research software</p><p class="project">Kidney biopsy rejection classifier</p></div><div class="toplinks"><a href="speaking_script.html#demo-evidence">Speaking script</a><button class="quiet" id="reference-library">Reports and sources</button></div></div><nav class="stops" role="tablist" aria-label="Demonstration stops"><button id="tab-evidence" role="tab" aria-selected="true" aria-controls="evidence" data-stop="evidence"><span>01</span>Evidence</button><button id="tab-specimen" role="tab" aria-selected="false" aria-controls="specimen" data-stop="specimen" tabindex="-1"><span>02</span>Application</button><button id="tab-engineering" role="tab" aria-selected="false" aria-controls="engineering" data-stop="engineering" tabindex="-1"><span>03</span>Engineering</button></nav></header>
<main id="main">
<section id="evidence" role="tabpanel" aria-labelledby="tab-evidence"><h1>The evidence behind the score</h1><p class="lead">Inspect the saved analysis and the follow-up that tested how model choice changes with the discovery split.</p>
<div class="subtabs" role="tablist" aria-label="Evidence views"><button id="tab-errors" role="tab" aria-selected="true" aria-controls="errors-view">Errors by diagnosis</button><button id="tab-splits" role="tab" aria-selected="false" aria-controls="splits-view" tabindex="-1">Discovery splits</button></div>
<div id="errors-view" role="tabpanel" aria-labelledby="tab-errors"><div class="table-wrap"><table><thead><tr><th>Recorded diagnosis</th><th>Error counted</th><th>CatBoost</th><th>Logistic regression</th></tr></thead><tbody>${errorRows}</tbody></table></div><p class="note">Most missed cases were recorded as T-cell-mediated rejection: 18 for CatBoost and 25 for logistic regression.</p><p class="small">Counts describe the same 345 technical-validation specimens. The mixed-rejection group has only 18 specimens, so its rates are particularly uncertain.</p><div class="action-row">${source('primary','Read the full primary analysis')}${source('errors','Inspect the source CSV')}</div></div>
<div id="splits-view" role="tabpanel" aria-labelledby="tab-splits" hidden><p class="split-count">CatBoost selected ${families.catboost} times · Logistic selected ${families.logistic} times</p><ol class="flow"><li><h3>Training</h3><span class="count">630</span><p>Fit both model families on the same specimens.</p></li><li><h3>Screening</h3><span class="count">210</span><p>Choose model settings, threshold and family.</p></li><li><h3>Held-out assessment</h3><span class="count">210</span><p>Check the selected fitted model and threshold.</p></li></ol><p class="small">All three partitions come from the 1,050-specimen discovery cohort. The 345-specimen author validation cohort is unused. The 20 repetitions overlap.</p><details class="records"><summary>Inspect all 20 selections</summary><div class="table-wrap records-body"><table><thead><tr><th>Repetition</th><th>Seed</th><th>Selected family</th><th>Selected candidate</th></tr></thead><tbody>${selectionRows}</tbody></table></div></details><p class="note">On held-out assessment, CatBoost missed fewer cases in 9 repetitions, logistic in 10, with 1 tie. Selection frequency does not establish a dependable performance advantage.</p><div class="action-row">${source('stability','Read the complete follow-up')}${source('split-design','Inspect the saved design')}</div></div>
<p class="source">Saved primary analysis: 15 Sep 2026. Discovery follow-up: 17 Sep 2026. Score reliability and paired uncertainty remain in the full primary report.</p></section>
<section id="specimen" role="tabpanel" aria-labelledby="tab-specimen" hidden><div class="section-head"><div><h1>One specimen through the application</h1><p class="lead">Submit compatible RNA counts, inspect the score, then try a missing target.</p></div></div><div class="mode-bar"><p class="status saved" id="application-mode" role="status">Saved example responses</p><button class="quiet" id="toggle-mode">Check live service</button></div>
<iframe id="live-app" class="app-frame" title="Live kidney biopsy scoring application" hidden></iframe>
<div id="saved-application" class="saved-demo"><p class="small">Actual responses captured ${esc(snapshot.captured_utc.slice(0,10))} from the project’s application and frozen model. These controls display saved results.</p><div class="saved-controls"><button class="button" data-saved-case="valid">Show saved complete input</button><button class="button secondary" data-saved-case="invalid">Show saved missing IFNG</button></div><p id="saved-case-status" class="status" aria-live="polite">Saved complete-input response</p>
<div id="saved-valid"><h2>${pred.specimen}</h2><p>Public discovery-screen specimen · Recorded no rejection</p><dl class="result-values"><div><dt>Model score</dt><dd>${pred.rejection_score.toFixed(6)}</dd></div><div><dt>Frozen threshold</dt><dd>${pred.threshold.toFixed(6)}</dd></div><div><dt>Rejection flag</dt><dd>False</dd></div></dl><p class="calculation-note">IFNG example: ${norm.raw_count} counts → ${norm.log2_count_plus_one.toFixed(3)} after log₂(count + 1). Subtract the reference mean ${norm.housekeeping_mean.toFixed(3)} to obtain ${norm.normalized_value.toFixed(3)}.</p><p class="small">The same operation produces all 758 model inputs. The recorded diagnosis stays separate from the predictors.</p></div>
<div id="saved-invalid" hidden><div class="error"><h2>No score returned</h2><p><strong>${esc(snapshot.invalid_response.error.message)}</strong></p><p>The incomplete batch fails validation. The service returns HTTP ${snapshot.invalid_status} and an explanation.</p></div></div><p class="source">Model: ${esc(snapshot.model_version)}</p><details class="records"><summary>Start the live demonstration</summary><p>Run this command from the project root, then open the local page below.</p><pre>uv run --frozen python presentation/source/serve_demo.py</pre><p><a href="http://127.0.0.1:8766/presentation/engineering_demo.html#specimen">Open the live engineering demonstration</a></p><p class="small">The existing research app remains available at the server’s root URL.</p></details></div></section>
<section id="engineering" role="tabpanel" aria-labelledby="tab-engineering" hidden><h1>The calculation, interface and checks</h1><p class="lead">The service makes the evaluated procedure available to a user and to other software.</p><div class="subtabs" role="tablist" aria-label="Engineering views"><button id="tab-shared" role="tab" aria-selected="true" aria-controls="shared-view">Shared calculation</button><button id="tab-interface" role="tab" aria-selected="false" aria-controls="interface-view" tabindex="-1">API request and response</button><button id="tab-checks" role="tab" aria-selected="false" aria-controls="checks-view" tabindex="-1">Verification and handoff</button></div>
<div id="shared-view" role="tabpanel" aria-labelledby="tab-shared"><ol class="flow"><li><h3>Check the counts</h3><p>Require the correct targets and finite, nonnegative values.</p></li><li><h3>Normalize each specimen</h3><p>Use the 12 housekeeping targets to prepare the 758 model inputs.</p></li><li><h3>Score and flag</h3><p>Apply the saved model, then its frozen threshold.</p></li></ol><div class="code-columns"><div class="code-block"><p class="code-label">Training calls the shared normalization function</p><pre>${esc(trainingCode)}</pre>${source('training-code','Inspect the training source')}</div><div class="code-block"><p class="code-label">The service and command line use Predictor.predict</p><pre>${esc(predictionCode)}</pre>${source('prediction-code','Inspect the prediction source')}</div></div><p class="small">Normalization uses only the specimen’s counts. Learned scaling and feature selection are fitted on training data and preserved with the fitted model.</p><div class="action-row">${source('preprocessing-code','Inspect shared preprocessing')}${source('code','Read the complete code guide')}</div></div>
<div id="interface-view" role="tabpanel" aria-labelledby="tab-interface" hidden><p>Another program sends the same CSV to <code>POST /predict</code> and receives a structured result.</p><div class="code-columns"><div class="code-block"><p class="code-label">Request · one specimen and all 770 counts</p><pre>${esc(requestExample)}</pre><button class="quiet" id="download-example">Download this exact public input</button><p class="small">CSV includes the specimen ID and measurements. It excludes the recorded diagnosis.</p><p class="code-label">Invalid input · HTTP 422</p><pre>${esc(JSON.stringify(snapshot.invalid_response,null,2))}</pre></div><div class="code-block"><p class="code-label">Actual saved response · HTTP 200</p><pre>${fullResponse}</pre></div></div><p class="small">The score, threshold and flag are separate fields. The model and schema versions identify the calculation and expected input format.</p>${source('api','Read the API contract')}</div>
<div id="checks-view" role="tabpanel" aria-labelledby="tab-checks" hidden><p class="verification-count">${http.specimens} <span>validation specimens checked across three routes</span></p><p>Saved research results, command-line predictions and HTTP responses had matching flags. Scores agreed within 10⁻¹², including reordered measurement columns.</p><div class="code-columns"><div><p class="code-label">Actual comparison in the HTTP verification script</p><pre>${esc(verificationCode)}</pre><p class="small">Recorded 17 Sep 2026. Maximum HTTP-to-saved score difference: ${http.max_http_saved_score_difference.toExponential(2)}. This checks software consistency.</p>${source('http','Inspect the recorded check')}</div><div><table class="check-table"><thead><tr><th>Failure checked</th><th>Expected behavior</th></tr></thead><tbody><tr><td>Missing or duplicate measurements</td><td>No scores for the batch</td></tr><tr><td>Incompatible model metadata</td><td>Model does not load</td></tr></tbody></table>${source('http-code','Inspect the verification source')}</div></div><details class="records" open><summary>What another developer receives</summary><table class="check-table"><tbody><tr><td>Locked environment and run commands</td><td>Install dependencies, reproduce the analysis and serve the saved model.</td></tr><tr><td>Automated checks on code changes</td><td>Tests and a synthetic-container check in the saved CI workflow.</td></tr><tr><td>Tested local research container</td><td>Actual model, valid and invalid requests checked on 17 Sep 2026.</td></tr></tbody></table><p class="small">Hosted CI passed for an earlier revision. The cited application and research-container checks were local. Cloud deployment remains future work.</p></details><div class="action-row">${source('verification','Read the verification guide')}${source('workflow','Inspect the automated checks')}${source('container','Inspect the local container record')}</div></div></section>
<footer class="footer-nav"><button id="previous-stop">Previous stop</button><p id="stop-position">1 of 3</p><button id="next-stop">Next: application</button></footer></main>
<dialog class="ref-dialog" id="reference-dialog" aria-label="Reports and source material"><div class="ref-toolbar"><button class="quiet" id="all-references">All reports and sources</button><button class="button secondary" id="close-reference">Close</button></div><div class="ref-body" id="reference-body"></div></dialog><script type="application/json" id="demo-data">${payload}</script><script>${js}</script></body></html>`;
await fs.writeFile(path.join(root,'presentation/engineering_demo.html'),html);
const inputs = ['presentation/source/demo_snapshot.json','results/followup/20260917_stability/summary.json',...definitions.map(x=>x[3])];
const hashes = Object.fromEntries(await Promise.all(inputs.map(async name=>[name,digest(await fs.readFile(path.join(root,name)))])));
await fs.writeFile(path.join(root,'presentation/engineering_demo_sources.json'),JSON.stringify({built:'2026-09-22',model_version:snapshot.model_version,sources:hashes,output_sha256:digest(html)},null,2)+'\n');
console.log(JSON.stringify({output:'presentation/engineering_demo.html',bytes:Buffer.byteLength(html),references:Object.keys(references).length,model_version:snapshot.model_version}));
