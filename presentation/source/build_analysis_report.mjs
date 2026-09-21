// Browser-readable copy of the preserved report; no analysis is rerun here.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import crypto from 'node:crypto';

const root = process.cwd();
const require = createRequire(path.join(root, 'build/presentation/runtime.mjs'));
const { marked } = await import(pathToFileURL(require.resolve('marked')).href);
const source = 'results/analysis/20260915_baseline/REPORT.md';
const bytes = await fs.readFile(path.join(root, source));
const digest = crypto.createHash('sha256').update(bytes).digest('hex');
const headings = [];
const body = marked.parse(bytes.toString('utf8')).replace(/href="([^"]+)"/g, (match, href) => {
  if (href.startsWith('#') || /^[a-z][a-z0-9+.-]*:/i.test(href)) return match;
  const target = new URL(href, pathToFileURL(path.join(root, source)));
  const relative = path.relative(path.join(root, 'presentation'), fileURLToPath(target)).split(path.sep).join('/');
  return `href="${encodeURI(relative)}${target.search}${target.hash}"`;
}).replace(/<h2>(.*?)<\/h2>/g, (_, title) => {
  const id = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  headings.push({ id, title });
  return `<h2 id="${id}">${title}</h2>`;
});
const document = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Primary analysis report · Kidney biopsy classifier</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:25px}body{margin:0;background:#F7F8F5;color:#16343E;font:19px/1.6 Arial,sans-serif}header{padding:28px 5vw;border-bottom:1px solid #CEDBD7}header p{margin:0 0 10px}a{color:#007C78;text-underline-offset:3px}nav{padding:25px 5vw;border-bottom:1px solid #CEDBD7;display:flex;gap:12px 28px;flex-wrap:wrap;font-size:17px}main{max-width:1500px;margin:auto;padding:35px 5vw 80px}h1{font-size:36px;line-height:1.2}h2{font-size:28px;margin:60px 0 18px}p{max-width:100ch}table{border-collapse:collapse;width:100%;font-size:17px;line-height:1.4;margin:24px 0;display:block;overflow:auto}th,td{border:1px solid #CEDBD7;padding:12px 15px;text-align:left}th{background:#16343E;color:white}tr:nth-child(even){background:#EAF1ED}code{overflow-wrap:anywhere;font-size:.9em}.context{border-left:4px solid #007C78;padding-left:18px}.provenance{font-size:14px;color:#52656B;overflow-wrap:anywhere}footer{border-top:1px solid #CEDBD7;padding:25px 5vw}@media print{nav,header .links{display:none}body{font-size:11pt}main{padding:0}table{font-size:9pt;display:table}h2{break-after:avoid}}
</style></head><body>
<header><p><strong>Saved primary analysis</strong></p><p class="links"><a href="speaking_script.html#slide-13">Return to speaking script</a> · <a href="../${source}">Original Markdown report</a> · <a href="../results/analysis/20260915_baseline/model_metrics.csv">Model metrics CSV</a> · <a href="../results/reproduction/20260915_shared/configuration.json">Serving-run configuration</a></p>
<p class="context">Population clarification from the September 19 source review: the 345 evaluation specimens include 334 transplant biopsies and 11 native-kidney controls. The deposited metadata do not identify those controls individually. <a href="../docs/references/STUDY_AUDIT_20260919.md">Source review</a>.</p>
<p class="provenance">The report below preserves the completed analysis. This page changes its display only; it does not rerun the models or change the results.</p></header>
<nav aria-label="Report sections">${headings.map(h => `<a href="#${h.id}">${h.title}</a>`).join('')}</nav>
<main>${body}</main><footer class="provenance">Source: ${source}<br>SHA-256: ${digest}</footer></body></html>`;
await fs.writeFile(path.join(root, 'presentation/analysis_report.html'), document);
console.log(`Rendered preserved report: ${headings.length} sections, SHA-256 ${digest}`);
