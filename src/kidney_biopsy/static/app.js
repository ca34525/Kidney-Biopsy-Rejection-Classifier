"use strict";

const $ = (id) => document.getElementById(id);
const ui = {select: $("example-select"), file: $("counts-file"), run: $("run-button"), invalid: $("invalid-button"), result: $("result-content")};
let metadata = null;
let examples = [];
let busy = false;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function jsonResponse(response) {
  let value;
  try { value = await response.json(); } catch { throw new Error("The service returned an unreadable response. Please try again."); }
  if (!response.ok) throw new Error(value.error?.message || "The research service is unavailable. Please try again.");
  return value;
}

function setBusy(value) {
  busy = value;
  ui.run.disabled = value || !metadata;
  ui.invalid.disabled = value || !metadata || !examples.some((item) => item.id === "missing-target");
  ui.select.disabled = value || examples.length === 0;
  ui.file.disabled = value;
  $("clear-file").disabled = value;
  ui.run.textContent = value ? "Checking counts…" : "Get research score →";
}

function describeSelection() {
  const item = examples.find((value) => value.id === ui.select.value);
  $("example-description").textContent = item?.description || "Prepared public examples are unavailable. You can upload a compatible CSV.";
  const file = ui.file.files[0];
  $("file-selection").hidden = !file;
  $("file-name").textContent = file ? `Selected upload: ${file.name}` : "";
  const box = element("div", "empty-result");
  const selection = file ? `Selected file: ${file.name}` : item ? `Selected example: ${item.label}` : "Choose a compatible counts CSV to continue.";
  box.append(element("span", "empty-icon", "↗"), element("h3", "", "Ready to score"), element("p", "", selection));
  ui.result.replaceChildren(box);
}

function showError(message) {
  const box = element("div", "error-result");
  box.setAttribute("role", "alert");
  box.append(element("div", "error-icon", "!"), element("h3", "", "This batch could not be scored"), element("p", "", message), element("p", "error-note", "No results are displayed. Follow the message above and try again."));
  ui.result.replaceChildren(box);
}

function flag(value) {
  return element("span", `outcome${value ? " flagged" : ""}`, value ? "Rejection flag" : "Below rejection threshold");
}

function showPredictions(data) {
  const results = data.predictions;
  if (!Array.isArray(results) || results.length === 0) throw new Error("The service returned no predictions.");
  if (results.some((result) => result.model_version !== metadata.model_version ||
      result.threshold !== metadata.threshold || result.schema_version !== metadata.schema_version)) {
    throw new Error("The service model changed. Reload this page before scoring again so its threshold and evaluation counts match the model.");
  }
  const box = element("div", "prediction");
  if (results.length === 1) {
    const result = results[0];
    box.append(element("p", "specimen-label", `Specimen ${result.specimen}`), flag(result.rejection_flag), element("p", "score-label", "Rejection model score"));
    const score = element("p", "score-value", result.rejection_score.toFixed(3));
    score.title = String(result.rejection_score);
    box.append(score);
    const track = element("div", "score-track");
    track.setAttribute("aria-hidden", "true");
    const fill = element("div", "score-fill");
    fill.style.width = `${Math.max(0, Math.min(1, result.rejection_score)) * 100}%`;
    const tick = element("span", "score-tick");
    tick.style.left = `${result.threshold * 100}%`;
    tick.title = `Frozen threshold: ${result.threshold}`;
    track.append(fill, tick);
    const axis = element("div", "score-axis");
    axis.append(element("span", "", "0"), element("span", "", "Marker = frozen threshold"), element("span", "", "1"));
    box.append(track, axis, element("p", "score-note", "This is a model score, not a verified probability for an individual biopsy."));
  } else {
    box.append(element("h3", "batch-title", `${results.length} specimens scored`));
    const wrapper = element("div", "table-scroll");
    const table = element("table", "batch-table");
    const header = element("thead");
    const row = element("tr");
    for (const title of ["Specimen", "Score", "Research flag"]) { const cell = element("th", "", title); cell.scope = "col"; row.append(cell); }
    header.append(row);
    const body = element("tbody");
    for (const result of results) {
      const line = element("tr");
      const outcome = element("td"); outcome.append(flag(result.rejection_flag));
      line.append(element("td", "", result.specimen), element("td", "", result.rejection_score.toFixed(3)), outcome);
      body.append(line);
    }
    table.append(header, body); wrapper.append(table); box.append(wrapper);
    box.append(element("p", "score-note", "Scores are not verified probabilities for individual biopsies."));
  }
  box.append(element("p", "input-ok", `✓ All ${data.input_checks.required_targets} targets passed input checks for ${results.length === 1 ? "this specimen" : "every specimen"}.`));
  ui.result.replaceChildren(box);
}

async function runPrediction() {
  if (busy || !metadata) return;
  setBusy(true);
  const waiting = element("div", "empty-result");
  waiting.append(element("h3", "", "Checking counts…"), element("p", "", "The complete batch must pass input checks before any scores are returned."));
  ui.result.replaceChildren(waiting);
  try {
    let body;
    const file = ui.file.files[0];
    if (file) {
      if (file.size > metadata.max_upload_bytes) throw new Error("CSV exceeds the 2 MiB upload limit.");
      body = await file.arrayBuffer();
    } else {
      if (!ui.select.value) throw new Error("Choose a compatible counts CSV to continue.");
      const response = await fetch(`/demo/examples/${encodeURIComponent(ui.select.value)}`);
      if (!response.ok) await jsonResponse(response);
      body = await response.arrayBuffer();
    }
    const response = await fetch("/predict", {method: "POST", headers: {"Content-Type": "text/csv"}, body});
    showPredictions(await jsonResponse(response));
  } catch (error) { showError(error instanceof TypeError ? "The service could not be reached. Check that the local application is running." : error.message); }
  finally { setBusy(false); }
}

ui.run.addEventListener("click", runPrediction);
ui.invalid.addEventListener("click", () => { ui.file.value = ""; ui.select.value = "missing-target"; describeSelection(); runPrediction(); });
ui.select.addEventListener("change", () => { ui.file.value = ""; describeSelection(); });
ui.file.addEventListener("change", describeSelection);
$("clear-file").addEventListener("click", () => { ui.file.value = ""; describeSelection(); });

async function initialize() {
  try {
    metadata = await jsonResponse(await fetch("/model"));
    $("service-status").textContent = "Model ready";
    $("service-status").classList.add("ready");
    $("threshold-value").textContent = metadata.threshold.toFixed(6);
    $("threshold-value").title = String(metadata.threshold);
    $("threshold-context").hidden = false;
    $("model-version").textContent = metadata.model_version;
    $("input-limits").textContent = `All ${metadata.required_targets.length} targets · Up to ${metadata.max_specimens} specimens · 2 MiB`;
    const evidence = metadata.evaluation;
    if (evidence) {
      $("evaluation-description").textContent = `${evidence.specimens} specimens in the authors’ technical-validation cohort, using this model and frozen threshold.`;
      $("false-flags").textContent = evidence.false_rejection_flags;
      $("missed-rejection").textContent = evidence.missed_rejection;
      $("false-flags-description").textContent = `Of ${evidence.recorded_no_rejection} specimens recorded as no rejection, ${evidence.false_rejection_flags} crossed the rejection threshold.`;
      $("missed-description").textContent = `Of ${evidence.recorded_rejection} specimens recorded as rejection, ${evidence.missed_rejection} fell below the threshold.`;
    } else { $("evaluation-description").textContent = "Verified evaluation counts are unavailable for this configured model."; }
    const response = await jsonResponse(await fetch("/demo/examples"));
    examples = response.examples;
    ui.select.replaceChildren();
    for (const item of examples) { const option = element("option", "", item.label); option.value = item.id; ui.select.append(option); }
    if (!examples.length) { const option = element("option", "", "Upload a counts CSV below"); option.value = ""; ui.select.append(option); }
    describeSelection();
  } catch (error) {
    metadata = null;
    $("service-status").textContent = "Model unavailable";
    $("service-status").classList.add("unavailable");
    $("evaluation-description").textContent = "Evaluation results are unavailable while the model is not ready.";
    ui.select.replaceChildren(element("option", "", "Model unavailable"));
    showError(error instanceof TypeError ? "The local research service could not be reached." : error.message);
  }
  setBusy(false);
}
initialize();
