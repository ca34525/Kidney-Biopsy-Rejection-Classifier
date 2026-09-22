// Detailed engineering evidence lives in the browser deliverable and speaking script.
export async function addTechnicalSlides({ slide, text, bullets, line, C }) {
  {
    const s = slide('Software engineering');
    text(s, 'Reports, application and scoring service', 64, 186, 1152, 73, 39, C.teal);
    bullets(s, [
      'Inspect the evidence',
      'Score a public specimen',
      'Trace and check the calculation',
    ], 64, 309, 1152, 231, 38, C.ink, 28);
  }
  {
    const s = slide('What this project accomplished', 'Public data: Zhang et al. (2024), GSE212160. Development and presentation used AI assistance.', true);
    text(s, 'Model comparison', 64, 180, 1152, 54, 37, C.white, true);
    text(s, 'CatBoost missed 8 fewer rejection cases than logistic, with 8 incorrect flags each.\nA dependable advantage remains uncertain.', 64, 249, 1152, 101, 31, C.white);
    line(s, 64, 383, 1152, '#78949B');
    text(s, 'Software engineering', 64, 417, 1152, 53, 37, C.white, true);
    text(s, 'Reproducible analysis and a tested scoring service,\nwith a prototype application and checks against saved results.', 64, 486, 1152, 88, 31, C.white);
    text(s, 'Next: cross-validation within discovery.\nThen investigate whether the score adds useful diagnostic information.', 64, 585, 1152, 65, 26, C.white);
  }
}
