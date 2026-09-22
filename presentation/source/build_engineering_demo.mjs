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
  ['prediction-tests','Input and model compatibility tests','Consequential input failures, shared prediction and incompatible model metadata.','tests/test_shared_prediction.py'],
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
const design = JSON.parse(references['split-design'].raw);
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
const pred = snapshot.valid_response.predictions[0];
const input = csv(snapshot.valid_csv)[0];
const previewColumns = ['specimen', 'AICDA', 'MYD88', 'IFNG', 'ABCF1', 'G6PD'];
if (Object.keys(input).length !== 771 || previewColumns.some(name => !(name in input))) throw new Error('Unexpected public CSV schema');
const csvPreview = [previewColumns.join(','), previewColumns.map(name => input[name]).join(',')].join('\n');
const assessmentComparison = stability.assessment_error_comparisons;
const fullResponse = esc(JSON.stringify(snapshot.valid_response, null, 2));
const requestExample = [
  'curl http://127.0.0.1:8766/predict \\',
  "  -H 'Content-Type: text/csv' \\",
  '  --data-binary @no-rejection.csv',
].join('\n');
const source = (id, text) => `<button class="quiet" data-ref="${id}">${text}</button>`;
const css = await read('presentation/source/engineering_demo.css');
const js = await read('presentation/source/engineering_demo.js');
const payload = JSON.stringify({snapshot,references}).replace(/</g,'\\u003c');
const html = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#16343E"><title>Software Engineering · Kidney biopsy classifier</title><style>${css}</style></head>
<body>
<a class="skip" href="#main">Demonstration content</a>
<header>
  <div class="topline"><div><p class="brand">Software Engineering</p><p class="project">Kidney biopsy rejection classifier</p></div><button class="quiet" id="reference-library">Reports and sources</button></div>
  <nav class="stops" role="tablist" aria-label="Demonstration sections">
    <button id="tab-evidence" role="tab" aria-selected="true" aria-controls="evidence" data-stop="evidence"><span>01</span>Model comparison</button>
    <button id="tab-specimen" role="tab" aria-selected="false" aria-controls="specimen" data-stop="specimen" tabindex="-1"><span>02</span>Application</button>
    <button id="tab-engineering" role="tab" aria-selected="false" aria-controls="engineering" data-stop="engineering" tabindex="-1"><span>03</span>Engineering</button>
  </nav>
</header>
<main id="main" tabindex="-1">
<section id="evidence" role="tabpanel" aria-labelledby="tab-evidence">
  <h1>Model comparison results</h1>
  <p class="lead">The original evaluation describes errors by recorded diagnosis. A separate follow-up examines how the choice between CatBoost and logistic regression changes with the discovery split.</p>
  <div class="subtabs" role="tablist" aria-label="Model comparison views">
    <button id="tab-errors" role="tab" aria-selected="true" aria-controls="errors-view">Validation errors by diagnosis</button>
    <button id="tab-splits" role="tab" aria-selected="false" aria-controls="splits-view" tabindex="-1">Model choice across repeated splits</button>
  </div>
  <div id="errors-view" role="tabpanel" aria-labelledby="tab-errors">
    <p>Both models were evaluated on the same <strong>345 specimens from the authors’ technical-validation cohort</strong>, after their models and thresholds were fixed using discovery data.</p>
    <p>The task is any recorded rejection versus no rejection. Each fraction below is the number of errors divided by the number of specimens with that recorded diagnosis.</p>
    <div class="table-wrap"><table>
      <caption>Errors in the authors’ technical-validation cohort</caption>
      <thead><tr><th scope="col">Recorded diagnosis</th><th scope="col">Error counted</th><th scope="col">CatBoost</th><th scope="col">Logistic regression</th></tr></thead>
      <tbody>${errorRows}</tbody>
    </table></div>
    <p class="note">Most missed rejection cases had a recorded T-cell-mediated diagnosis: 18 for CatBoost and 25 for logistic regression.</p>
    <p>The mixed-rejection group contains only 18 specimens, so its error rates are particularly uncertain.</p>
    <p>The cohort includes 334 transplant biopsies and 11 native-kidney controls. These counts describe that combined population.</p>
    <div class="action-row">${source('primary','Primary analysis report')}${source('errors','Diagnosis error counts (CSV)')}</div>
  </div>
  <div id="splits-view" role="tabpanel" aria-labelledby="tab-splits" hidden>
    <h2>How the discovery specimens were reassigned</h2>
    <p>This follow-up examined whether the preferred model family changed when the discovery specimens were assigned differently to training, screening and assessment.</p>
    <p>Each of <strong>${selections.length} repetitions</strong> randomly divided the same <strong>1,050 discovery specimens</strong>, using a recorded random seed. Both splitting steps were stratified by the four recorded diagnoses: no rejection, antibody-mediated, T-cell-mediated and mixed rejection. This preserved approximately their proportions in each group.</p>
    <p>The procedure first set aside 210 assessment specimens, then selected 210 screening specimens from the remaining 840, leaving 630 for training.</p>
    <div class="table-wrap"><table class="design-table">
      <caption>Three separate groups within each repetition</caption>
      <thead><tr><th scope="col">Group</th><th scope="col">Specimens</th><th scope="col">Role</th></tr></thead>
      <tbody>
        <tr><th scope="row">Training</th><td class="num">${design.split_sizes.fit}</td><td>Both model families were fitted on the same specimens.</td></tr>
        <tr><th scope="row">Screening</th><td class="num">${design.split_sizes.screen}</td><td>These specimens determined model settings, thresholds and the preferred family.</td></tr>
        <tr><th scope="row">Assessment</th><td class="num">${design.split_sizes.assessment}</td><td>Both family winners were compared after their models and thresholds were fixed.</td></tr>
      </tbody>
    </table></div>
    <p class="note">The authors’ 345-specimen technical-validation cohort was unused in this follow-up. Within a repetition, the three groups were separate. Across repetitions, specimens were reused; the repetitions are not independent validation trials.</p>
    <section class="content-section" aria-labelledby="selection-heading">
      <h2 id="selection-heading">Model selection using screening specimens</h2>
      <p>The candidates were three logistic regression settings and two CatBoost depths. Each candidate’s threshold retained at least 90% of screening rejection cases. Within each family, then between the family winners, selection favored fewer false positives; ROC-AUC broke ties. An exact tie between families favored logistic regression.</p>
      <table class="selection-table"><caption>Preferred family across the 20 repetitions</caption><thead><tr><th scope="col">Model family</th><th scope="col">Repetitions selected</th></tr></thead><tbody>
        <tr><th scope="row">CatBoost</th><td class="selection-value">${families.catboost} <span>of ${selections.length}</span></td></tr>
        <tr><th scope="row">Logistic regression</th><td class="selection-value">${families.logistic} <span>of ${selections.length}</span></td></tr>
      </tbody></table>
      <details class="records"><summary>All 20 selections and random seeds</summary><div class="table-wrap records-body"><table><thead><tr><th scope="col">Repetition</th><th scope="col">Seed</th><th scope="col">Selected family</th><th scope="col">Selected candidate</th></tr></thead><tbody>${selectionRows}</tbody></table></div></details>
    </section>
    <section class="content-section" aria-labelledby="assessment-heading">
      <h2 id="assessment-heading">Errors on the discovery assessment specimens</h2>
      <p>In each repetition, both family winners were evaluated on the same 210 discovery specimens reserved for assessment. These specimens had no role in fitting or selection. Each assessment contained 139 rejection and 71 no-rejection specimens.</p>
      <div class="table-wrap"><table><caption>Repetitions with fewer errors on the assessment specimens</caption><thead><tr><th scope="col">Error compared</th><th scope="col">CatBoost had fewer</th><th scope="col">Logistic had fewer</th><th scope="col">Equal counts</th></tr></thead><tbody>
        <tr><th scope="row">Missed rejection</th><td class="num">${assessmentComparison.fn.catboost_fewer} / 20</td><td class="num">${assessmentComparison.fn.logistic_fewer} / 20</td><td class="num">${assessmentComparison.fn.tied} / 20</td></tr>
        <tr><th scope="row">False rejection flags</th><td class="num">${assessmentComparison.fp.catboost_fewer} / 20</td><td class="num">${assessmentComparison.fp.logistic_fewer} / 20</td><td class="num">${assessmentComparison.fp.tied} / 20</td></tr>
      </tbody></table></div>
      <p>CatBoost was selected more often, but neither family consistently missed fewer rejection cases. Selection frequency alone does not establish a dependable performance advantage.</p>
      <p>This follow-up examined models fitted on 630 specimens. It does not re-estimate the accuracy of the application’s saved model, which was fitted on 787 specimens.</p>
    </section>
    <div class="action-row">${source('stability','Repeated-split analysis report')}${source('split-design','Saved partition and selection design')}</div>
  </div>
  <p class="source">Primary analysis: 15 Sep 2026. Discovery follow-up: 17 Sep 2026. The primary report includes paired uncertainty and score reliability.</p>
</section>
<section id="specimen" role="tabpanel" aria-labelledby="tab-specimen" hidden>
  <h1>Application input</h1>
  <p class="lead">An analyst or molecular laboratory researcher can submit raw B-HOT RNA counts through the application. The service uses the saved model without another training run.</p>
  <h2>The CSV supplied to the service</h2>
  <p>Each row represents one specimen. The first column is its identifier; the remaining 770 columns contain raw assay counts, including 12 housekeeping targets. The recorded diagnosis is excluded, and the identifier is not a predictor.</p>
  <figure class="csv-preview"><figcaption>Selected columns from the actual public example · ${esc(pred.specimen)}</figcaption><pre id="csv-preview">${esc(csvPreview)}</pre></figure>
  <p>The preview shows five measurement columns. The complete input requires all 770. ABCF1 and G6PD are two of the housekeeping targets; IFNG is one of the 758 model targets.</p>
  <p>This example comes from the discovery-screening group and has a recorded no-rejection diagnosis. Its use here demonstrates the software.</p>
  <section class="content-section" aria-labelledby="application-heading">
    <h2 id="application-heading">Local application</h2>
    <p>The following command starts the service from the project root. The application opens in a separate tab, keeping this explanation available.</p>
    <pre>uv run --frozen python presentation/source/serve_demo.py</pre>
    <p><a class="button" id="application-link" href="http://127.0.0.1:8766/" target="_blank" rel="noopener">Kidney biopsy application</a></p>
  </section>
</section>
<section id="engineering" role="tabpanel" aria-labelledby="tab-engineering" hidden>
  <h1>From research code to a scoring service</h1>
  <p class="lead">The application needs to reproduce the calculation used during model evaluation. Shared preprocessing, a saved model and its fixed threshold connect the research procedure to the service.</p>
  <div class="subtabs" role="tablist" aria-label="Engineering views">
    <button id="tab-shared" role="tab" aria-selected="true" aria-controls="shared-view">Shared calculation</button>
    <button id="tab-interface" role="tab" aria-selected="false" aria-controls="interface-view" tabindex="-1">Programmatic access</button>
    <button id="tab-checks" role="tab" aria-selected="false" aria-controls="checks-view" tabindex="-1">Verification and setup</button>
  </div>
  <div id="shared-view" role="tabpanel" aria-labelledby="tab-shared">
    <h2>One implementation of specimen preparation</h2>
    <p>Training and prediction call the same normalization function. The browser collects input and displays results; the service and command line use the shared Python prediction code.</p>
    <ol class="process">
      <li><h3>Input validation</h3><p>The service checks that every required target is present exactly once and that counts are finite and nonnegative. Invalid input produces an explanation and no predictions.</p></li>
      <li><h3>Specimen normalization</h3><p>The shared function calculates log₂(count + 1), then subtracts the mean of the 12 housekeeping log counts. The remaining 758 targets become model inputs.</p></li>
      <li><h3>Model output</h3><p>The saved model produces a score. A score at or above its fixed threshold produces a positive rejection flag.</p></li>
    </ol>
    <section class="content-section" aria-labelledby="shared-source-heading">
      <h2 id="shared-source-heading">The shared function in the actual source</h2>
      <p>Both excerpts call <code>normalize_counts</code>. Prediction also supplies the saved schema, which identifies the required targets and their model input order.</p>
      <div class="code-columns">
        <div><p class="code-label">Training</p><pre>${esc(trainingCode)}</pre>${source('training-code','Training source')}</div>
        <div><p class="code-label">Service and command-line prediction</p><pre>${esc(predictionCode)}</pre>${source('prediction-code','Prediction source')}</div>
      </div>
      <p>Normalization uses only that specimen’s counts. Models with learned scaling or feature selection fit those steps on training specimens only and retain them with the fitted model.</p>
      <div class="action-row">${source('preprocessing-code','Shared preprocessing source')}${source('code','Complete code guide')}</div>
    </section>
  </div>
  <div id="interface-view" role="tabpanel" aria-labelledby="tab-interface" hidden>
    <h2>The same service is available to other software</h2>
    <p>A batch script or research tool can send a CSV directly to <code>POST /predict</code>. The service applies the same input checks and calculation used by the browser application, then returns a structured response.</p>
    <section class="content-section" aria-labelledby="request-heading">
      <h3 id="request-heading">Request: one specimen and all 770 counts</h3>
      <p>This request uses the complete public example shown in the Application tab. The CSV download contains the exact input used for the saved response.</p>
      <pre>${esc(requestExample)}</pre>
      <button class="quiet" id="download-example">Complete example CSV</button>
    </section>
    <section class="content-section" aria-labelledby="response-heading">
      <h3 id="response-heading">Successful response: HTTP 200</h3>
      <p>The caller receives a result for each specimen. Separate fields describe the numerical result, the threshold decision and the version of the calculation.</p>
      <div class="table-wrap"><table class="field-table"><thead><tr><th scope="col">Response field</th><th scope="col">Meaning</th></tr></thead><tbody>
        <tr><th scope="row"><code>specimen</code></th><td>The identifier supplied with the input row.</td></tr>
        <tr><th scope="row"><code>rejection_score</code></th><td>The model’s numerical score.</td></tr>
        <tr><th scope="row"><code>threshold</code> and <code>rejection_flag</code></th><td>The fixed cutoff and whether the score reached it.</td></tr>
        <tr><th scope="row"><code>model_version</code> and <code>schema_version</code></th><td>The saved model and the expected input format.</td></tr>
        <tr><th scope="row"><code>input_checks</code></th><td>The batch’s input-check status and specimen count.</td></tr>
      </tbody></table></div>
      <details class="records"><summary>Complete saved JSON response</summary><pre>${fullResponse}</pre><p class="source">Captured ${esc(snapshot.captured_utc.slice(0,10))} from the local application and saved model.</p></details>
    </section>
    <section class="content-section" aria-labelledby="invalid-heading">
      <h3 id="invalid-heading">Incomplete input: HTTP 422</h3>
      <p>When IFNG is missing, the whole batch is rejected. The response identifies the missing target and contains no predictions.</p>
      <pre>${esc(JSON.stringify(snapshot.invalid_response,null,2))}</pre>
    </section>
    <div class="action-row">${source('api','Application and API guide')}</div>
  </div>
  <div id="checks-view" role="tabpanel" aria-labelledby="tab-checks" hidden>
    <h2>Agreement between research results and the service</h2>
    <p>The recorded check sent all <strong>${http.specimens} specimens from the authors’ technical-validation cohort</strong> through the HTTP service. It compared their results with command-line predictions and the saved research results, using the same model and threshold.</p>
    <p>Measurement columns were reordered to check that the service matched targets by name. This comparison tests software consistency; it does not provide another estimate of classifier performance.</p>
    <div class="table-wrap"><table><caption>Recorded agreement check · 17 Sep 2026</caption><thead><tr><th scope="col">Comparison</th><th scope="col">Requirement</th><th scope="col">Observed result</th></tr></thead><tbody>
      <tr><th scope="row">Model scores</th><td>Absolute difference no greater than 10⁻¹²</td><td>Largest HTTP-to-saved difference: ${http.max_http_saved_score_difference.toExponential(2)}</td></tr>
      <tr><th scope="row">Rejection flags</th><td>Identical across all three routes</td><td>All ${http.specimens} matched</td></tr>
    </tbody></table></div>
    <details class="records"><summary>Source assertion for HTTP and command-line score agreement</summary><pre>${esc(verificationCode)}</pre></details>
    <div class="action-row">${source('http','Recorded agreement check')}${source('http-code','HTTP verification source')}</div>
    <section class="content-section" aria-labelledby="failure-heading">
      <h2 id="failure-heading">Failures that must prevent scoring</h2>
      <p>Separate tests check that invalid input and incompatible model metadata cannot produce a result.</p>
      <div class="table-wrap"><table><thead><tr><th scope="col">Failure</th><th scope="col">Expected behavior</th><th scope="col">Supporting record or source</th></tr></thead><tbody>
        <tr><th scope="row">Missing assay target</th><td>The batch is rejected without predictions.</td><td>${source('http','HTTP check record')}</td></tr>
        <tr><th scope="row">Duplicate targets or non-finite counts</th><td>The input fails validation before scoring.</td><td>${source('prediction-tests','Input validation tests')}</td></tr>
        <tr><th scope="row">Incompatible model metadata</th><td>The model does not load.</td><td>${source('prediction-tests','Model compatibility tests')}</td></tr>
      </tbody></table></div>
    </section>
    <section class="content-section" aria-labelledby="setup-heading">
      <h2 id="setup-heading">Reproducing and running the software</h2>
      <p>The repository includes the environment definition, commands and checks another developer needs to reproduce the analysis and run the saved model.</p>
      <div class="table-wrap"><table><thead><tr><th scope="col">Included in the project</th><th scope="col">Purpose and evidence</th></tr></thead><tbody>
        <tr><th scope="row">Python 3.12, uv lockfile and run instructions</th><td>The dependency versions and commands are recorded in the ${source('code','code guide')} and ${source('api','application guide')}.</td></tr>
        <tr><th scope="row">Automated checks on code changes</th><td>The ${source('workflow','CI workflow')} runs installed-package tests and a synthetic-model container check. A hosted pass is recorded for an earlier revision.</td></tr>
        <tr><th scope="row">Local container with the research model</th><td>The ${source('container','17 Sep 2026 container record')} covers the running service, public examples and invalid input.</td></tr>
      </tbody></table></div>
      <p>The application and research-container checks cited here were local. Cloud deployment remains future work.</p>
      <div class="action-row">${source('verification','Software verification guide')}</div>
    </section>
  </div>
</section>
<footer class="footer-nav"><button id="previous-stop">Previous section</button><p id="stop-position">1 of 3</p><button id="next-stop">Next: application</button></footer>
</main>
<dialog class="ref-dialog" id="reference-dialog" aria-label="Reports and source material"><div class="ref-toolbar"><button class="quiet" id="all-references">All reports and sources</button><button class="button secondary" id="close-reference">Close</button></div><div class="ref-body" id="reference-body"></div></dialog>
<script type="application/json" id="demo-data">${payload}</script><script>${js}</script>
</body></html>`;
await fs.writeFile(path.join(root,'presentation/engineering_demo.html'),html);
const inputs = ['presentation/source/demo_snapshot.json','results/followup/20260917_stability/summary.json',...definitions.map(x=>x[3])];
const hashes = Object.fromEntries(await Promise.all(inputs.map(async name=>[name,digest(await fs.readFile(path.join(root,name)))])));
await fs.writeFile(path.join(root,'presentation/engineering_demo_sources.json'),JSON.stringify({built:'2026-09-22',model_version:snapshot.model_version,sources:hashes,output_sha256:digest(html)},null,2)+'\n');
console.log(JSON.stringify({output:'presentation/engineering_demo.html',bytes:Buffer.byteLength(html),references:Object.keys(references).length,model_version:snapshot.model_version}));
