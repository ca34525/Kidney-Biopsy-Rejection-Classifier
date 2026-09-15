"use strict";

const byId = (id) => document.getElementById(id);
const ui = {
  exampleSelect: byId("example-select"),
  countsFile: byId("counts-file"),
  runButton: byId("run-button"),
  invalidButton: byId("invalid-button"),
  result: byId("result-content"),
};
let metadata = null;
let examples = [];
let busy = false;

async function runPrediction() {
  if (busy || !metadata) return;
  setBusy(true);

  const waiting = element("div", "empty-result");
  waiting.append(
    element("h3", "", "Checking counts…"),
    element("p", "", "The complete batch must pass input checks before any scores are returned."),
  );
  ui.result.replaceChildren(waiting);

  try {
    const body = await readSelectedCounts();
    const response = await fetch("/predict", {
      method: "POST",
      headers: {"Content-Type": "text/csv"},
      body,
    });
    const prediction = await jsonResponse(response);
    showPredictions(prediction);
  } catch (error) {
    const message = error instanceof TypeError
      ? "The service could not be reached. Check that the local application is running."
      : error.message;
    showError(message);
  } finally {
    setBusy(false);
  }
}

async function readSelectedCounts() {
  const file = ui.countsFile.files[0];
  if (file) {
    if (file.size > metadata.max_upload_bytes) {
      throw new Error("CSV exceeds the 2 MiB upload limit.");
    }
    return file.arrayBuffer();
  }

  const exampleId = ui.exampleSelect.value;
  if (!exampleId) {
    throw new Error("Choose a compatible counts CSV to continue.");
  }
  const response = await fetch(`/demo/examples/${encodeURIComponent(exampleId)}`);
  if (!response.ok) await jsonResponse(response);
  return response.arrayBuffer();
}

function showPredictions(data) {
  const results = data.predictions;
  if (!Array.isArray(results) || results.length === 0) {
    throw new Error("The service returned no predictions.");
  }
  const modelChanged = results.some((result) => (
    result.model_version !== metadata.model_version ||
    result.threshold !== metadata.threshold ||
    result.schema_version !== metadata.schema_version
  ));
  if (modelChanged) {
    throw new Error(
      "The service model changed. Reload this page before scoring again " +
      "so its threshold and evaluation counts match the model.",
    );
  }

  const box = results.length === 1
    ? singlePrediction(results[0])
    : batchPredictions(results);
  const specimenDescription = results.length === 1 ? "this specimen" : "every specimen";
  box.append(element(
    "p", "input-ok",
    `✓ All ${data.input_checks.required_targets} targets passed input checks for ${specimenDescription}.`,
  ));
  ui.result.replaceChildren(box);
}

function singlePrediction(result) {
  const box = element("div", "prediction");
  box.append(
    element("p", "specimen-label", `Specimen ${result.specimen}`),
    flag(result.rejection_flag),
    element("p", "score-label", "Rejection model score"),
  );
  const score = element("p", "score-value", result.rejection_score.toFixed(3));
  score.title = String(result.rejection_score);
  box.append(score);

  const track = element("div", "score-track");
  track.setAttribute("aria-hidden", "true");
  const fill = element("div", "score-fill");
  fill.style.width = `${Math.max(0, Math.min(1, result.rejection_score)) * 100}%`;
  const thresholdMarker = element("span", "score-tick");
  thresholdMarker.style.left = `${result.threshold * 100}%`;
  thresholdMarker.title = `Frozen threshold: ${result.threshold}`;
  track.append(fill, thresholdMarker);

  const axis = element("div", "score-axis");
  axis.append(
    element("span", "", "0"),
    element("span", "", "Marker = frozen threshold"),
    element("span", "", "1"),
  );
  box.append(
    track,
    axis,
    element("p", "score-note", "This is a model score, not a verified probability for an individual biopsy."),
  );
  return box;
}

function batchPredictions(results) {
  const box = element("div", "prediction");
  box.append(element("h3", "batch-title", `${results.length} specimens scored`));
  const wrapper = element("div", "table-scroll");
  const table = element("table", "batch-table");

  const header = element("thead");
  const headerRow = element("tr");
  for (const title of ["Specimen", "Score", "Research flag"]) {
    const cell = element("th", "", title);
    cell.scope = "col";
    headerRow.append(cell);
  }
  header.append(headerRow);

  const body = element("tbody");
  for (const result of results) {
    const row = element("tr");
    const outcome = element("td");
    outcome.append(flag(result.rejection_flag));
    row.append(
      element("td", "", result.specimen),
      element("td", "", result.rejection_score.toFixed(3)),
      outcome,
    );
    body.append(row);
  }
  table.append(header, body);
  wrapper.append(table);
  box.append(wrapper);
  box.append(element("p", "score-note", "Scores are not verified probabilities for individual biopsies."));
  return box;
}

function describeSelection() {
  const example = examples.find((item) => item.id === ui.exampleSelect.value);
  byId("example-description").textContent = example?.description ||
    "Prepared public examples are unavailable. You can upload a compatible CSV.";
  const file = ui.countsFile.files[0];
  byId("file-selection").hidden = !file;
  byId("file-name").textContent = file ? `Selected upload: ${file.name}` : "";

  let selection = "Choose a compatible counts CSV to continue.";
  if (file) {
    selection = `Selected file: ${file.name}`;
  } else if (example) {
    selection = `Selected example: ${example.label}`;
  }
  const box = element("div", "empty-result");
  box.append(
    element("span", "empty-icon", "↗"),
    element("h3", "", "Ready to score"),
    element("p", "", selection),
  );
  ui.result.replaceChildren(box);
}

function setBusy(value) {
  busy = value;
  ui.runButton.disabled = value || !metadata;
  ui.invalidButton.disabled = value || !metadata ||
    !examples.some((example) => example.id === "missing-target");
  ui.exampleSelect.disabled = value || examples.length === 0;
  ui.countsFile.disabled = value;
  byId("clear-file").disabled = value;
  ui.runButton.textContent = value ? "Checking counts…" : "Get research score →";
}

function showError(message) {
  const box = element("div", "error-result");
  box.setAttribute("role", "alert");
  box.append(
    element("div", "error-icon", "!"),
    element("h3", "", "This batch could not be scored"),
    element("p", "", message),
    element("p", "error-note", "No results are displayed. Follow the message above and try again."),
  );
  ui.result.replaceChildren(box);
}

function flag(value) {
  return element(
    "span",
    `outcome${value ? " flagged" : ""}`,
    value ? "Rejection flag" : "Below rejection threshold",
  );
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function jsonResponse(response) {
  let value;
  try {
    value = await response.json();
  } catch {
    throw new Error("The service returned an unreadable response. Please try again.");
  }
  if (!response.ok) {
    throw new Error(value.error?.message || "The research service is unavailable. Please try again.");
  }
  return value;
}

async function initialize() {
  try {
    metadata = await jsonResponse(await fetch("/model"));
    byId("service-status").textContent = "Model ready";
    byId("service-status").classList.add("ready");
    byId("threshold-value").textContent = metadata.threshold.toFixed(6);
    byId("threshold-value").title = String(metadata.threshold);
    byId("threshold-context").hidden = false;
    byId("model-version").textContent = metadata.model_version;
    byId("input-limits").textContent =
      `All ${metadata.required_targets.length} targets · Up to ${metadata.max_specimens} specimens · 2 MiB`;

    const evidence = metadata.evaluation;
    if (evidence) {
      byId("evaluation-description").textContent =
        `${evidence.specimens} specimens in the authors’ technical-validation cohort, ` +
        "using this model and frozen threshold.";
      byId("false-flags").textContent = evidence.false_rejection_flags;
      byId("missed-rejection").textContent = evidence.missed_rejection;
      byId("false-flags-description").textContent =
        `Of ${evidence.recorded_no_rejection} specimens recorded as no rejection, ` +
        `${evidence.false_rejection_flags} crossed the rejection threshold.`;
      byId("missed-description").textContent =
        `Of ${evidence.recorded_rejection} specimens recorded as rejection, ` +
        `${evidence.missed_rejection} fell below the threshold.`;
    } else {
      byId("evaluation-description").textContent =
        "Verified evaluation counts are unavailable for this configured model.";
    }

    const response = await jsonResponse(await fetch("/demo/examples"));
    examples = response.examples;
    ui.exampleSelect.replaceChildren();
    for (const example of examples) {
      const option = element("option", "", example.label);
      option.value = example.id;
      ui.exampleSelect.append(option);
    }
    if (!examples.length) {
      const option = element("option", "", "Upload a counts CSV below");
      option.value = "";
      ui.exampleSelect.append(option);
    }
    describeSelection();
  } catch (error) {
    metadata = null;
    byId("service-status").textContent = "Model unavailable";
    byId("service-status").classList.add("unavailable");
    byId("evaluation-description").textContent =
      "Evaluation results are unavailable while the model is not ready.";
    ui.exampleSelect.replaceChildren(element("option", "", "Model unavailable"));
    showError(error instanceof TypeError
      ? "The local research service could not be reached."
      : error.message);
  }
  setBusy(false);
}

ui.runButton.addEventListener("click", runPrediction);
ui.invalidButton.addEventListener("click", () => {
  ui.countsFile.value = "";
  ui.exampleSelect.value = "missing-target";
  describeSelection();
  runPrediction();
});
ui.exampleSelect.addEventListener("change", () => {
  ui.countsFile.value = "";
  describeSelection();
});
ui.countsFile.addEventListener("change", describeSelection);
byId("clear-file").addEventListener("click", () => {
  ui.countsFile.value = "";
  describeSelection();
});
initialize();
