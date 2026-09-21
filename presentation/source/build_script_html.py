"""Build the offline speaking script. Run from the repository root.

The script lives entirely in this HTML deliverable, never in PowerPoint notes.
Slide images are embedded when available so the reading page works offline.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parents[2]


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def clock(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def paragraphs(value: str | list[str] | None) -> str:
    if not value:
        return ""
    parts = value if isinstance(value, list) else value.split("\n\n")
    return "\n".join(f"<p>{escape(part)}</p>" for part in parts if str(part).strip())


def source_href(value: str) -> str:
    """Local sources are repository-relative in JSON and HTML-relative here."""
    if urlsplit(value).scheme in {"https", "http"}:
        return value
    if urlsplit(value).scheme or value.startswith(("/", "\\")):
        raise ValueError(f"Unsupported source URL: {value}")
    clean = value.replace("\\", "/")
    if clean.startswith("../"):
        clean = clean[3:]
    source_path = (ROOT / clean.split("#", 1)[0]).resolve()
    if not source_path.is_relative_to(ROOT) or not source_path.exists():
        raise ValueError(f"Missing or out-of-project source: {value}")
    return "../" + quote(clean, safe="/#:?=&")


def source_list(sources: list[dict | str]) -> str:
    items = []
    for source in sources:
        if isinstance(source, str):
            label = href = source
        else:
            label = source.get("label") or source.get("title") or source.get("path") or source.get("url")
            href = source.get("url") or source.get("path") or source.get("href")
        if not href:
            raise ValueError("Every source needs a path or URL.")
        items.append(f'<li><a href="{escape(source_href(href))}">{escape(label)}</a></li>')
    if not items:
        return ""
    return '<details class="sources"><summary>Sources and evidence</summary><ul>' + "".join(items) + "</ul></details>"


CSS = r"""
.preview-button{display:block;width:100%;padding:0!important;border:0!important;background:transparent!important;cursor:zoom-in}.slide-dialog{border:1px solid #CEDBD7;border-radius:4px;padding:14px;max-width:96vw;width:1280px;background:#F7F8F5}.slide-dialog::backdrop{background:rgba(0,0,0,.72)}.slide-dialog img{display:block;width:100%;max-height:84vh;object-fit:contain}.dialog-actions{display:flex;justify-content:flex-end;margin-bottom:8px}@media print{.slide-dialog{display:none!important}}
:root{--paper:#F6F7F5;--ink:#142F3B;--teal:#007F78;--muted:#53656C;--line:#D5DEDC;--reading-size:21px}
*{box-sizing:border-box}html{scroll-padding-top:106px;scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.5}button,select,input,textarea{font:inherit}button,select{border:1px solid #AEBEBA;background:#fff;color:var(--ink);border-radius:4px;padding:.44rem .68rem}button{cursor:pointer}button:hover{border-color:var(--teal);background:#F0F6F4}button:focus-visible,a:focus-visible,select:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #007F78;outline-offset:3px}a{color:var(--teal);text-underline-offset:3px}h1,h2,h3,p{margin-top:0}.skip{position:fixed;top:-90px;left:12px;z-index:10;background:white;padding:12px}.skip:focus{top:12px}
.toolbar{position:sticky;top:0;z-index:5;background:rgba(246,247,245,.98);border-bottom:1px solid var(--line);padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}.brand{font-size:14px;font-weight:700;letter-spacing:.02em;margin-right:auto}.tools{display:flex;align-items:center;gap:7px}.timer{font-variant-numeric:tabular-nums;font-size:20px;min-width:60px;text-align:center}.timer.over{color:#A84B2D}.tool-label{font-size:12px;color:var(--muted)}.picker{max-width:350px;width:28vw;font-size:14px}.font-size{font-size:13px;min-width:30px;text-align:center}.layout{display:grid;grid-template-columns:236px minmax(0,1fr);max-width:1600px;margin:auto}.index{position:sticky;top:87px;height:calc(100vh - 106px);overflow:auto;padding:30px 16px 30px 24px}.index h2{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:0 0 12px}.index ol{list-style:none;margin:0 0 24px;padding:0}.index a{display:grid;grid-template-columns:24px 1fr;gap:6px;text-decoration:none;padding:8px 10px;margin:1px 0;border-left:3px solid transparent;color:var(--muted);font-size:13px;line-height:1.35}.index a[aria-current=true]{color:var(--ink);background:#E7EFEB;border-color:var(--teal)}.index small{display:block;color:var(--muted);font-size:11px;margin-top:3px}.index .slide-number{font-variant-numeric:tabular-nums;color:var(--teal)}main{padding:40px clamp(26px,4vw,72px) 80px;min-width:0;max-width:1240px}.page-head{max-width:770px;margin:0 0 42px}.eyebrow{font-size:12px;font-weight:bold;letter-spacing:.1em;text-transform:uppercase;color:var(--teal);margin-bottom:12px}h1{font-size:clamp(29px,3vw,42px);font-weight:600;line-height:1.15;margin-bottom:16px}.intro{font-size:17px;color:var(--muted)}.file-links{display:flex;flex-wrap:wrap;gap:18px;font-size:14px}.reader-help{font-size:12px;color:var(--muted);margin-top:16px}kbd{font-family:inherit;font-weight:bold}.slide-section{border-top:1px solid var(--line);padding:35px 0 46px;scroll-margin-top:15px}.slide-heading{display:flex;align-items:baseline;gap:16px;justify-content:space-between;margin-bottom:8px}.slide-heading h2{font-size:clamp(24px,2.2vw,31px);line-height:1.2;margin-bottom:0;font-weight:600}.slide-label{font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:bold;color:var(--teal);margin-bottom:9px}.timing{font-size:14px;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap;margin:0 0 23px}.reader-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(230px,34%);gap:30px;align-items:start}.spoken{font-family:Georgia,'Times New Roman',serif;font-size:var(--reading-size);line-height:1.65;max-width:69ch}.spoken p{margin:0 0 1.04em}.spoken p:last-child{margin-bottom:0}.visual{margin:0;position:sticky;top:102px}.visual img{display:block;width:100%;height:auto;border:1px solid var(--line);background:white}.visual figcaption{font-size:11px;color:var(--muted);margin-top:7px}.visual-placeholder{aspect-ratio:16/9;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;padding:20px;color:var(--muted);text-align:center;font-size:13px}.stage{font:15px/1.55 Arial,Helvetica,sans-serif;margin:0 0 24px;padding:15px 18px;background:#EAF1EE;border-left:3px solid var(--teal)}.stage h3{font-size:11px;text-transform:uppercase;letter-spacing:.08em;margin:0 0 7px;color:var(--teal)}.stage p{margin:0 0 .55em}.stage p:last-child{margin-bottom:0}.stage ul{padding-left:19px;margin:0}.stage li+li{margin-top:5px}.sources{font-size:13px;margin-top:25px;color:var(--muted);overflow-wrap:anywhere}.sources summary{cursor:pointer;color:var(--teal)}.sources ul{margin:10px 0 0;padding-left:18px}.sources li{margin-bottom:8px}.backup-divider{border-top:3px solid var(--ink);padding-top:25px;margin:18px 0 0}.backup-divider h2{font-size:27px;margin-bottom:9px}.backup-divider p{color:var(--muted);font-size:15px}.closing{border-top:1px solid var(--line);padding:26px 0 0;max-width:760px}.closing h2{font-size:24px;margin-bottom:12px}.closing p,.closing li{font-size:15px;color:var(--muted)}.closing details{margin-top:24px}.closing summary{cursor:pointer;color:var(--teal)}.log-form{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:18px}.log-form label{font-size:13px;display:grid;gap:5px}.log-form input,.log-form textarea{padding:9px;border:1px solid #AEBEBA;border-radius:4px;background:white;color:var(--ink);min-width:0}.log-form .wide{grid-column:1/-1}.log-actions{display:flex;gap:12px;align-items:center}.log-status{font-size:12px;color:var(--muted)}.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(min-width:1550px){.spoken{max-width:65ch}.reader-grid{gap:42px}}
@media(max-width:1120px){.reader-grid{grid-template-columns:1fr}.visual{position:static;max-width:540px;grid-row:1}.visual img{max-height:304px;object-fit:contain;object-position:left}.toolbar{gap:10px;padding:10px 18px}.brand{display:none}.picker{margin-right:auto;width:32vw}.index{top:78px}.spoken{max-width:68ch}}
@media(max-width:820px){.layout{display:block}.index{display:none}main{padding:27px 22px 60px}.toolbar{gap:9px}.picker{max-width:none;flex:1;width:auto;min-width:160px}.reader-grid{gap:22px}.page-head{margin-bottom:30px}.toolbar .tool-label,.toolbar .font-size{display:none}.slide-section{padding:29px 0 36px}.spoken{font-size:var(--reading-size)}.timing{font-size:13px}.reader-help{line-height:1.6}.tools.font-tools{gap:4px}.log-form{grid-template-columns:1fr}.slide-heading{display:block}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@page{size:A4;margin:17mm 18mm}
@media print{html{scroll-padding:0}body{background:#fff;color:#142F3B}.toolbar,.index,.skip,.reader-help,.file-links,.log-form,.log-intro{display:none!important}.layout{display:block}main{padding:0;max-width:none}.page-head{margin-bottom:8mm}h1{font-size:25pt}.intro{font-size:10pt}.slide-section{break-before:page;padding:0;border:0}.slide-heading h2{font-size:19pt}.slide-label{font-size:9pt}.timing{font-size:10pt;margin-bottom:5mm}.reader-grid{display:block}.visual{position:static;max-width:100mm;margin-bottom:5mm;break-inside:avoid}.visual figcaption{font-size:8pt}.spoken{font-size:12pt;line-height:1.5;max-width:none}.stage{font-size:10pt;line-height:1.4;margin-bottom:5mm;padding:3mm 4mm;break-inside:avoid;-webkit-print-color-adjust:exact;print-color-adjust:exact}.stage h3{font-size:8pt}.sources{font-size:8pt;margin-top:5mm;break-inside:avoid}.sources summary{display:none}.sources>ul{display:block!important;margin:0}.sources li{margin-bottom:2mm}.sources a{text-decoration:none}.backup-divider{break-before:page;padding-top:0;border:0}.backup-divider+.slide-section{break-before:auto;margin-top:8mm}.closing{break-before:page;border:0;padding:0}.closing p,.closing li{font-size:11pt}.closing details{display:none}.page-head,.slide-heading{break-after:avoid}.spoken p{orphans:3;widows:3}}
"""


JS = r"""
(() => {
  'use strict';
  const slideDialog = document.querySelector('#slide-dialog');
  const enlargedSlide = slideDialog.querySelector('img');
  document.querySelectorAll('.preview-button').forEach(button => button.addEventListener('click', () => {
    const preview = button.querySelector('img');
    enlargedSlide.src = preview.src;
    enlargedSlide.alt = preview.alt;
    slideDialog.showModal();
  }));
  slideDialog.querySelector('button').addEventListener('click', () => slideDialog.close());
  const sections = [...document.querySelectorAll('.slide-section')];
  const picker = document.querySelector('#slide-picker');
  const links = [...document.querySelectorAll('.index a')];
  let active = 0;
  function setActive(index) {
    active = Math.max(0, Math.min(sections.length - 1, index));
    picker.value = sections[active].id;
    links.forEach(a => a.setAttribute('aria-current', String(a.hash === '#' + sections[active].id)));
  }
  function jump(index) {
    setActive(index);
    sections[active].scrollIntoView({behavior: 'instant'});
    history.replaceState(null, '', '#' + sections[active].id);
  }
  picker.addEventListener('change', () => jump(sections.findIndex(s => s.id === picker.value)));
  links.forEach(a => a.addEventListener('click', event => {
    event.preventDefault(); jump(sections.findIndex(s => '#' + s.id === a.hash));
  }));
  document.querySelector('#previous').addEventListener('click', () => jump(active - 1));
  document.querySelector('#next').addEventListener('click', () => jump(active + 1));
  document.addEventListener('keydown', event => {
    if (/INPUT|TEXTAREA|SELECT|BUTTON/.test(event.target.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === 'ArrowRight') { event.preventDefault(); jump(active + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); jump(active - 1); }
  });
  let scrollQueued = false;
  document.addEventListener('scroll', () => {
    if (scrollQueued) return;
    scrollQueued = true;
    requestAnimationFrame(() => {
      let nearest = 0;
      sections.forEach((section, i) => { if (section.getBoundingClientRect().top < innerHeight * .38) nearest = i; });
      setActive(nearest); scrollQueued = false;
    });
  }, {passive:true});
  const initial = sections.findIndex(s => '#' + s.id === location.hash);
  setActive(initial < 0 ? 0 : initial);
  let fontSize = 21;
  function resize(amount) {
    fontSize = Math.max(17, Math.min(29, fontSize + amount));
    document.documentElement.style.setProperty('--reading-size', fontSize + 'px');
    document.querySelector('#font-value').textContent = fontSize + 'px';
    sections[active].scrollIntoView({behavior: 'instant'});
  }
  document.querySelector('#smaller').addEventListener('click', () => resize(-2));
  document.querySelector('#larger').addEventListener('click', () => resize(2));
  let accumulated = 0, started = null;
  const timer = document.querySelector('#elapsed');
  const timerButton = document.querySelector('#timer-toggle');
  const format = seconds => Math.floor(seconds / 60) + ':' + String(Math.floor(seconds % 60)).padStart(2, '0');
  function elapsed() { return accumulated + (started === null ? 0 : (performance.now() - started) / 1000); }
  function updateTimer() {
    const seconds = elapsed(); timer.textContent = format(seconds);
    timer.classList.toggle('over', seconds > 1200);
  }
  timerButton.addEventListener('click', () => {
    if (started === null) { started = performance.now(); timerButton.textContent = 'Pause'; }
    else { accumulated = elapsed(); started = null; timerButton.textContent = 'Resume'; }
    updateTimer();
  });
  document.querySelector('#timer-reset').addEventListener('click', () => {
    accumulated = 0; started = null; timerButton.textContent = 'Start'; updateTimer();
  });
  setInterval(updateTimer, 250);
  document.querySelector('#rehearsal-date').value = new Date().toLocaleDateString('en-CA');
  document.querySelector('#use-timer').addEventListener('click', () => {
    document.querySelector('#rehearsal-duration').value = format(elapsed());
  });
  document.querySelector('#export-log').addEventListener('click', () => {
    const date = document.querySelector('#rehearsal-date').value;
    const duration = document.querySelector('#rehearsal-duration').value.trim();
    const kind = document.querySelector('#rehearsal-kind').value;
    const notes = document.querySelector('#rehearsal-notes').value.trim();
    const status = document.querySelector('#log-status');
    if (!date || !duration) { status.textContent = 'Enter the date and measured duration first.'; return; }
    const text = 'Kidney biopsy presentation rehearsal\n\nDate: ' + date + '\nRun: ' + kind + '\nMeasured duration: ' + duration + '\nPlanned duration: 20:00\n\nNotes\n' + (notes || '(No notes entered)') + '\n';
    const url = URL.createObjectURL(new Blob([text], {type:'text/plain;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'rehearsal-' + date + '.txt';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = 'Rehearsal record exported. Keep the downloaded file with the presentation.';
  });
  window.addEventListener('beforeprint', () => document.querySelectorAll('.sources').forEach(d => { d.dataset.wasOpen = String(d.open); d.open = true; }));
  window.addEventListener('afterprint', () => document.querySelectorAll('.sources').forEach(d => { d.open = d.dataset.wasOpen === 'true'; }));
})();
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="presentation/source/speaking_script.json")
    parser.add_argument("--output", default="presentation/speaking_script.html")
    parser.add_argument("--require-images", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / args.source).read_text(encoding="utf-8-sig"))
    main_slides = data["slides"]
    slides = [
        {**slide, "number": index, "backup": False}
        for index, slide in enumerate(main_slides, start=1)
    ] + [
        {**slide, "number": index, "backup": True}
        for index, slide in enumerate(data.get("backups", []), start=len(main_slides) + 1)
    ]
    total = sum(int(s["seconds"]) for s in main_slides)
    if total != 1200:
        raise ValueError(f"Main presentation must total 20:00, got {clock(total)}.")
    sections, main_links, backup_links, main_options, backup_options = [], [], [], [], []
    elapsed = image_count = words = 0
    backup_started = False
    for position, slide in enumerate(slides, start=1):
        number = int(slide.get("number", position))
        title = slide["title"]
        backup = bool(slide.get("backup", False))
        seconds = int(slide.get("seconds", 0))
        ident = f"slide-{number:02d}"
        label = f"Backup {number - len(main_slides)}" if backup else f"Slide {number}"
        timing = "For questions after the 20-minute talk" if backup else f"Approximate pacing: {clock(seconds)} on this slide"
        if not backup:
            elapsed += seconds
        if backup and not backup_started:
            sections.append('<div class="backup-divider"><h2>Backup slides</h2><p>Use these for questions. They are outside the planned 20 minutes.</p></div>')
            backup_started = True
        image_path = ROOT / "presentation" / "slides" / f"slide-{number:02d}.png"
        if image_path.exists():
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            visual = f'<button class="preview-button" aria-label="Enlarge {escape(label.lower())}"><img src="data:image/png;base64,{encoded}" alt="{escape(label + ": " + title)}" width="1600" height="900"></button>'
            image_count += 1
        elif args.require_images:
            raise FileNotFoundError(image_path)
        else:
            visual = '<div class="visual-placeholder">Slide image will appear after the deck is rendered and this file is rebuilt.</div>'
        spoken = slide["paragraphs"]
        words += 0 if backup else len(re.findall(r"\S+", " ".join(spoken) if isinstance(spoken, list) else spoken))
        directions = slide.get("actions", [])
        stage_html = ''
        if directions:
            stage_html = '<aside class="stage"><h3>Delivery cues · not read aloud</h3>' + paragraphs(directions) + '</aside>'
        cue_list = slide.get("visible_cues", [])
        screen_cues = ''
        if cue_list:
            screen_cues = '<details class="sources"><summary>On this slide</summary><ul>' + ''.join(f'<li>{escape(cue)}</li>' for cue in cue_list) + '</ul></details>'
        sections.append(f'''<section class="slide-section" id="{ident}" aria-labelledby="title-{number}">
<p class="slide-label">{escape(label)}</p><div class="slide-heading"><h2 id="title-{number}">{escape(title)}</h2></div>
<p class="timing">{escape(timing)}</p><div class="reader-grid"><div>{stage_html}<div class="spoken">{paragraphs(spoken)}</div>{source_list(slide.get("sources", []))}</div>
<figure class="visual">{visual}<figcaption>{escape(label)} as shown to the audience. Click to enlarge.</figcaption>{screen_cues}</figure></div></section>''')
        nav_time = "Questions" if backup else f"About {clock(seconds)}"
        link = f'<li><a href="#{ident}"><span class="slide-number">{number:02d}</span><span>{escape(title)}<small>{nav_time}</small></span></a></li>'
        option = f'<option value="{ident}">{number:02d}. {escape(title)}</option>'
        (backup_links if backup else main_links).append(link)
        (backup_options if backup else main_options).append(option)
    title = data.get("title", "Kidney biopsy rejection classifier")
    title = re.sub(r"\s*[—–-]\s*speaking script$", "", title, flags=re.IGNORECASE)
    backup_picker = '<optgroup label="Backup slides">' + ''.join(backup_options) + '</optgroup>' if backup_options else ''
    backup_navigation = '<h2>For questions</h2><ol>' + ''.join(backup_links) + '</ol>' if backup_links else ''
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Offline speaking script for the 20-minute kidney biopsy classifier presentation."><title>{escape(title)} · Speaking script</title><style>{CSS}</style></head>
<body><a class="skip" href="#script">Skip to speaking script</a>
<header class="toolbar"><span class="brand">Speaking script</span><label class="visually-hidden" for="slide-picker">Go to slide</label>
<select class="picker" id="slide-picker"><optgroup label="Main talk · 20 minutes">{''.join(main_options)}</optgroup>{backup_picker}</select>
<div class="tools"><button id="previous" aria-label="Previous slide" title="Previous slide (left arrow)">←</button><button id="next" aria-label="Next slide" title="Next slide (right arrow)">→</button></div>
<div class="tools font-tools"><button id="smaller" aria-label="Decrease script font size">A−</button><span class="font-size" id="font-value" aria-live="polite">21px</span><button id="larger" aria-label="Increase script font size">A+</button></div>
<div class="tools"><span class="tool-label">Rehearsal</span><output class="timer" id="elapsed" aria-label="Elapsed rehearsal time">0:00</output><button id="timer-toggle">Start</button><button id="timer-reset">Reset</button></div></header>
<div class="layout"><nav class="index" aria-label="Slide index"><h2>Main talk · 20:00</h2><ol>{''.join(main_links)}</ol>{backup_navigation}</nav>
<main id="script"><div class="page-head"><h1>{escape(title)}</h1>
<p class="intro">Words to say aloud, with delivery cues and the matching slides. The main talk is planned for 20 minutes. Questions follow.</p>
<div class="file-links"><a href="unos_kidney_biopsy.pptx">PowerPoint slides</a><a href="unos_kidney_biopsy.pdf">PDF backup</a><a href="analysis_report.html">Analysis report</a><a href="http://127.0.0.1:8765">Local demonstration</a><a href="demo_fallback.html">Captured demo backup</a></div>
<p class="reader-help">Use the slide index or <kbd>←</kbd> / <kbd>→</kbd> to move between slides. <kbd>A−</kbd> / <kbd>A+</kbd> changes the reading size. This file works offline. Links to the local demo require the application to be running.</p></div>
{''.join(sections)}
<section class="closing" id="rehearsal"><h2>Rehearsal record</h2><p>The timings above are a plan. No completed rehearsal is recorded in this deliverable. Complete two full timed runs and one run using the demonstration fallback before presenting.</p>
<p>Check the time at section boundaries. Keep the result counts, the report walkthrough, and the valid and invalid demonstration. If delivery runs long, shorten secondary explanations. Use rehearsal to adjust the pace. The report and Code Guide remain available for questions.</p>
<details><summary>Record a rehearsal</summary><p class="log-intro">Enter the measured time after a run and export the record. Entries remain on this page only until it is closed or reloaded.</p>
<div class="log-form"><label>Date<input id="rehearsal-date" type="date"></label><label>Run<select id="rehearsal-kind"><option>Full timed run 1</option><option>Full timed run 2</option><option>Interruption and fallback run</option><option>Additional run</option></select></label>
<label>Measured duration (minutes:seconds)<input id="rehearsal-duration" type="text" placeholder="20:00" inputmode="numeric"></label><div class="log-actions"><button id="use-timer">Use timer value</button></div>
<label class="wide">Notes and changes needed<textarea id="rehearsal-notes" rows="4" placeholder="Where did delivery slow down? Did the fallback work? What needs another pass?"></textarea></label>
<div class="log-actions wide"><button id="export-log">Export rehearsal record</button><span class="log-status" id="log-status" role="status"></span></div></div></details></section>
</main></div><dialog class="slide-dialog" id="slide-dialog" aria-label="Enlarged slide"><div class="dialog-actions"><button type="button">Close slide</button></div><img alt=""></dialog><script>{JS}</script></body></html>'''
    output = ROOT / args.output
    output.write_text(document, encoding="utf-8", newline="\n")
    print(json.dumps({"output": output.relative_to(ROOT).as_posix(), "main_slides": len(main_slides), "backup_slides": len(slides) - len(main_slides), "planned_seconds": total, "main_spoken_words": words, "embedded_images": image_count, "bytes": output.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
