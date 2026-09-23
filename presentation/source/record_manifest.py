"""Check package requirements and record the exact presentation sources/outputs."""
from pathlib import Path
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation"
EXPECTED_MAIN_SLIDES = 14
EXPECTED_BACKUP_SLIDES = 0
EXPECTED_CHART_SLIDES = [12]
REVISED_SLIDES = [4, 12, 13, 14]
REVISED_NARRATION_SLIDES = [3, 4, 13, 14]
PRESERVED_SLIDES = [n for n in range(1, 13) if n not in REVISED_SLIDES]
BASELINE = ROOT / "build/presentation/before-final-pass-20260923/presentation/unos_kidney_biopsy.pptx"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}


def sha(file: Path) -> str:
    return hashlib.sha256(file.read_bytes()).hexdigest()


def relationships(archive: zipfile.ZipFile, part: str) -> dict:
    """Resolve package references independently of exporter-generated IDs."""
    folder, name = posixpath.split(part)
    rel_part = posixpath.join(folder, "_rels", name + ".rels")
    if rel_part not in archive.namelist():
        return {}
    result = {}
    for relation in ET.fromstring(archive.read(rel_part)):
        target = relation.attrib["Target"]
        mode = relation.get("TargetMode", "Internal")
        if mode != "External":
            target = posixpath.normpath(posixpath.join(folder, target)).lstrip("/")
        result[relation.attrib["Id"]] = (relation.attrib["Type"], target, mode)
    return result


def semantic_xml(archive: zipfile.ZipFile, part: str, *, normalize_chart_whitespace: bool = False, chart_label_aliases: bool = False) -> tuple:
    """Keep content, formatting and geometry, omitting volatile creation IDs."""
    references = relationships(archive, part)

    def element_value(element: ET.Element) -> tuple:
        attributes = []
        for key, value in element.attrib.items():
            if key.startswith("{" + REL_NS + "}"):
                value = references[value]
            attributes.append((key, value))
        element_text = element.text or ""
        if chart_label_aliases:
            element_text = {
                "False negatives / 169": "Missed cases / 169",
                "False positives / 176": "Incorrect flags / 176",
            }.get(element_text, element_text)
        if normalize_chart_whitespace and element.tag == "{" + NS["c"] + "}v":
            element_text = " ".join(element_text.split())
        return (
            element.tag,
            tuple(sorted(attributes)),
            element_text,
            tuple(
                element_value(child)
                for child in element
                if child.tag.rsplit("}", 1)[-1] != "creationId"
            ),
        )

    return element_value(ET.fromstring(archive.read(part)))


data = json.loads((OUT / "source/speaking_script.json").read_text(encoding="utf-8"))
assert len(data["slides"]) == EXPECTED_MAIN_SLIDES
assert len(data.get("backups", [])) == EXPECTED_BACKUP_SLIDES
browser_stops = data["browser_demo"]["stops"]
assert data["browser_demo"]["after_slide"] == 13
assert [stop["id"] for stop in browser_stops] == ["evidence", "specimen", "engineering"]
assert sum(stop["seconds"] for stop in browser_stops) == 450
assert sorted(file.name for file in (OUT / "slides").glob("slide-*.png")) == [
    f"slide-{n:02d}.png" for n in range(1, EXPECTED_MAIN_SLIDES + 1)
]
preservation = {
    "baseline": BASELINE.relative_to(ROOT).as_posix(),
    "status": "not checked: archived baseline is unavailable",
}
with zipfile.ZipFile(OUT / "unos_kidney_biopsy.pptx") as archive:
    parts = archive.namelist()
    slides = [name for name in parts if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
    charts = [name for name in parts if re.search(r"/charts/chart\d+\.xml$", name)]
    workbooks = [name for name in parts if name.endswith(".xlsx")]
    assert len(slides) == EXPECTED_MAIN_SLIDES + EXPECTED_BACKUP_SLIDES
    assert not any("notes" in name.lower() for name in parts)
    assert len(charts) == len(workbooks) == len(EXPECTED_CHART_SLIDES)
    chart_slides = sorted(
        int(re.search(r"slide(\d+)\.xml$", name).group(1))
        for name in slides
        if ET.fromstring(archive.read(name)).findall(".//c:chart", NS)
    )
    assert chart_slides == EXPECTED_CHART_SLIDES
    tables = sum(len(ET.fromstring(archive.read(name)).findall(".//a:tbl", NS)) for name in slides)
    # The archive is a local revision aid, not a dependency of a clean checkout.
    # Main-slide renders are compared separately during visual review.
    if BASELINE.exists():
        with zipfile.ZipFile(BASELINE) as original:
            for number in PRESERVED_SLIDES:
                name = f"ppt/slides/slide{number}.xml"
                assert semantic_xml(archive, name) == semantic_xml(original, name), (
                    f"Preserved slide {number} changed its content, formatting, or geometry."
                )
            for name in charts:
                # This revision removes the viewer-dependent legend only.
                current = ET.fromstring(archive.read(name))
                previous = ET.fromstring(original.read(name))
                previous_chart = previous.find("c:chart", NS)
                previous_chart.remove(previous_chart.find("c:legend", NS))
                assert ET.tostring(current) == ET.tostring(previous), (
                    f"Chart data or styling changed beyond the requested legend: {name}"
                )
        preservation = {
            "baseline": BASELINE.relative_to(ROOT).as_posix(),
            "baseline_sha256": sha(BASELINE),
            "status": "passed",
            "slides": PRESERVED_SLIDES,
            "comparison": "Unrevised slide XML preserved. Chart XML preserved except for removing the automatic legend; editable keys on slide 12 set its order. Generated creation IDs ignored and relationship IDs resolved.",
        }
        previous_script = json.loads((BASELINE.parent / "source/speaking_script.json").read_text(encoding="utf-8"))
        for current, previous in zip(data["slides"][:12], previous_script["slides"][:12], strict=True):
            assert current["id"] == previous["id"]
            assert current["seconds"] == previous["seconds"]
            if current["id"] not in REVISED_NARRATION_SLIDES:
                assert current == previous, f"Unrevised narration changed on slide {current['id']}"
assert len(PdfReader(OUT / "unos_kidney_biopsy.pdf").pages) == len(slides)
assert sum(slide["seconds"] for slide in data["slides"] + browser_stops) == 1200
sources = [
    "results/reproduction/baseline/biopsy_screen.csv",
    "results/analysis/20260915_baseline/REPORT.md",
    "results/reproduction/20260915_shared/configuration.json",
    "results/analysis/20260915_baseline/model_metrics.csv",
    "results/analysis/20260915_baseline/reliability_bins.csv",
    "results/analysis/20260915_baseline/errors_by_diagnosis.csv",
    "results/analysis/20260915_baseline/paired_differences.csv",
    "results/reproduction/20260915_shared/data_audit.json",
    "results/followup/20260917_stability/summary.json",
    "results/followup/20260917_stability/selections.csv",
    "results/followup/20260917_stability/design.json",
    "results/followup/20260915_subtypes/any_rejection_metrics.csv",
    "results/checks/20260917_coherence/checks.json",
    "results/checks/20260917_coherence/http/http.json",
    "results/checks/20260917_coherence/container.json",
    "results/checks/20260915_application/fresh_setup_final.json",
    "src/kidney_biopsy/prediction.py",
    "src/kidney_biopsy/preprocessing.py",
    "src/kidney_biopsy/api.py",
    "experiments/rejection_public/run.py",
    "tests/test_api.py",
    "scripts/verify_http_service.py",
    "scripts/verify_container.py",
    "scripts/verify_fresh_setup.py",
    "docs/JOB_REQUIREMENTS.md",
    "docs/PROJECT_SPEC.md",
    "docs/NEXT_STEPS.md",
    "docs/references/JOB_DESCRIPTION.txt",
    "docs/API.md",
    "docs/CODE_GUIDE.md",
    "docs/VERIFICATION.md",
    "docs/CONTAINERS.md",
    ".github/workflows/checks.yml",
    "pyproject.toml",
    "uv.lock",
    "Dockerfile",
    "docs/RESEARCH_CONTEXT.md",
    "docs/PRESENTATION_GUIDE.md",
    "docs/PRESENTATION_SPEC.md",
    "docs/references/STUDY_AUDIT_20260919.md",
    "docs/references/BIOPSY_CARE_20260919.md",
    "docs/references/PRESENTATION_WORDING_20260921.md",
    "docs/references/PRESENTATION_REFRAMING_20260921.md",
    "docs/references/PRESENTATION_PURPOSE_20260921.md",
    "docs/references/PRESENTATION_CONTEXT_PASS_20260922.md",
    "docs/references/PRACTICAL_PURPOSE_20260922.md",
    "docs/references/ENGINEERING_DEMO_20260922.md",
    "docs/references/PRESENTATION_FINAL_PASS_20260923.md",
    "presentation/engineering_demo_sources.json",
    "docs/references/rejection_source_manifest.json",
]


manifest = {
    "created": "2026-09-23",
    "revision": data.get("revision", data["status"]),
    "main_slides": len(data['slides']),
    "backup_slides": len(data['backups']),
    "browser_stops": len(browser_stops),
    "browser_seconds": sum(stop["seconds"] for stop in browser_stops),
    "planned_seconds": 1200,
    "main_spoken_words": sum(len(" ".join(s["paragraphs"]).split()) for s in data["slides"] + browser_stops),
    "powerpoint_notes_parts": 0,
    "native_tables": tables,
    "native_charts": len(charts),
    "embedded_chart_workbooks": len(workbooks),
    "native_chart_slides": chart_slides,
    "preserved_slides": preservation,
    "revised_slides": REVISED_SLIDES,
    "revised_narration_slides": REVISED_NARRATION_SLIDES,
    "rehearsals": "User reports rehearsing as of 2026-09-23; measured times not supplied",
    "sources": {name: sha(ROOT / name) for name in sources},
    "outputs_and_authoring_sources": {
        file.relative_to(ROOT).as_posix(): sha(file)
        for file in sorted(OUT.rglob("*"))
        if file.is_file() and file.name != "manifest.json" and not file.name.startswith(".~lock.")
    },
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: v for k, v in manifest.items() if k not in ("sources", "outputs_and_authoring_sources")}, indent=2))
