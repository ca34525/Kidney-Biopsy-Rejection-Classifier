# Presentation design and review

Use [Presentation specification](PRESENTATION_SPEC.md) for the agreed content,
slide sequence and timing. Use the [presentation README](../presentation/README.md)
for launch, build, backup and rehearsal instructions. This guide keeps the design
sources and review criteria in one place.

The requested design guidance predates 2020: these sources were published in
2007–2014 and reviewed September 15, 2026. That cutoff applies to presentation
design; clinical sources and their review dates are in
[Research context](RESEARCH_CONTEXT.md).

## What the sources support

### Audience, structure, and rehearsal

Philip E. Bourne's **April 27, 2007** editorial advises presenters to adapt to the audience, keep the argument focused, give the talk a logical progression, rehearse aloud with timing, review recordings, and acknowledge contributions. These are an experienced author's recommendations, not results from a controlled trial. Use them to decide what the audience needs to understand and what can wait for questions. [Bourne, *Ten Simple Rules for Making Good Oral Presentations*](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.0030077).

### Readability and limited attention

Stephen M. Kosslyn, Rogier A. Kievit, Alexandra G. Russell, and Jennifer M. Shephard's **July 17, 2012** paper examines common presentation flaws through three studies. Its guidance addresses perceptual differences, grouping, consistency, and the amount of information viewers must process. The studies document flaws, audience complaints, and difficulty recognizing problems. They do not establish that every checklist rule improves learning in every setting. Apply the principles by making labels easy to distinguish, keeping related information together, and removing competing content. [Kosslyn et al., *PowerPoint Presentation Flaws and Failures: A Psychological Analysis*](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2012.00230/full).

### A statement supported by evidence

Joanna K. Garner and Michael P. Alley's **2013** study compared technical presentations viewed by 110 engineering students. Slides using a sentence headline with supporting visual evidence produced better comprehension and fewer misconceptions, with stronger delayed recall, than the comparison slides. The study tested a package of design choices in an educational setting. It does not isolate headline wording or prove an interview outcome. Use this structure for result slides: a defensible statement, then the chart or diagram that supports it. [Garner and Alley, *How the Design of Presentation Slides Affects Audience Comprehension: A Case for the Assertion–Evidence Approach*](https://writing.engr.psu.edu/ae_comprehension.pdf).

### Figures made for a talk

Nicolas P. Rougier, Michael Droettboom, and Philip E. Bourne's **September 11, 2014** editorial recommends choosing a figure's message before its design and adapting it to the display medium. A projected figure needs readable labels and a simpler composition than a figure people can examine at their own pace. The article also addresses color, explanatory captions, and the risks of accepting plotting defaults. This is practical advice informed by visualization literature. [Rougier et al., *Ten Simple Rules for Better Figures*](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833).

## Apply the guidance

- Give each slide one main point. Use a short topic title for definitions and
  processes, and a factual takeaway for results. Choose the layout for the
  information; avoid repeated decorative boxes, icons or kidney images.
- Use plain English, dark-text bullets for parallel points, numbered steps for
  calculations, and diagrams for relationships. Bold labels distinguish terms
  from explanations. Place each explanation beside its evidence.
- Introduce unfamiliar terms before using them. Distinguish measurements,
  housekeeping references, metadata and recorded diagnoses. Use the same model
  names, error terms and colors across the slides, browser and script.
- Start with roughly 28–32 point body text and 36–44 point titles, then inspect
  the actual display. These are project defaults, not scientifically established
  cutoffs. Enlarge figure labels separately and keep code excerpts short and editable.
- Keep a readable visual cue for each substantive spoken topic. Elaboration and
  transitions do not each need another bullet. Delivery cues belong in the
  separate HTML script; PowerPoint notes stay empty.
- Keep units, denominators, comparison models and estimated uncertainty visible.
  Label the population and evaluation partition. Quantitative figures must come
  from saved outputs; generated illustrations cannot stand in for results.
- Put a brief source acknowledgment beside external evidence and full links in
  the script. Avoid repeated source footers. Explain limitations next to the
  affected claim, and put secondary methods in linked reports.
- Explain the candidate's decisions and AI assistance accurately. A list of tools
  or job-description keywords is not evidence of completed work.

## Review before delivery

- [ ] The motivation, prediction target, comparison and software purpose are clear
  to someone unfamiliar with gene-expression analysis.
- [ ] Slides and narration follow the current specification, with consistent
  terminology and readable support for each main spoken topic.
- [ ] Counts and claims match identified sources; specimen counts are not called
  patient counts, associations are not called causes, and external clinical
  evidence is distinct from this project's evaluation.
- [ ] Every final slide render and PDF page is readable, without clipping or
  crowded labels. Color is reinforced by words or labels.
- [ ] Local links, source dialogs, browser navigation, valid and invalid requests,
  and offline fallback work. The displayed model matches the configured run.
- [ ] The full talk includes both screen-share transitions and ends near 20
  minutes at a natural pace, with questions afterward. Record actual rehearsal
  times; planned script allocations are pacing aids.
- [ ] A practice listener can explain the target, evaluation and conclusion.
  Shorten secondary detail if the talk runs long; explain a substantive decision
  more clearly if it runs short.
