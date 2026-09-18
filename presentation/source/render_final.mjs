import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const root=process.cwd();
const require=createRequire(path.join(root,'build/presentation/runtime.mjs'));
const {FileBlob,PresentationFile}=await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(root,'presentation/unos_kidney_biopsy.pptx')));
for(let i=0;i<p.slides.items.length;i++){
  const image=await p.export({slide:p.slides.getItem(i),format:'png',scale:1.5});
  await fs.writeFile(path.join(root,'presentation/slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await image.arrayBuffer()));
}
console.log(`Rendered all ${p.slides.items.length} slides from the final PPTX`);
