"""Check package requirements and record the exact presentation sources/outputs."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation"
data = json.loads((OUT / "source/speaking_script.json").read_text(encoding="utf-8"))
with zipfile.ZipFile(OUT / "unos_kidney_biopsy.pptx") as archive:
    parts = archive.namelist()
    slides = [name for name in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
    charts = [name for name in parts if re.search(r"/charts/chart\d+\.xml$", name)]
    workbooks = [name for name in parts if name.endswith(".xlsx")]
    assert len(slides) == len(data['slides']) + len(data['backups'])
    assert not any("notes" in name.lower() for name in parts)
    assert len(charts) == 2 and len(workbooks) == 2
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    tables = sum(len(ET.fromstring(archive.read(name)).findall(".//a:tbl", ns)) for name in slides)
assert len(PdfReader(OUT / "unos_kidney_biopsy.pdf").pages) == len(slides)
assert sum(slide["seconds"] for slide in data["slides"]) == 1200
sources = [
    "results/analysis/20260915_baseline/model_metrics.csv",
    "results/analysis/20260915_baseline/reliability_bins.csv",
    "results/analysis/20260915_baseline/errors_by_diagnosis.csv",
    "results/analysis/20260915_baseline/paired_differences.csv",
    "results/reproduction/20260915_shared/data_audit.json",
    "results/followup/20260917_stability/summary.json",
    "results/followup/20260915_subtypes/any_rejection_metrics.csv",
    "results/checks/20260917_coherence/checks.json",
    "results/checks/20260917_coherence/http/http.json",
    "docs/RESEARCH_CONTEXT.md",
    "docs/PRESENTATION_GUIDE.md",
    "docs/PRESENTATION_SPEC.md",
    "docs/references/STUDY_AUDIT_20260919.md",
    "docs/references/rejection_source_manifest.json",
]


def sha(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


manifest = {
    "created": "2026-09-19",
    "revision": "study-source pass: revised sequence, examples, error definitions and verified study population",
    "main_slides": len(data['slides']),
    "backup_slides": len(data['backups']),
    "planned_seconds": 1200,
    "main_spoken_words": sum(len(" ".join(s["paragraphs"]).split()) for s in data["slides"]),
    "powerpoint_notes_parts": 0,
    "native_tables": tables,
    "native_charts": len(charts),
    "embedded_chart_workbooks": len(workbooks),
    "rehearsals": "pending",
    "sources": {name: sha(ROOT / name) for name in sources},
    "outputs_and_authoring_sources": {
        file.relative_to(ROOT).as_posix(): sha(file)
        for file in sorted(OUT.rglob("*"))
        if file.is_file() and file.name != "manifest.json"
    },
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: v for k, v in manifest.items() if k not in ("sources", "outputs_and_authoring_sources")}, indent=2))
