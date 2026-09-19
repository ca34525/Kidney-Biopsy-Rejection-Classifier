"""Build the static PDF and offline demo capture page from verified local images."""
from pathlib import Path
import base64
import json

from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "presentation"
data = json.loads((OUT / "source/speaking_script.json").read_text(encoding="utf-8"))
slides = data["slides"] + data["backups"]
demo_slide = next(slide["id"] for slide in data["slides"] if slide["title"] == "One public specimen through the service")
pdf = canvas.Canvas(str(OUT / "unos_kidney_biopsy.pdf"), pagesize=(960, 540))
pdf.setTitle("Classifying Kidney Transplant Rejection from Biopsy RNA")
pdf.setSubject(f"{len(data['slides'])} main slides and {len(data['backups'])} backup slides. Speaking script is a separate HTML file.")
for i, slide in enumerate(slides, 1):
    pdf.bookmarkPage(f"slide{i}")
    pdf.addOutlineEntry(f"{i:02d}. {slide['title']}", f"slide{i}", level=0)
    pdf.drawImage(str(OUT / f"slides/slide-{i:02d}.png"), 0, 0, width=960, height=540)
    pdf.showPage()
pdf.save()


def image(name: str) -> str:
    encoded = base64.b64encode((OUT / "assets" / name).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


(OUT / "demo_fallback.html").write_text(f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Captured demonstration · kidney biopsy classifier</title>
<style>body{{margin:0;font-family:Arial,sans-serif;background:#F7F8F5;color:#16343E}}header{{padding:24px 4vw;background:#16343E;color:white}}h1{{font-size:28px;margin:0 0 10px}}p{{line-height:1.5}}nav{{display:flex;gap:30px}}a{{color:inherit}}main{{max-width:1440px;margin:auto;padding:20px}}img{{display:block;width:100%;height:auto;border:1px solid #CEDBD7}}section{{margin:30px 0 60px}}h2{{font-size:26px}}code{{overflow-wrap:anywhere}}@media print{{header{{background:white;color:#16343E}}section{{break-before:page}}}}</style>
<header><h1>Captured local demonstration</h1><p>Actual browser captures, 18 September 2026. This page works offline.</p>
<nav><a href="#valid">Valid public specimen</a><a href="#invalid">Missing IFNG</a><a href="speaking_script.html#slide-{demo_slide}">Speaking script</a></nav></header>
<main><p>Saved model: <code>20260915_shared:any_rejection:catboost_all_depth4</code><br>
Threshold: 0.8765880870219778. The public discovery-screen example demonstrates software behavior, not new validation.</p>
<section id="valid"><h2>GSM6510425 produces a model score of 0.274934</h2>
<p>The score is below the selected threshold. Its flag agrees with the recorded no-rejection diagnosis.</p>
<img src="{image('demo-valid.png')}" alt="Actual local application displaying specimen GSM6510425, normalized IFNG minus 5.578 and model score 0.275"></section>
<section id="invalid"><h2>Removing IFNG stops scoring</h2><p>The application clears the previous result and reports the missing target.</p>
<img src="{image('demo-invalid.png')}" alt="Actual local application reporting Missing required assay targets: IFNG and showing no prediction"></section></main></html>''', encoding="utf-8", newline="\n")
print(f"Created matching {len(slides)}-page PDF and offline demonstration capture page")
