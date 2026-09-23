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
const config = JSON.parse(await read('presentation/source/demo_config.json'));
const applicationUrl = `http://127.0.0.1:${config.port}/`;
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
// Keep the walkthrough excerpts tied to exact lines in the working source.
function excerpt(raw, first, last, indent = 0) {
  const lines = raw.split(/\r?\n/);
  const start = lines.findIndex(line => line.trim() === first);
  const end = lines.findIndex((line, index) => index >= start && line.trim() === last);
  if (start < 0 || end < start) throw new Error(`Source excerpt changed: ${first}`);
  return lines.slice(start, end + 1).map(line => line.slice(indent)).join('\n');
}
const normalizationCode = excerpt(references['preprocessing-code'].raw,
  'numeric_counts = validate_counts(counts, schema)', 'return normalized.loc[:, feature_names]', 4);
const scoringCode = references['prediction-code'].raw.split(/\r?\n/)
  .filter(line => /^\s*(?:scores = predict_scores\(self\.model, features\)|"rejection_flag": scores >= self\.threshold,)$/.test(line))
  .map(line => line.trim()).join('\n…\n');
if (scoringCode.split('\n').length !== 3) throw new Error('Scoring excerpt changed');
const apiSource = await read('src/kidney_biopsy/api.py');
const apiCallCode = excerpt(apiSource,
  'predictions = await run_in_threadpool(predictor.predict, counts)',
  'predictions = await run_in_threadpool(predictor.predict, counts)', 12);
const reorderTestCode = excerpt(references['prediction-tests'].raw,
  'training = normalize_counts(self.raw)',
  'assert_frame_equal(training, prediction, check_exact=True)', 8);
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
  `curl ${applicationUrl}predict \\`,
  "  -H 'Content-Type: text/csv' \\",
  '  --data-binary @no-rejection.csv',
].join('\n');
const source = (id, text) => `<button class="quiet" data-ref="${id}">${text}</button>`;
const css = await read('presentation/source/engineering_demo.css');
const js = await read('presentation/source/engineering_demo.js');
const payload = JSON.stringify({snapshot,references}).replace(/</g,'\\u003c');
const html = `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#16343E"><title>Project walkthrough · Kidney biopsy classifier</title><style>${css}</style></head>
<body>
<a class="skip" href="#main">Demonstration content</a>
<header>
  <div class="topline"><div><p class="brand">Project walkthrough</p><p class="project">Kidney biopsy rejection classifier</p></div><button class="quiet" id="reference-library">Reports and sources</button></div>
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
    <p>CatBoost’s original screening advantage was one fewer false positive at the same sensitivity. This follow-up checked how consistently screening preferred either model across discovery splits.</p>
    <p>Each of <strong>${selections.length} repetitions</strong> randomly reassigned the same <strong>1,050 discovery specimens</strong> using a recorded seed. The procedure reserved 210 for assessment, then 210 of the remaining 840 for screening, leaving 630 for training. Both steps preserved approximately the four diagnosis proportions.</p>
    <div class="table-wrap"><table class="design-table">
      <caption>Three separate groups within each repetition</caption>
      <thead><tr><th scope="col">Group</th><th scope="col">Specimens</th><th scope="col">Role</th></tr></thead>
      <tbody>
        <tr><th scope="row">Training</th><td class="num">${design.split_sizes.fit}</td><td>Both model families use the same training specimens.</td></tr>
        <tr><th scope="row">Screening</th><td class="num">${design.split_sizes.screen}</td><td>Screening determines settings, thresholds and the preferred family.</td></tr>
        <tr><th scope="row">Assessment</th><td class="num">${design.split_sizes.assessment}</td><td>Both family winners score these specimens after selection.</td></tr>
      </tbody>
    </table></div>
    <p class="note">Groups were separate within each repetition. Repetitions reused specimens and are not independent trials. The authors’ 345 validation specimens were unused.</p>
    <section class="content-section" aria-labelledby="selection-heading">
      <h2 id="selection-heading">Model selection using screening specimens</h2>
      <p>This follow-up used 630 training specimens instead of 787 and revised the candidates to three logistic settings and two CatBoost depths. The candidate settings stayed fixed across repetitions.</p>
      <p>Each threshold retained at least 90% of screening rejection cases. Selection within and between families favored fewer false positives, then higher ROC-AUC. Exact ties between families favored logistic regression.</p>
      <table class="selection-table"><caption>Preferred family across the 20 repetitions</caption><thead><tr><th scope="col">Model family</th><th scope="col">Repetitions selected</th></tr></thead><tbody>
        <tr><th scope="row">CatBoost</th><td class="selection-value">${families.catboost} <span>of ${selections.length}</span></td></tr>
        <tr><th scope="row">Logistic regression</th><td class="selection-value">${families.logistic} <span>of ${selections.length}</span></td></tr>
      </tbody></table>
      <p>Screening selected CatBoost more often, but selected logistic regression in seven repetitions. The model choice depended on the discovery split.</p>
      <details class="records"><summary>All 20 selections and random seeds</summary><div class="table-wrap records-body"><table><thead><tr><th scope="col">Repetition</th><th scope="col">Seed</th><th scope="col">Selected family</th><th scope="col">Selected candidate</th></tr></thead><tbody>${selectionRows}</tbody></table></div></details>
    </section>
    <details class="records content-section" aria-labelledby="assessment-heading">
      <summary id="assessment-heading">Supporting results: errors on held-out discovery specimens</summary>
      <div class="records-body">
      <p>Both family winners were assessed on the same 210 reserved specimens: 139 rejection and 71 no rejection. These errors did not determine the 13/7 screening selection count.</p>
      <div class="table-wrap"><table><caption>Repetitions with fewer errors on the assessment specimens</caption><thead><tr><th scope="col">Error compared</th><th scope="col">CatBoost had fewer</th><th scope="col">Logistic had fewer</th><th scope="col">Equal counts</th></tr></thead><tbody>
        <tr><th scope="row">Missed rejection</th><td class="num">${assessmentComparison.fn.catboost_fewer} / 20</td><td class="num">${assessmentComparison.fn.logistic_fewer} / 20</td><td class="num">${assessmentComparison.fn.tied} / 20</td></tr>
        <tr><th scope="row">False rejection flags</th><td class="num">${assessmentComparison.fp.catboost_fewer} / 20</td><td class="num">${assessmentComparison.fp.logistic_fewer} / 20</td><td class="num">${assessmentComparison.fp.tied} / 20</td></tr>
      </tbody></table></div>
      <p>Neither family consistently missed fewer rejection cases. These results describe the follow-up procedure, not the application’s saved model.</p>
      </div>
    </details>
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
    <p>On this Mac, use the existing virtual environment:</p>
    <pre>.venv/bin/python presentation/source/serve_demo.py</pre>
    <p>With uv installed, the equivalent command is <code>uv run --frozen python presentation/source/serve_demo.py</code>.</p>
    <p>The launcher uses the frozen run and prepared examples selected in <code>presentation/source/demo_config.json</code>.</p>
    <p><a class="button" id="application-link" href="${applicationUrl}" target="_blank" rel="noopener">Kidney biopsy application</a> <span id="application-url">${applicationUrl}</span></p>
  </section>
</section>
<section id="engineering" role="tabpanel" aria-labelledby="tab-engineering" hidden>
  <h1>How the scoring service works</h1>
  <p class="lead">Training and the application share preparation and scoring code. The saved model and threshold preserve the evaluated calculation.</p>
  <div class="subtabs" role="tablist" aria-label="Engineering views">
    <button id="tab-shared" role="tab" aria-selected="true" aria-controls="shared-view">Shared prediction code</button>
    <button id="tab-interface" role="tab" aria-selected="false" aria-controls="interface-view" tabindex="-1">Using the API</button>
    <button id="tab-checks" role="tab" aria-selected="false" aria-controls="checks-view" tabindex="-1">Tests and reproducibility</button>
  </div>
  <div id="shared-view" role="tabpanel" aria-labelledby="tab-shared">
    <h2>The same preparation in training and prediction</h2>
    <p><code>normalize_counts</code> checks the input, normalizes each specimen and returns targets in the saved model’s order. The browser and command line both use <code>Predictor</code>.</p>
    <div class="code-columns">
      <div>
        <p class="code-label">preprocessing.py · normalize_counts</p>
        <pre>${esc(normalizationCode)}</pre>
        ${source('preprocessing-code','Full preprocessing source')}
      </div>
      <div>
        <p class="code-label">prediction.py · Predictor.predict</p>
        <pre>${esc(predictionCode)}</pre>
        <p class="code-label">Score and flag · selected lines from predict_normalized</p>
        <pre>${esc(scoringCode)}</pre>
        ${source('prediction-code','Full prediction source')}
      </div>
    </div>
    <section class="content-section" aria-labelledby="training-heading">
      <h2 id="training-heading">Where training fits</h2>
      <p>The research script prepares the data, fits candidates and uses discovery screening to select the model and threshold. Each run saves the fitted models, split assignments and results with its configuration and input hashes.</p>
      <p>Training calls the same normalization function. Learned scaling and feature selection fit only the training rows.</p>
      <pre>${esc(trainingCode)}</pre>
      <div class="action-row">${source('training-code','Training source')}${source('code','Code guide')}</div>
    </section>
  </div>
  <div id="interface-view" role="tabpanel" aria-labelledby="tab-interface" hidden>
    <h2>Other software can request the same score</h2>
    <p><code>POST /predict</code> accepts a CSV and returns each specimen’s score, threshold decision and model version.</p>
    <div class="code-columns">
      <div>
        <p class="code-label">Request · one specimen with all 770 counts</p>
        <pre>${esc(requestExample)}</pre>
        <button class="quiet" id="download-example">Complete example CSV</button>
      </div>
      <div>
        <p class="code-label">Saved response · HTTP 200 · selected fields</p>
        <pre>${esc(JSON.stringify({specimen:pred.specimen,rejection_score:pred.rejection_score,threshold:pred.threshold,rejection_flag:pred.rejection_flag,model_version:pred.model_version},null,2))}</pre>
      </div>
    </div>
    <section class="content-section" aria-labelledby="handler-heading">
      <h2 id="handler-heading">The handler calls the shared predictor</h2>
      <p>After validating the CSV, the API calls <code>Predictor.predict</code> and returns its result rows as JSON.</p>
      <p class="code-label">src/kidney_biopsy/api.py · inside POST /predict</p>
      <pre>${esc(apiCallCode)}</pre>
      <details class="records"><summary>Complete saved JSON response</summary><pre>${fullResponse}</pre><p class="source">Captured ${esc(snapshot.captured_utc.slice(0,10))} from the local application and saved model.</p></details>
      <p>Missing IFNG produces <strong>HTTP 422</strong>. The whole batch fails, with no predictions.</p>
      <details class="records"><summary>Saved error response</summary><pre>${esc(JSON.stringify(snapshot.invalid_response,null,2))}</pre></details>
      <div class="action-row">${source('api','Application and API guide')}</div>
    </section>
  </div>
  <div id="checks-view" role="tabpanel" aria-labelledby="tab-checks" hidden>
    <h2>The service agrees with the saved research results</h2>
    <p>The recorded check compared HTTP, command-line and saved predictions for all <strong>${http.specimens} technical-validation specimens</strong>, using the same model and threshold. It also reordered the CSV columns.</p>
    <div class="table-wrap"><table><caption>Recorded agreement check · 17 Sep 2026</caption><thead><tr><th scope="col">Comparison</th><th scope="col">Requirement</th><th scope="col">Observed result</th></tr></thead><tbody>
      <tr><th scope="row">Model scores</th><td>Absolute difference ≤ 10⁻¹²</td><td>Largest HTTP-to-saved difference: ${http.max_http_saved_score_difference.toExponential(2)}</td></tr>
      <tr><th scope="row">Rejection flags</th><td>Identical across all three routes</td><td>All ${http.specimens} matched</td></tr>
    </tbody></table></div>
    <p>This checks software consistency. The earlier evaluation measures classifier performance.</p>
    <div class="action-row">${source('http','Recorded agreement check')}${source('http-code','HTTP verification source')}</div>
    <section class="content-section" aria-labelledby="test-heading">
      <h2 id="test-heading">A test for reordered columns</h2>
      <p>This test reverses the CSV columns and checks that preparation still produces identical model inputs.</p>
      <p class="code-label">tests/test_shared_prediction.py · test excerpt</p>
      <pre>${esc(reorderTestCode)}</pre>
      <p>Other tests reject missing or duplicate targets, non-finite counts and incompatible model metadata.</p>
      <div class="action-row">${source('prediction-tests','Input and model compatibility tests')}</div>
    </section>
    <section class="content-section" aria-labelledby="setup-heading">
      <h2 id="setup-heading">Running and checking the project</h2>
      <div class="table-wrap"><table><thead><tr><th scope="col">Included</th><th scope="col">Purpose and evidence</th></tr></thead><tbody>
        <tr><th scope="row">Python 3.12 and uv lockfile</th><td>The ${source('code','code guide')} and ${source('api','application guide')} document setup and run commands.</td></tr>
        <tr><th scope="row">Automated checks</th><td>The ${source('workflow','CI workflow')} tests the installed package and a container with a synthetic model. A hosted pass covers an earlier revision.</td></tr>
        <tr><th scope="row">Local research-model container</th><td>The ${source('container','17 Sep 2026 record')} verifies startup, predictions and invalid input.</td></tr>
      </tbody></table></div>
      <p>Cloud deployment remains future work.</p>
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
const inputs = ['src/kidney_biopsy/api.py','presentation/source/demo_config.json','presentation/source/demo_snapshot.json','results/followup/20260917_stability/summary.json',...definitions.map(x=>x[3])];
const hashes = Object.fromEntries(await Promise.all(inputs.map(async name=>[name,digest(await fs.readFile(path.join(root,name)))])));
await fs.writeFile(path.join(root,'presentation/engineering_demo_sources.json'),JSON.stringify({built:'2026-09-22',model_version:snapshot.model_version,sources:hashes,output_sha256:digest(html)},null,2)+'\n');
console.log(JSON.stringify({output:'presentation/engineering_demo.html',bytes:Buffer.byteLength(html),references:Object.keys(references).length,model_version:snapshot.model_version}));
