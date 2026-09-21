"""Build the offline code guide from editable content and current source.

Run from the project root: uv run --frozen python scripts/build_code_guide.py
Use --check to detect stale HTML, links, symbols, or its source manifest.
Use --refresh-example to recalculate the public specimen with the frozen predictor.
Normal builds need only Python's standard library and the checked-in example record.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "docs/code_guide"
OUTPUT = ROOT / "docs/CODE_GUIDE.html"
CHAPTERS = ("data", "preprocessing", "training", "results", "prediction", "operations")
SOURCES: dict[str, str] = {}
INPUTS: set[str] = set()


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"Missing or nonlocal documentation input: {relative}")
    INPUTS.add(relative)
    return path.read_text(encoding="utf-8-sig")


def digest(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def prose(value: str) -> str:
    parts = value.split("`")
    return "".join(
        f"<code>{esc(part)}</code>" if i % 2 else esc(part) for i, part in enumerate(parts)
    )


def paragraphs(values: list[str]) -> str:
    return "".join(f"<p>{prose(value)}</p>" for value in values)


def source_id(path: str) -> str:
    return "source-" + re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-")


def source(path: str) -> str:
    if path not in SOURCES:
        SOURCES[path] = read(path)
    return SOURCES[path]


def symbol_range(path: str, symbol: str) -> tuple[int, int]:
    value = source(path)
    if path.endswith(".py"):
        nodes = ast.parse(value).body
        node = None
        for part in symbol.split("."):
            node = next(
                (
                    n
                    for n in nodes
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and n.name == part
                ),
                None,
            )
            if node is None:
                raise ValueError(f"Documented Python symbol no longer exists: {path}:{symbol}")
            nodes = node.body
        return node.lineno, node.end_lineno
    if path.endswith(".js"):
        match = re.search(r"^(?:async )?function " + re.escape(symbol) + r"\(", value, re.M)
        if not match:
            raise ValueError(f"Documented JavaScript function no longer exists: {path}:{symbol}")
        end = re.search(r"^}", value[match.start() :], re.M)
        if not end:
            raise ValueError(f"Could not find end of JavaScript function: {symbol}")
        return value[: match.start()].count("\n") + 1, value[: match.start() + end.end()].count(
            "\n"
        ) + 1
    raise ValueError(f"Unsupported source format: {path}")


def source_link(path: str, symbol: str, label: str | None = None) -> str:
    start, _ = symbol_range(path, symbol)
    return f'<a href="#{source_id(path)}-L{start}">{esc(label or symbol)}</a>'


def local_link(path: str, label: str) -> str:
    base = path.split("#")[0]
    read(base)
    return f'<a href="../{quote(path, safe="/#")}">{esc(label)}</a>'


def code_lines(path: str, start: int, end: int, anchors: bool = False) -> str:
    lines = source(path).splitlines()
    rendered = []
    for number in range(start, min(end, len(lines)) + 1):
        ident = f' id="{source_id(path)}-L{number}"' if anchors else ""
        rendered.append(
            f'<span class="code-line"{ident}><span class="line-number" aria-hidden="true">'
            f"{number}</span>{esc(lines[number - 1])}</span>"
        )
    return "<pre><code>" + "".join(rendered) + "</code></pre>"


def function_card(item: dict, chapter_title: str) -> str:
    path, symbol = item["path"], item["symbol"]
    start, end = symbol_range(path, symbol)
    steps = "".join(f"<li>{prose(step)}</li>" for step in item["steps"])
    checks = "".join(
        f"<li>{source_link(check['path'], check['symbol'])} — {prose(check['reason'])}</li>"
        for check in item["checks"]
    )
    preview_end = min(end, start + 24)
    remainder = (
        f'<p class="source-caption">Excerpt: lines {start}–{preview_end} of {start}–{end}. '
        f"{source_link(path, symbol, 'Read the complete function in the embedded source')}.</p>"
        if preview_end < end
        else ""
    )
    if not checks:
        checks = "<li>No dedicated unit test covers this function. Follow the verification procedure described above and in the maintenance guidance; do not infer coverage from nearby tests.</li>"
    return f"""<details class="function" id="{esc(item["id"])}" data-search-title="{esc(item["title"])}" data-search-label="{esc(symbol)} · {esc(chapter_title)}">
<summary><span><span class="fn-heading">{esc(item["title"])}</span><span class="fn-symbol">{esc(symbol)} · {esc(path)}</span></span></summary>
<div class="function-body"><p>{prose(item["purpose"])}</p>
<dl class="io"><div><dt>Receives</dt><dd>{prose(item["inputs"])}</dd></div><div><dt>Returns or writes</dt><dd>{prose(item["outputs"])}</dd></div></dl>
<h4>What happens, and in what order</h4><ol class="steps">{steps}</ol>
<p><span class="fact-label">Why this design:</span> {prose(item["why"])}</p>
<p><span class="fact-label">When it fails:</span> {prose(item["failures"])}</p>
<p><span class="fact-label">If you change it:</span> {prose(item["change"])}</p>
<h4>Checks to understand</h4><ul class="checks">{checks}</ul>
<details class="source-snippet"><summary>Read the source · lines {start}–{end}</summary><p class="source-caption">Embedded from the recorded source revision. <a href="../{quote(path)}">Open the local file</a>.</p>{code_lines(path, start, preview_end)}{remainder}</details>
</div></details>"""


def render_diagram(diagram: dict, functions: dict) -> str:
    ident = diagram["id"]
    width, height = diagram.get("width", 1040), diagram["height"]
    nodes = {node["id"]: node for node in diagram["nodes"]}
    pieces = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="group" aria-labelledby="{ident}-title {ident}-desc">',
        f'<title id="{ident}-title">{esc(diagram["title"])}</title>',
        f'<desc id="{ident}-desc">{esc(diagram["caption"])} Each underlined function links to its explanation.</desc>',
        f'<defs><marker id="{ident}-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#60777b"/></marker></defs>',
    ]
    edge_descriptions = []
    for edge in diagram["edges"]:
        points = edge["points"]
        points_string = " ".join(f"{x},{y}" for x, y in points)
        kind = " artifact-edge" if edge.get("kind") == "artifact" else ""
        pieces.append(
            f'<polyline class="edge{kind}" points="{points_string}" '
            f'marker-end="url(#{ident}-arrow)"/>'
        )
        lx, ly = edge["label_at"]
        pieces.append(
            f'<text class="edge-label" x="{lx}" y="{ly}" text-anchor="middle">{esc(edge["label"])}</text>'
        )
        edge_descriptions.append(
            f"{nodes[edge['from']]['title']} → {nodes[edge['to']]['title']}: {edge['label']}."
        )
    for node in diagram["nodes"]:
        x, y = node["x"], node["y"]
        w, h = node.get("w", 296), node.get("h", 164)
        kind = node.get("kind", "module")
        pieces.append(f'<rect class="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>')
        pieces.append(
            f'<text class="node-kind" x="{x + 16}" y="{y + 23}">{esc(node.get("tag", "SAVED FILES" if kind == "artifact" else "CODE"))}</text>'
        )
        title = esc(node["title"])
        if node.get("anchor"):
            title = f'<a href="#{esc(node["anchor"])}">{title}</a>'
        pieces.append(f'<text class="node-title" x="{x + 16}" y="{y + 49}">{title}</text>')
        yy = y + 70
        if node.get("path"):
            short_path = node["path"].replace("src/kidney_biopsy/", "src/kidney_biopsy/\n")
            short_path = short_path.replace("experiments/", "experiments/\n")
            for line in short_path.splitlines():
                pieces.append(f'<text class="node-path" x="{x + 16}" y="{yy}">{esc(line)}</text>')
                yy += 14
            yy += 9
        else:
            yy += 8
        for function in node.get("functions", []):
            path = function.get("path", node.get("path"))
            symbol = function["symbol"]
            key = (path, symbol)
            if key not in functions:
                raise ValueError(f"Diagram has no explanation for {key}")
            label = function.get("label", symbol.replace("create_app.", ""))
            if len(label) > 36:
                raise ValueError(f"Diagram label too long: {label}")
            pieces.append(
                f'<a href="#{functions[key]["id"]}" aria-label="Explain {esc(symbol)} in {esc(path)}">'
                f'<text class="fn" x="{x + 16}" y="{yy}">{esc(label)}()</text></a>'
            )
            yy += 21
        for line in node.get("lines", []):
            pieces.append(f'<text class="file-line" x="{x + 16}" y="{yy}">{esc(line)}</text>')
            yy += 19
        if yy > y + h + 3:
            raise ValueError(f"Diagram node needs more height: {ident}/{node['id']}")
    pieces.append("</svg>")
    text_edges = "".join(f"<li>{esc(edge)}</li>" for edge in edge_descriptions)
    return (
        f'<figure class="diagram" id="{ident}"><div class="diagram-viewport">'
        + "".join(pieces)
        + f"</div><figcaption><strong>{esc(diagram['title'])}</strong> {esc(diagram['caption'])}</figcaption>"
        + '<p class="diagram-hint screen-only">Scroll the diagram sideways on a narrow screen. Select an underlined function to open its explanation.</p>'
        + f'<details class="diagram-list"><summary>Read the connections as text</summary><ul>{text_edges}</ul></details></figure>'
    )


def refresh_example() -> None:
    # The normal documentation build never loads a model or requires public raw data.
    sys.path.insert(0, str(ROOT / "src"))
    from kidney_biopsy.prediction import load_predictor, verify_artifact
    from kidney_biopsy.preprocessing import read_counts_csv
    from kidney_biopsy.walkthrough import describe_specimen

    manifest_path = "data/demo/manifest.json"
    manifest = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
    item = next(item for item in manifest["examples"] if item["id"] == "no-rejection")
    csv_path = verify_artifact(ROOT, item)
    predictor = load_predictor(ROOT, manifest["run_dir"])
    item["model_version"] = manifest["model_version"]
    counts = read_counts_csv(csv_path, predictor.schema)
    result = describe_specimen(counts, item, predictor)
    run_manifest_file = f"{manifest['run_dir']}/run_manifest.json"
    run_manifest = json.loads((ROOT / run_manifest_file).read_text(encoding="utf-8"))
    result["provenance"] = {
        "run_dir": manifest["run_dir"],
        "example_file": item["file"],
        "example_sha256": item["sha256"],
        "manifest_file": manifest_path,
        "manifest_sha256": digest(manifest_path),
        "run_manifest_file": run_manifest_file,
        "run_manifest_sha256": digest(run_manifest_file),
        "frozen_artifacts": [
            artifact
            for artifact in run_manifest["artifacts"]
            if artifact["file"].endswith(
                ("any_rejection_selected_model.joblib", "any_rejection_frozen.json")
            )
        ],
        "selection": manifest["selection"],
        "source_sha256": {
            path: digest(path)
            for path in (
                "src/kidney_biopsy/preprocessing.py",
                "src/kidney_biopsy/prediction.py",
                "src/kidney_biopsy/walkthrough.py",
            )
        },
    }
    (CONTENT / "specimen.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def specimen_block(example: dict) -> str:
    n = example["normalization"]
    p = example["prediction"]
    flag = bool(p["rejection_flag"])
    relation = "at or above" if flag else "below"
    flag_text = str(flag).lower()
    rows = "".join(
        f"<tr><td>{esc(item['target'])}</td><td>{item['raw_count']:g}</td>"
        f"<td>{item['log2_count_plus_one']:.6f}</td></tr>"
        for item in n["housekeeping"]
    )
    return f"""<aside class="specimen" id="specimen"><div class="specimen-head"><div><p class="eyebrow">One specimen, followed through the guide</p><h3>{esc(example["specimen"])} · prepared public example</h3></div><small>Recorded diagnosis: {esc(example["recorded_diagnosis"])}<br>Saved discovery-screen split</small></div>
<div class="specimen-grid"><div><strong>{n["raw_count"]:g}</strong><span>Raw IFNG count</span></div><div><strong>{n["normalized_value"]:.6f}</strong><span>Normalized IFNG value</span></div><div><strong>{p["rejection_score"]:.6f}</strong><span>Model score from all {example["predictor_targets"]} targets</span></div><div><strong>{p["threshold"]:.6f}</strong><span>Frozen flag threshold</span></div></div>
<p>The score is {relation} the threshold, so this specimen receives <code>rejection_flag = {flag_text}</code>. Its recorded diagnosis is used afterward for comparison. Neither the diagnosis nor the specimen ID enters the model.</p>
<details><summary>See the arithmetic and all 12 housekeeping measurements</summary><p><code>log2({n["raw_count"]:g} + 1) − {n["housekeeping_mean"]:.6f} = {n["normalized_value"]:.6f}</code>. The mean is calculated across the transformed housekeeping counts below. IFNG illustrates one feature; it does not by itself determine this model's score.</p><div class="table-wrap"><table><thead><tr><th>Housekeeping target</th><th>Raw count</th><th>log2(count + 1)</th></tr></thead><tbody>{rows}</tbody></table></div><p class="source-caption">Calculated with the project's <code>describe_specimen()</code> and the verified frozen model. Example selection: {esc(example["provenance"]["selection"])} Displayed values are rounded; the saved record retains full precision. Source: <a href="code_guide/specimen.json">specimen.json</a>.</p></details></aside>"""


def trace_for(chapter: str, example: dict) -> str:
    n, p = example["normalization"], example["prediction"]
    traces = {
        "data": f"{example['specimen']} is joined by its public accession. The prepared example contains 770 named raw measurements; its diagnosis is stored separately from that CSV.",
        "preprocessing": f"Its IFNG count {n['raw_count']:g} becomes log2(count + 1) = {n['log2_count_plus_one']:.6f}. Subtracting the 12-target mean {n['housekeeping_mean']:.6f} gives {n['normalized_value']:.6f}. The output has 758 targets in model order.",
        "training": "This specimen belongs to the saved discovery-screen split. It contributes to candidate comparison and threshold selection, not fitting or the 345-specimen technical-validation result. The prepared example was chosen by accession within diagnosis, not by its score.",
        "results": "This demonstration specimen is not one of the 345 technical-validation specimens. The report reads their saved predictions to measure performance; showing this one screening example is an explanation of software behavior.",
        "prediction": f"The frozen predictor scores the entire normalized panel at {p['rejection_score']:.6f}. Comparing it with {p['threshold']:.6f} produces rejection_flag = {str(bool(p['rejection_flag'])).lower()}. The browser checks model identity before displaying it.",
        "operations": "The prepared CSV has its own recorded hash. The container verifier can send it to the service and compare its score, flag, threshold, and model version with the locally loaded predictor.",
    }
    return f'<p class="trace"><strong>Follow {esc(example["specimen"])}.</strong> {esc(traces[chapter])}</p>'


def validate_html(document: str) -> None:
    from html.parser import HTMLParser

    class References(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = []
            self.links = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                self.ids.append(attrs["id"])
            if "href" in attrs:
                self.links.append(attrs["href"])
            if tag in {"script", "img", "iframe"} and "src" in attrs:
                raise ValueError("The guide must embed all its display dependencies.")

    refs = References()
    refs.feed(document)
    if len(refs.ids) != len(set(refs.ids)):
        raise ValueError("Duplicate HTML anchor IDs")
    identifiers = set(refs.ids)
    for link in refs.links:
        if link.startswith("#"):
            if unquote(link[1:]) not in identifiers:
                raise ValueError(f"Broken in-guide link: {link}")
        elif not urlsplit(link).scheme:
            relative = unquote(urlsplit(link).path)
            destination = (OUTPUT.parent / relative).resolve()
            generated = {OUTPUT.resolve(), (CONTENT / "build_manifest.json").resolve()}
            if destination not in generated and not destination.is_file():
                raise ValueError(f"Broken local documentation link: {link}")


def build(recorded_revision: dict | None = None) -> tuple[str, str]:
    chapters = [json.loads(read(f"docs/code_guide/{name}.json")) for name in CHAPTERS]
    diagrams = json.loads(read("docs/code_guide/diagrams.json"))
    example = json.loads(read("docs/code_guide/specimen.json"))
    for path, expected in example["provenance"]["source_sha256"].items():
        if digest(path) != expected:
            raise ValueError("Specimen calculation source changed; rebuild with --refresh-example.")
    functions = {(f["path"], f["symbol"]): f for chapter in chapters for f in chapter["functions"]}
    count = sum(len(chapter["functions"]) for chapter in chapters)
    if count != len(functions):
        raise ValueError("Each critical function should have one explanation.")
    source_paths = {item["path"] for chapter in chapters for item in chapter["functions"]}
    source_paths.update(
        check["path"]
        for chapter in chapters
        for item in chapter["functions"]
        for check in item["checks"]
    )
    revision = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", *sorted(source_paths)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    revision_files = subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "experiments", "tests", "scripts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    changed_source = [line for line in revision_files if "build_code_guide.py" not in line]
    source_state = (
        "working source differs from HEAD" if changed_source else "application source matches HEAD"
    )
    # A documentation commit changes HEAD. Reference metadata is informational;
    # --check retains the recorded build context and verifies exact input hashes.
    if recorded_revision:
        revision = recorded_revision["source_commit"]
        source_state = recorded_revision["source_state"]
    navigation = (
        '<a href="#overview" class="active"><span>00</span>Start here</a>'
        + "".join(
            f'<a href="#{chapter["id"]}"><span>{chapter["number"]}</span>{esc(chapter["title"])}</a>'
            for chapter in chapters
        )
        + '<a href="#source-reference"><span>07</span>Source & maintenance</a>'
    )
    overview_diagram = render_diagram(diagrams["overview"][0], functions)
    index = "".join(
        f'<a href="#{chapter["id"]}">{chapter["number"]} · {esc(chapter["title"])}<small>{esc(chapter["summary"])}</small></a>'
        for chapter in chapters
    )
    sections = []
    for chapter in chapters:
        changes = "".join(
            f'<div class="change-item"><h4>{esc(item["title"])}</h4><p>{prose(item["body"])}</p></div>'
            for item in chapter["changes"]
        )
        exercises = "".join(
            f'<details class="exercise"><summary>{esc(item["question"])}</summary><p>{prose(item["answer"])}</p></details>'
            for item in chapter["exercises"]
        )
        related = "".join(local_link(item["path"], item["label"]) for item in chapter["related"])
        sections.append(
            f'<section class="chapter" id="{chapter["id"]}"><div class="chapter-head"><span class="chapter-num">{chapter["number"]}</span><h2>{esc(chapter["title"])}</h2></div>'
            f'<p class="chapter-summary">{esc(chapter["summary"])}</p>'
            + "".join(render_diagram(diagram, functions) for diagram in diagrams[chapter["id"]])
            + f'<div class="prose">{paragraphs(chapter["story"])}</div>'
            + trace_for(chapter["id"], example)
            + f'<div class="section-tools"><h3>Critical functions</h3><button type="button" data-expand-section="{chapter["id"]}">Expand functions</button></div>'
            + "".join(function_card(item, chapter["title"]) for item in chapter["functions"])
            + f'<h3>If you need to change this part</h3><div class="change-grid">{changes}</div>'
            + f'<h3>Check your understanding</h3>{exercises}<p class="related">Continue in the project: {related}</p></section>'
        )
    catalog = []
    for path in sorted(SOURCES):
        value = SOURCES[path]
        catalog.append(
            f'<details class="source-file" id="{source_id(path)}"><summary>{esc(path)}</summary>'
            f'<p class="source-caption">SHA-256 <code>{digest(path)}</code> · <a href="../{quote(path)}">Open current local file</a></p>'
            f'<div class="source-full">{code_lines(path, 1, len(value.splitlines()), anchors=True)}</div></details>'
        )
    css = read("docs/code_guide/guide.css")
    js = read("docs/code_guide/guide.js")
    read("scripts/build_code_guide.py")
    html_document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A source-linked guide to the kidney biopsy rejection classifier code."><title>Code guide · Kidney biopsy classifier</title><style>{css}</style></head>
<body><a class="skip" href="#overview">Skip to the guide</a>
<aside class="sidebar"><p class="brand">Kidney biopsy classifier</p><p class="side-title">Code guide</p>
<div class="search-wrap screen-only"><label for="guide-search">Find a function or concept</label><input id="guide-search" type="search" placeholder="e.g. threshold, missing target" autocomplete="off"><p id="search-status" class="side-foot" role="status" aria-live="polite"></p><ul id="search-results" class="search-results"></ul></div>
<details class="contents" id="contents" open><summary>Contents and reading controls</summary><nav aria-label="Guide contents">{navigation}</nav><div class="side-tools screen-only"><button type="button" id="expand-all">Expand functions</button><button type="button" id="collapse-all">Collapse functions</button><button type="button" id="print-guide">Print guide</button></div></details><p class="side-foot">6 workflows · {count} function explanations<br>Works offline · source included</p></aside>
<main><header id="overview"><p class="eyebrow">Read the workflow. Understand the code. Make a checked change.</p><h1>How this project works</h1><p class="lead">From raw biopsy measurements to a model score: the scripts, the decisions inside them, and the checks used to verify their behavior.</p>
<div class="meta"><span>Guide edition: September 21, 2026</span><span>Source reference: <code>{revision[:12]}</code></span><span>{source_state}</span><span>Frozen service: <code>20260915_shared</code></span></div>
<div class="prose"><p>This guide follows the current binary rejection classifier. Start with the diagrams, then open a function to inspect its inputs, steps, design choices, failure behavior, and checks. Underlined functions in a diagram jump directly to their explanations. The source excerpts and linked test code are embedded, so they remain readable when this HTML file is copied elsewhere.</p><p>The molecular measurements classify a specimen's recorded diagnosis. The software returns a model score and a flag at a frozen research threshold. The project motivates a molecular second opinion; these results do not establish added benefit in uncertain clinical cases.</p></div>
<div class="legend"><span><b>Green / blue boxes:</b> code or entry points</span><span><b>Dashed amber boxes:</b> saved data or artifacts</span><span><b>Solid arrows:</b> calls or execution</span><span><b>Dashed arrows:</b> reads or writes</span></div>
{overview_diagram}<p class="rule"><strong>The important connection:</strong> training saves a model, schema, threshold, and manifest. The server reads those files at startup. Training and prediction both call the same preprocessing code.</p>
{specimen_block(example)}<div class="index-grid">{index}</div><p class="print-note">Source listings are available in the HTML edition. Printing expands all function explanations and exercise answers.</p></header>
{"".join(sections)}
<section class="chapter" id="source-reference"><div class="chapter-head"><span class="chapter-num">07</span><h2>Source & maintenance</h2></div>
<p class="chapter-summary">The explanations are hand-written; the source excerpts, symbol links, and file hashes are checked during the build.</p>
<div class="prose"><p>The diagrams deliberately show the important calls and artifact transfers, rather than every helper or import. A module can appear in several workflows because its responsibilities are shared. Historical copies under <code>results/</code> preserve earlier experiments; the active implementation is under <code>src/</code>, <code>experiments/</code>, and <code>scripts/</code>.</p><p>Each function's source link opens the corresponding embedded file at its recorded line. Links labeled “Open current local file” and the related documentation links require the surrounding checkout. Diagram links, explanations, tests, search, and print work in the standalone file.</p></div>
<h3>Update this guide after changing code</h3><ol class="steps"><li>Edit the chapter JSON under <code>docs/code_guide/</code>. Update the workflow relationships in <code>diagrams.json</code> if calls or saved files change.</li><li>Run <code>uv run --frozen python scripts/build_code_guide.py</code> from the project root. The builder rejects missing symbols, missing files, broken anchors, and diagram nodes without explanations.</li><li>If preprocessing, prediction, or walkthrough code changed, use <code>uv run --frozen python scripts/build_code_guide.py --refresh-example</code> to recalculate the public example with the project-controlled frozen model. A normal build needs no model or raw assay files.</li><li>Review changed explanations against the source. The build checks references and captures hashes; it cannot determine whether prose still explains the implementation correctly.</li><li>Run <code>uv run --frozen python scripts/build_code_guide.py --check</code>, then open the HTML and inspect the affected diagrams and links. Commit the editable sources, generated HTML, and <code>docs/code_guide/build_manifest.json</code> together.</li></ol>
<h3>Scope of the source record</h3><p>The latest commit affecting the documented source at build time was <code>{revision}</code>; {source_state}. Exact input hashes are recorded in <a href="code_guide/build_manifest.json">build_manifest.json</a>. The public specimen record identifies its model run, prepared CSV hash, and calculation source hashes. Existing model results and verification reports are historical evidence; building this guide is not a new training run or a rerun of those software checks.</p>
<div class="source-catalog"><h3>Embedded source and test reference</h3>{"".join(catalog)}</div></section>
<footer>Prepared with Codex assistance from this project's active source, tests, and recorded artifacts. The guide's reference checks do not replace review of its explanations. Editable content: <a href="code_guide/README.md">docs/code_guide/README.md</a>.</footer>
</main><script>{js}</script></body></html>"""
    validate_html(html_document)
    manifest = {
        "guide": "docs/CODE_GUIDE.html",
        "guide_sha256": hashlib.sha256(html_document.encode("utf-8")).hexdigest(),
        "source_commit": revision,
        "source_state": source_state,
        "chapters": len(chapters),
        "function_explanations": count,
        "diagrams": sum(len(items) for items in diagrams.values()),
        "source_files_embedded": len(SOURCES),
        "inputs": [{"file": path, "sha256": digest(path)} for path in sorted(INPUTS)],
    }
    return html_document, json.dumps(manifest, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-example", action="store_true")
    args = parser.parse_args()
    if args.check and args.refresh_example:
        parser.error("--check does not write files; run --refresh-example separately")
    if args.refresh_example:
        refresh_example()
    recorded = None
    if args.check and (CONTENT / "build_manifest.json").is_file():
        recorded = json.loads((CONTENT / "build_manifest.json").read_text(encoding="utf-8"))
    document, manifest = build(recorded)
    destinations = {OUTPUT: document, CONTENT / "build_manifest.json": manifest}
    if args.check:
        stale = [
            path.relative_to(ROOT).as_posix()
            for path, expected in destinations.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != expected
        ]
        if stale:
            raise SystemExit("Guide is stale; rebuild: " + ", ".join(stale))
        print("PASS: guide, source symbols, local links, anchors, and input hashes are current.")
    else:
        for path, content in destinations.items():
            path.write_text(content, encoding="utf-8", newline="\n")
        print(
            f"Built {OUTPUT.relative_to(ROOT).as_posix()} ({len(document.encode('utf-8')):,} bytes)"
        )


if __name__ == "__main__":
    main()
