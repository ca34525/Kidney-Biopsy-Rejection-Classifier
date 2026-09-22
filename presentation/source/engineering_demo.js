(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('demo-data').textContent);
  const tabs = [...document.querySelectorAll('[data-stop]')];
  const stops = ['evidence', 'specimen', 'engineering'];
  const panels = [...document.querySelectorAll('main > [role=tabpanel]')];
  const dialog = document.getElementById('reference-dialog');
  const refBody = document.getElementById('reference-body');
  let active = 0;
  function selectStop(name, focus = false) {
    active = Math.max(0, stops.indexOf(name));
    tabs.forEach(button => {
      const selected = button.dataset.stop === stops[active];
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
      if (selected && focus) button.focus();
    });
    panels.forEach(panel => { panel.hidden = panel.id !== stops[active]; });
    history.replaceState(null, '', '#' + stops[active]);
    document.getElementById('previous-stop').disabled = active === 0;
    document.getElementById('next-stop').textContent = active === 2 ? 'Return to closing slide 14' : 'Next: ' + (active === 0 ? 'application' : 'engineering');
    document.getElementById('stop-position').textContent = `${active + 1} of 3`;
    window.scrollTo(0, 0);
  }
  tabs.forEach(button => button.addEventListener('click', () => selectStop(button.dataset.stop)));
  document.querySelector('.stops').addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (active + (event.key === 'ArrowRight' ? 1 : 2)) % 3;
    selectStop(stops[next], true);
  });
  document.getElementById('previous-stop').addEventListener('click', () => selectStop(stops[Math.max(0, active - 1)]));
  document.getElementById('next-stop').addEventListener('click', () => {
    if (active < 2) selectStop(stops[active + 1]);
    else {
      refBody.innerHTML = '<h1>Return to the slideshow</h1><p>Resume PowerPoint on slide 14, “What this project accomplished”.</p><p><a href="unos_kidney_biopsy.pptx">Open the PowerPoint</a> · <a href="unos_kidney_biopsy.pdf#page=14">Open the PDF closing page</a></p>';
      dialog.showModal();
    }
  });
  document.querySelectorAll('.subtabs').forEach(group => {
    const buttons = [...group.querySelectorAll('button')];
    function choose(button, focus = false) {
      buttons.forEach(other => {
        const selected = other === button;
        other.setAttribute('aria-selected', String(selected));
        other.tabIndex = selected ? 0 : -1;
        document.getElementById(other.getAttribute('aria-controls')).hidden = !selected;
      });
      if (focus) button.focus();
    }
    buttons.forEach(button => button.addEventListener('click', () => choose(button)));
    group.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
      event.preventDefault();
      const index = buttons.indexOf(document.activeElement);
      choose(buttons[(index + (event.key === 'ArrowRight' ? 1 : buttons.length - 1)) % buttons.length], true);
    });
  });
  const escape = text => String(text).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  function showReference(id) {
    const ref = data.references[id];
    if (!ref) return;
    refBody.innerHTML = `<p class="ref-source">Source: ${escape(ref.path)}<br>SHA-256: ${escape(ref.sha256)}</p><p><button class="quiet" data-download-ref="${escape(id)}">Download original source</button></p>` + ref.html;
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
  }
  function showLibrary() {
    refBody.innerHTML = '<h1>Reports and source material</h1><p>The highlights link to these complete documents and saved records.</p><ul class="ref-library">' + Object.entries(data.references).map(([id, ref]) => `<li><button class="quiet" data-ref="${escape(id)}">${escape(ref.title)}</button><p>${escape(ref.description)}</p></li>`).join('') + '</ul>';
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
  }
  function download(text, name, type) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const link = document.createElement('a'); link.href = url; link.download = name;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  document.addEventListener('click', event => {
    const ref = event.target.closest('[data-ref]');
    if (ref) { event.preventDefault(); showReference(ref.dataset.ref); }
    const source = event.target.closest('[data-download-ref]');
    if (source) {
      const record = data.references[source.dataset.downloadRef];
      download(record.raw, record.path.split('/').pop(), 'text/plain;charset=utf-8');
    }
  });
  document.getElementById('reference-library').addEventListener('click', showLibrary);
  document.getElementById('all-references').addEventListener('click', showLibrary);
  document.getElementById('close-reference').addEventListener('click', () => dialog.close());
  document.getElementById('download-example').addEventListener('click', () => download(data.snapshot.valid_csv, 'no-rejection.csv', 'text/csv'));
  document.querySelectorAll('[data-saved-case]').forEach(button => button.addEventListener('click', () => {
    const valid = button.dataset.savedCase === 'valid';
    document.getElementById('saved-valid').hidden = !valid;
    document.getElementById('saved-invalid').hidden = valid;
    document.getElementById('saved-case-status').textContent = valid ? 'Saved complete-input response' : 'Saved missing-IFNG response: HTTP 422, no score';
  }));
  const frame = document.getElementById('live-app');
  frame.addEventListener('load', () => {
    // The surrounding demonstration supplies the title; keep the real app controls.
    const embedded = frame.contentDocument;
    if (!embedded || embedded.getElementById('presentation-embedding')) return;
    const style = embedded.createElement('style');
    style.id = 'presentation-embedding';
    style.textContent = '.site-header,.intro{display:none}main{padding-top:24px!important}';
    embedded.head.append(style);
  });
  const saved = document.getElementById('saved-application');
  const toggle = document.getElementById('toggle-mode');
  const mode = document.getElementById('application-mode');
  let liveReady = false;
  function savedMode() {
    frame.hidden = true; saved.hidden = false;
    mode.textContent = 'Saved example responses'; mode.classList.add('saved');
    toggle.textContent = liveReady ? 'Use live application' : 'Check live service';
  }
  function liveMode() {
    saved.hidden = true; frame.hidden = false;
    if (!frame.getAttribute('src')) frame.src = '/';
    mode.textContent = 'Live application · frozen model verified'; mode.classList.remove('saved');
    toggle.textContent = 'Use saved example';
  }
  async function checkService() {
    if (location.protocol === 'file:') { savedMode(); return; }
    try {
      const response = await fetch('/model', {cache:'no-store', signal:AbortSignal.timeout(5000)});
      if (!response.ok) throw new Error('Unavailable');
      const model = await response.json();
      if (model.model_version !== data.snapshot.model_version || model.threshold !== data.snapshot.threshold) throw new Error('Different model');
      liveReady = true; liveMode();
    } catch { liveReady = false; savedMode(); }
  }
  toggle.addEventListener('click', () => {
    if (!frame.hidden) savedMode();
    else if (liveReady) liveMode();
    else checkService();
  });
  selectStop(location.hash.slice(1));
  checkService();
})();
