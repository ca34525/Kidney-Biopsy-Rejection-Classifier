# Presentation guide

## Purpose

Prepare a **20-minute presentation** for the UNOS Associate Data Scientist interview about this kidney biopsy gene-expression classifier. The user confirmed that the full 20 minutes is presentation time. Questions come separately.

The user's September 18, 2026 instruction puts all spoken text and delivery cues in a **separate HTML speaking script**. Do not use PowerPoint notes. The [current draft](../presentation/README.md) has 18 main slides, 6 backup slides, and a complete script planned for 20 minutes. Real timed rehearsals remain pending.

The user's second-pass feedback sets the order and level of explanation: open with the topic and research question, establish the biological and data context, then present methods and results. Give every substantive spoken topic a visible cue. These are the user's presentation preferences, separate from the external guidance summarized below.

This guide uses external sources published in **2007–2014**, with a cutoff before 2020 for the requested guidance predating modern generative-AI presentation tools. Publication dates come from the papers themselves or their publishers. Source summaries appear below. The project standards that follow apply those ideas to this interview.

## What the sources support

### Audience, structure, and rehearsal

Philip E. Bourne's **April 27, 2007** editorial advises presenters to adapt to the audience, keep the argument focused, give the talk a logical progression, rehearse aloud with timing, review recordings, and acknowledge contributions. These are an experienced author's recommendations, not results from a controlled trial. Use them to decide what the audience needs to understand and what can wait for questions. [Bourne, *Ten Simple Rules for Making Good Oral Presentations*](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.0030077).

### Readability and limited attention

Stephen M. Kosslyn, Rogier A. Kievit, Alexandra G. Russell, and Jennifer M. Shephard's **July 17, 2012** paper examines common presentation flaws through three studies. Its guidance addresses perceptual differences, grouping, consistency, and the amount of information viewers must process. The studies document flaws, audience complaints, and difficulty recognizing problems. They do not establish that every checklist rule improves learning in every setting. Apply the principles by making labels easy to distinguish, keeping related information together, and removing competing content. [Kosslyn et al., *PowerPoint Presentation Flaws and Failures: A Psychological Analysis*](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2012.00230/full).

### A statement supported by evidence

Joanna K. Garner and Michael P. Alley's **2013** study compared technical presentations viewed by 110 engineering students. Slides using a sentence headline with supporting visual evidence produced better comprehension and fewer misconceptions, with stronger delayed recall, than the comparison slides. The study tested a package of design choices in an educational setting. It does not isolate headline wording or prove an interview outcome. Use this structure for result slides: a defensible statement, then the chart or diagram that supports it. [Garner and Alley, *How the Design of Presentation Slides Affects Audience Comprehension: A Case for the Assertion–Evidence Approach*](https://writing.engr.psu.edu/ae_comprehension.pdf).

### Figures made for a talk

Nicolas P. Rougier, Michael Droettboom, and Philip E. Bourne's **September 11, 2014** editorial recommends choosing a figure's message before its design and adapting it to the display medium. A projected figure needs readable labels and a simpler composition than a figure people can examine at their own pace. The article also addresses color, explanatory captions, and the risks of accepting plotting defaults. This is practical advice informed by visualization literature. [Rougier et al., *Ten Simple Rules for Better Figures*](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833).

## Standards for this interview

### Build the argument before the slides

- Assume a mixed audience of data scientists and transplant-domain colleagues until the panel composition is known. Explain the prediction target before introducing model terminology.
- Define biopsy, RNA, assay, and panel in plain language before explaining the measurements. Give only the biological context needed to understand the data and label.
- Keep the title slide to the topic and research question, with light context only if needed. Introduce the model comparison and error counts after the audience understands the specimens, diagnoses, and evaluation groups. Omit the interview-project tagline.
- Draft the central question in one sentence. State what information the model receives, what label it predicts, and which biopsy population the analysis covers.
- Organize around the work: why the question matters, what the data contain, how the evaluation works, what happened, and what the result permits us to conclude.
- Distinguish an RNA measurement from the diagnosis the model predicts. Prefer "RNA measurement" or "measured molecule" in audience-facing explanations. When an exact assay or software term requires "target," define it as the molecule the assay measures. Call the predicted outcome the "recorded diagnosis" or "rejection label."
- Call a sample identifier a "specimen ID." Explain that it identifies the source record and does not enter the model. Reserve "study accession" for the dataset reference in source material.
- Explain decisions through concrete examples. For example, show why a missing required RNA measurement causes the service to reject an input instead of producing a misleading score.
- Explain the candidate's own contributions accurately. Credit the public dataset and any borrowed methods at the point of use.
- End with the measured finding, its main limitation, and the next justified step. Do not promise an outcome before the analysis exists.

### Make each slide understandable

- Give each substantive slide one job. Prefer a short topic title for definitions, processes, and setup. Use a factual takeaway title when the slide establishes a result. Do not force background material into a conclusion.
- Under that title, show the relevant evidence. A cohort flow diagram explains exclusions. A split diagram explains evaluation. A result chart explains a comparison.
- Put the explanation for delivery in the separate HTML speaking script, with spoken text visibly separated from delivery cues. Keep PowerPoint notes empty. The visible slide should contain the words needed to understand its evidence and follow the spoken discussion.
- Choose a few consistent type sizes and a restrained color palette. As a starting point, use roughly 28–32 point body text and 36–44 point titles. These are project defaults, not scientifically established thresholds.
- Test readability at the actual display size. Enlarge chart labels separately from the slide text. Move secondary detail to an appendix when it cannot remain readable.
- Use the same class names, colors, and model names throughout. Add labels or marker shapes so color is not the only distinction.
- Use images only when they explain something the audience needs. Decorative kidney images, gradients, and repeated icon grids consume space without showing the analysis.

### Align the script and slides

- Review the script by topic, then identify the visible cue for each substantive explanation. A cue can be a diagram label, a short bullet, an example, a table row, or a chart annotation. A transition sentence does not need its own cue.
- Keep each cue on screen while discussing it. If one script section covers several topics that cannot fit readably together, divide it across slides and move the matching script paragraphs with it.
- Provide enough words to explain what a diagram means. For a definition, use a distinct label followed by a colon and a short explanation, such as "Biopsy tissue: a small tissue sample."
- Use the same terms and order in both places. Introduce an unfamiliar term before relying on it. Make the distinction between measurements, reference measurements, metadata, and the recorded diagnosis visible.
- Retain concise cues rather than full spoken paragraphs. Sparse slides can be as difficult to follow as crowded slides when the speaker discusses topics that never appear on screen.
- Place short, meaningful source acknowledgments beside externally sourced material. Keep full linked references in the script's source area. Omit slide footers that merely announce where the full links are stored.
- Check each slide beside its script before export. Confirm that every main spoken topic has a readable cue and that every prominent on-slide item is explained aloud.

### Make the evidence inspectable

- Identify the dataset and the counts used in each result. Separate patient counts from biopsy counts where both are available.
- Define the positive class. Label whether a displayed value comes from training, cross-validation, or held-out evaluation.
- State the comparison model and show its result alongside the selected model. Explain the size of the difference in ordinary language.
- Give each metric a short interpretation. For example, explain sensitivity as the fraction of rejection cases the classifier identifies under the stated labeling rule and threshold.
- Show uncertainty where it has been estimated. Name what an interval represents. Do not manufacture error bars or claim an improvement from a small visible gap alone.
- Explain consequential errors using actual counts or de-identified examples from the evaluation. Keep hypothetical examples clearly labeled.
- Retain units, denominators, axis labels, and relevant baselines. If simplifying a chart for the talk, preserve the values and comparisons.
- Describe a gene's model contribution as an association. A useful predictor does not by itself establish a biological cause.
- State the limits of retrospective public-data evaluation before discussing possible clinical use. Claims about diagnosis or clinical benefit require evidence beyond this interview project.
- Generate quantitative figures from saved analysis outputs. Every reported number must match a reproducible result. Never use generated images to depict results, observations, or diagnostic performance.

These evidence requirements are project choices. The presentation sources above support clear communication, but do not prescribe this classifier's methods or establish medical claims.

### Use all 20 minutes deliberately

- Allocate section times totaling **20:00**, including the opening and conclusion. Do not reserve two minutes of this slot for questions.
- Choose the number of slides after allocating time to the argument. There is no required slide count or universal bullets-per-slide formula.
- Rehearse the complete talk aloud, with the real figures and transitions. Record elapsed time at section boundaries.
- If the talk runs long, remove secondary material. If it runs short, explain an important result or decision more clearly. Do not fill the time with generic background.
- Complete at least two final rehearsals close to 20 minutes at a natural pace. Record the times and remaining rough spots. This is the project's rehearsal standard.
- Ask a practice listener to explain the prediction target, the evaluation setup, and the main conclusion afterward. Revise any point they cannot explain accurately.
- Put detailed methods and likely answers in backup slides after the conclusion. They are outside the planned 20-minute sequence.
- If including a demonstration, time it as part of the talk and keep a local screenshot or recording available. Verify the deck and PDF on the intended display setup.

## Review for common AI-generated presentation problems

Before accepting a draft, check these points:

| Problem | Required revision |
| --- | --- |
| The opening gives a model name or error counts before explaining the task | Keep the title slide to the topic and research question. Move results after the relevant context and show denominators. |
| A spoken topic has no visible counterpart | Add a short cue or give the topic its own slide, then align the script and timing. |
| A technical label has several possible meanings | Define it with ordinary words and use the same term on the slide and in the script. |
| The deck lists tools and job-description keywords | Show a decision, the work that supports it, and its consequence. |
| Every slide uses the same three-box layout | Choose the layout from the information the slide needs to explain. |
| Dense paragraphs repeat the HTML speaking script | Keep only essential labels and the evidence needed on screen. |
| A figure looks polished but lacks sample counts or a comparison | Add the missing information and verify it against the saved analysis. |
| Words such as “transformative,” “robust,” or “actionable” substitute for a finding | State the measured result or the specific action the evidence supports. |
| A kidney image or diagram appears to be measured evidence | Label the illustration and replace it when actual study evidence is required. |
| The conclusion quietly expands beyond the tested population | State the population actually evaluated and the validation still needed. |

## Ready-to-present check

- [ ] The argument is understandable without specialist gene-expression knowledge.
- [ ] The title slide introduces the topic and question without premature results or an interview tagline.
- [ ] Every substantive spoken topic has a readable on-slide cue, and the slide order matches the script.
- [ ] RNA measurements, reference measurements, specimen IDs, and recorded diagnoses have distinct, explained roles.
- [ ] The visible results match saved outputs, including cohort counts and metric definitions.
- [ ] Claims have supporting evidence or an explicit label describing their uncertainty.
- [ ] Figures remain readable at presentation size, with no clipped labels or crowded annotations.
- [ ] The candidate can explain each methodological choice without reading the slide.
- [ ] The separate HTML speaking script contains the complete spoken text and delivery cues, and PowerPoint notes are empty.
- [ ] The planned presentation fills 20 minutes, and final rehearsal times are recorded.
- [ ] A local deck, PDF, and any demonstration backup open successfully.
- [ ] Source acknowledgments and backup slides are complete.

Source verification date: September 15, 2026.
