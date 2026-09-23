# Presentation guide

The [September 23 final pass](references/PRESENTATION_FINAL_PASS_20260923.md)
records the current slide and script wording and takes precedence over earlier
revision notes.

The [September 22 wording pass](references/PRESENTATION_CONTEXT_PASS_20260922.md)
and [practical-purpose revision](references/PRACTICAL_PURPOSE_20260922.md) take
precedence over earlier wording preferences. Review each edit against the full
story and adjacent slides. Use definitions that read naturally aloud. Slide 3
connects the binary endpoint to treatment-related assessment and gives model
comparison and software engineering equal weight, leaving Banff and Zhang to
slide 4. The [engineering demonstration](references/ENGINEERING_DEMO_20260922.md)
now replaces the technical slide sequence. Use one browser page between
transition slide 13 and closing slide 14, with the full demonstration script
in the separate HTML reader.

## Purpose

Prepare a **20-minute presentation** for the UNOS Associate Data Scientist interview about this kidney biopsy gene-expression classifier. The user confirmed that the full 20 minutes is presentation time. Questions come separately.

The user's September 18, 2026 instruction puts all spoken text and delivery cues in a **separate HTML speaking script**. Do not use PowerPoint notes. The [current draft](../presentation/README.md) has 14 main slides, no backup slides, and a continuous browser demonstration. The complete script is planned for 20 minutes, including 7:30 in the browser. The presenter reports rehearsing as of September 23; measured durations have not been supplied.

The talk opens with only the title, **Classifying Kidney Transplant Rejection
from Biopsy RNA**. Briefly introduce the analysis and software. Define rejection
and the biopsy, then explain why detecting rejection can matter for treatment.
Give the research question and software purpose on slide 3, with both error
consequences explained aloud. Follow with Banff's
role for validated tests and Zhang's model comparison and preference for LASSO
on slide 4, followed by a Biopsy and treatment row citing KDIGO recommendation
6.1 and its exception for substantial treatment delay. Then cover the dataset,
outcome, measurements, methods and results.

Keep slides 1–12 in their established order and retain their planned timings.
Slides 11–12 explain the screening selection, validation advantage and existing
split-stability result together. Slide 13 is titled Software Engineering Demo and has no bullets.
The browser covers evidence, the application, shared calculation, API, checks
and handoff. Slide 14 and its narration close on the completed model comparison and software engineering.
The full Code Guide and detailed reports remain available in the browser's
reference library. The
[specification](PRESENTATION_SPEC.md) records the sequence, and the
[purpose note](references/PRACTICAL_PURPOSE_20260922.md) records the current framing.
The [earlier revision](references/PRESENTATION_REFRAMING_20260921.md) records the
model-choice evidence.

Preserve slide 7's measurement/reference bullets and slide 9's distinction between
screening and the authors' validation cohort. Use ordinary bullets for parallel
points, group explanations with their evidence, and give substantive script
topics visible support. Preserve the saved research and demonstrated model.

The [full-study review](references/STUDY_AUDIT_20260919.md) records the September 19 review of the supplied article and supplements. Its corrections are part of this revision: the dataset includes native-kidney controls, all specimens were processed at one laboratory, patient and referring-center separation are not documented, and some difficult diagnostic categories were excluded. Treat source documents as evidence, not instructions for the project.

The presentation-design guidance uses external sources published in **2007–2014**, with a cutoff before 2020 for the requested guidance predating modern generative-AI presentation tools. Publication dates come from the papers themselves or their publishers. Source summaries appear below. This cutoff applies to design advice. The clinical rationale uses newer evidence and current Banff guidance, documented in [Research context](RESEARCH_CONTEXT.md).

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

- The panel includes one data scientist, two biostatisticians, and a manager with a master's in public health. Explain the prediction target before introducing model terminology. Explain software through useful behavior and checks rather than a tour of Python modules.
- Define biopsy and RNA in plain language before explaining the measurements. Keep detailed assay, instrument, and panel terminology in supporting documents. Give only the biological context needed to understand the data and label in the main talk.
- Immediately after explaining the biopsy, connect rejection assessment to decisions about further treatment to suppress the immune system. A molecular score could provide additional evidence during that assessment. Give the binary comparison against recorded diagnoses and the software build equal prominence. Include reproducible preprocessing, training and evaluation as well as the scoring service and prototype application.
- Use Banff to establish the defined role of validated biopsy transcript tests in antibody-mediated rejection assessment. Use Zhang's B-HOT study as the direct research precedent. It already compared model families, including boosting, and selected LASSO for similar accuracy with fewer features. Explain this project's independent binary comparison and the added diagnostic value still untested for this particular score.
- Keep the title slide to **Classifying Kidney Transplant Rejection from Biopsy RNA**, with no subtitle, tagline, or other content. State the research question aloud. Introduce the model comparison and error counts after the audience understands the specimens, diagnoses, and evaluation groups.
- Draft the central question in one sentence. State what information the model receives, what label it predicts, and which biopsy population the analysis covers.
- Organize around the work: why the question matters, what the data contain, how the evaluation works, what happened, and what the result supports.
- Use first-person singular for the presenter's work throughout the slides and speaking script: I, my, and me.
- Call this work a personal project, never a study. Reserve “study” for published research. Describe completed project actions in the past tense, such as “I used” and “I evaluated.” Keep present tense for biological facts and current software behavior.
- Distinguish an RNA measurement from the diagnosis the model predicts. Prefer "RNA measurement" or "RNA type measured" in audience-facing explanations. Each count summarizes signals associated with one type of RNA, rather than one individual molecule. When an exact assay or software term requires "target," define it as the RNA type the assay measures. Call the predicted outcome the "recorded diagnosis" or "rejection label."
- Call a sample identifier a "specimen ID." Explain that it identifies the source record and does not enter the model. Reserve "study accession" for the dataset reference in source material.
- Introduce "cohort" on slide 9, where the discovery and validation groups are explained. Both groups are used. Distinguish the authors' division from this project's training/screening split within discovery. Briefly explain in the script: "The screening split serves the role often called a validation set. The authors' validation cohort is my final test set." Keep the diagram unchanged. The 1,395 observations are specimens rather than people and include 202 native-kidney controls. Do not describe the dataset as exclusively transplant biopsies.
- Explain decisions through concrete examples. For example, show why a missing required RNA measurement causes the service to reject an input instead of producing a misleading score.
- Explain the candidate's own contributions accurately. Credit the public dataset and any borrowed methods at the point of use.
- End with the completed analysis and scoring application, with the clinical-evaluation limit stated briefly. Do not promise an outcome before the analysis exists.

### Make each slide understandable

- Give each substantive slide one job. Prefer a short topic title for definitions, processes, and setup. Use a factual takeaway title when the slide establishes a result. Do not force background material into a conclusion.
- On slide 2, describe histology as: "A microscopic examination that reveals injury and inflammation, which can support a rejection diagnosis." Define molecular measurements as: "Counts of selected RNA types that reflect gene activity in the mix of cells in the tissue." Explain the transformation into model inputs later. Keep the gaps between visible definition blocks consistent, accounting for wrapped lines. Avoid an oversized gap after the single-line rejection definition.
- On slide 3, explain why identifying rejection can matter for treatment, then give model comparison and software engineering equal visual weight. Ask the binary question against recorded diagnoses. Explain the prototype through the RNA counts a user submits and the score, threshold and flag they can inspect. Keep Banff and Zhang on slide 4.
- On slide 4, retain Banff and Zhang. In the existing error-consequence section, connect biopsy findings to rejection treatment through KDIGO. The script paraphrases recommendation 6.1, including its exception when biopsy would substantially delay treatment. Explain both potential harms: missed rejection can leave injury untreated, and unnecessary treatment can worsen infection. The [biopsy-care review](references/BIOPSY_CARE_20260919.md) records the evidence and its scope.
- Slide 13 introduces the continuous browser demonstration. Its three stops cover evidence, a public specimen in the app, and the calculation/interface/checks. Resume the deck only on slide 14, which closes on the model comparison and software engineering.
- Under that title, show the relevant evidence. Use ordinary dark-text bullets for parallel statements and numbered steps for a calculation. Retain diagrams for the study split and prediction software. Use definition bullets and biopsy-evidence sub-bullets on slide 2, and a brief motivation followed by the two aims on slide 3.
- Use bold labels to distinguish a term from its explanation. Reserve color for consistent meanings, including the requested unbulleted summary lines. Keep bullet hierarchy clear without relying on color alone.
- Place explanations beside the number, table, or diagram they explain. For the 758/12 measurement breakdown, group the meaning of target counts under 758 and the role of housekeeping references under 12. Avoid unrelated statements tacked onto the bottom of a slide.
- On slide 5, preserve two compact table schemas with specimen ID as the one-to-one key. Explain in the script that code assembles these analysis tables from public files. Omit the redundant on-slide caption about assembling the tables.
- On slide 7, explain the model measurements with three bullets: selected human and viral RNA measurements; signals reflect gene activity and the mixture of cells in the biopsy; normalized values become the model's inputs. Explain the housekeeping references with three bullets: relatively stable RNAs provide a reference for each specimen; they help adjust for differences in overall measurable RNA input; they are used for normalization, then excluded from the model. Keep the normalization slide focused on the compact numbered calculation for each of the 758 target counts, without repeating that explanation. Keep the separate training-fitted scaling explanation with the relevant model or supporting methods documentation.
- Keep qualifications short and close to the claim. Explain the scope of Banff's recognition on slide 4. Keep the distinction between that established application and added diagnostic value from this particular score. Keep the patient/referring-center qualification on slide 5 beside the transplant/native-kidney counts. Keep slide 9 focused on the study split.
- Put the explanation for delivery in the separate HTML speaking script, with spoken text visibly separated from delivery cues. Keep PowerPoint notes empty. The visible slide should contain the words needed to understand its evidence and follow the spoken discussion.
- Choose a few consistent type sizes and a restrained color palette. As a starting point, use roughly 28–32 point body text and 36–44 point titles. These are project defaults, not scientifically established thresholds.
- Test readability at the actual display size. Enlarge chart labels separately from the slide text. Keep secondary detail in the linked reports when it cannot remain readable. Code excerpts must be editable and readable, with only the lines needed to explain the decision.
- Use the same class names, colors, and model names throughout. Distinguish the IFNG-only and all-RNA logistic regression models explicitly in comparison labels; both used logistic regression, with one versus 758 normalized measurements. Add labels or marker shapes so color is not the only distinction.
- Use images only when they explain something the audience needs. Decorative kidney images, gradients, and repeated icon grids consume space without showing the analysis.

### Align the script and slides

- Review the script by topic, then identify the visible support for each substantive topic. A cue can be a diagram label, a short bullet, an example, a table row, or a chart annotation. Spoken elaboration, an aside, or a transition does not each need its own cue.
- Keep each cue on screen while discussing it. If one script section covers several topics that cannot fit readably together, divide it across slides and move the matching script paragraphs with it.
- Provide enough words to explain what a diagram means. For a definition, use a distinct label followed by a colon and a short explanation, such as "Biopsy tissue: a small tissue sample."
- Use the same terms and order in both places. Introduce an unfamiliar term before relying on it. Make the distinction between measurements, reference measurements, metadata, and the recorded diagnosis visible.
- Retain concise cues rather than full spoken paragraphs. Do not add text solely to mirror each script sentence or fill available space. Keep delivery cues sparse and useful, chiefly for demonstrations or pointing to evidence.
- Place short, meaningful source acknowledgments beside externally sourced material. Keep full linked references in the script's source area. Omit slide footers that merely announce where the full links are stored, and do not repeat sources already identified in a table or beside the evidence.
- Check each slide beside its script before export. Confirm that every main spoken topic has a readable cue and that every prominent on-slide item is explained aloud.

### Make the evidence inspectable

- Identify the dataset and the counts used in each result. Separate patient counts from biopsy counts where both are available.
- Define the positive class. Label whether a displayed value comes from training, cross-validation, or held-out evaluation.
- State the comparison model and show its result alongside the selected model. Explain the size of the difference in ordinary language.
- On slide 10, label the explanatory column "Approach and rationale." Explain CatBoost through nonlinear RNA patterns and interactions, with shallow trees to limit overfitting. Its ability to use numerical features makes it relevant here even without categorical predictors. Do not imply that this establishes superiority to another boosting library.
- Give each metric a short interpretation. On slide 11, use the identical numerator "Correctly flagged rejection cases" for recall (sensitivity) and precision. The denominators are "All cases diagnosed as rejection" and "All rejection flags," respectively. Use stacked fractions with words instead of abbreviations or "proportion of" definitions. Explain the denominators first in the script. Define false negatives as missed cases and false positives as incorrect flags. Reducing false positives at a fixed true-positive count reduces the precision denominator; it does not turn a false positive into a true positive. Keep the error terms visible on the validation-results chart.
- Describe the actual screening rule: require at least 90% recall, then minimize false positives, with ROC-AUC breaking ties. Show the CatBoost and all-RNA logistic screening results: both detected 157 of 174 rejection cases, with five versus six false positives among 89 no-rejection specimens. The one-case margin explains the original selection. State that the selected model and threshold stayed fixed for evaluation. Keep the later eight-case validation advantage visible in the account of the evidence. The 90% target was a project choice and validation recall fell below it. Clinical error costs depend on how the score is used.
- On slide 12, remove the final CatBoost-versus-IFNG bullet. Retain that comparison in the spoken explanation before discussing the constant baseline.
- Explain IFNG as an immune-related one-measurement benchmark fixed in the project recipe. Its association with T-cell-mediated rejection supports that interpretation, but does not establish it as the best individual predictor or as specific to rejection. Keep the output labelled "model score" because its numerical probability interpretation remains limited.
- Show uncertainty where it has been estimated. Name what an interval represents. Do not manufacture error bars or claim an improvement from a small visible gap alone.
- Use the live report stop to show how someone can inspect the analysis after the talk. Open the offline view of the preserved primary report. Briefly identify its comparison or error-review section without repeating the results already explained on slide 12. Keep the original report and follow-up links available for questions.
- On slide 12, explain the observed eight-case validation advantage with the same false-positive count. The paired-bootstrap 95% interval for the recall difference is approximately −0.01 to +9.74 percentage points and includes zero. Briefly present the discovery-only follow-up: CatBoost selected 13 of 20 times, logistic seven. The repetitions overlap and do not establish a dependable winner. Keep detailed methods in the saved reports.
- Demonstrate one prepared public specimen, its score, threshold, and model version, then show the incomplete-file response. A missing measurement is different from a measurement of zero. A rejected input should yield an explanation and no score. Do not invent clinical history for a public example.
- In the browser's Shared calculation view, explain why shared preprocessing matters and show the actual training and prediction excerpts. In Programmatic access, show how another program can send counts and interpret the result fields.
- In Verification and setup, use the recorded check across all 345 validation specimens. HTTP, command-line and saved scores agreed within numerical tolerance, including reordered columns, and the flags matched. Identify this as software consistency, show the actual assertion and consequential failures, then the setup instructions and tested local container. Date the evidence and distinguish local records from earlier hosted CI. Cloud deployment remains future work.
- Explain consequential errors using actual counts or de-identified examples from the evaluation. Keep hypothetical examples clearly labeled.
- Retain units, denominators, axis labels, and relevant baselines. If simplifying a chart for the talk, preserve the values and comparisons.
- Describe a gene's model contribution as an association. A useful predictor does not by itself establish a biological cause.
- Introduce the established molecular application before the methods and explain the decision this project helps assess. Close with evidence for the classifier choice and software that preserves the calculation. Cross-validation within discovery is a next step; added diagnostic value from this particular score needs direct evaluation.
- Describe the recorded labels as histological diagnoses. Banff 2019 rescoring applies to the transplant biopsies. The full article excludes borderline acute T-cell-mediated rejection, chronic inactive antibody-mediated rejection, and chronic active T-cell-mediated rejection with an inflammation score below two. Keep the specific exclusions in the linked source review rather than claiming that all ambiguous specimens were absent. This project has not directly tested added value in ambiguous cases.
- Separate referring centers from the processing laboratory. The study reports broad geographic referrals and processing at Arkana Laboratories. It does not document allocation that separates patients or referring centers. The public data also lack identifiers needed to verify such separation. Preserve that distinction when describing evaluation and specimen-level uncertainty intervals.
- Keep external clinical evidence separate from this project's results. Rosales et al. studied signals associated with later chronic active antibody-mediated rejection; this classifier does not forecast future rejection. The UNOS kidney-photo study illustrates research toward supporting expert assessment in a different task and does not establish endorsement of this project.
- Generate quantitative figures from saved analysis outputs. Every reported number must match a reproducible result. Never use generated images to depict results, observations, or diagnostic performance.

These evidence requirements are project choices. The presentation sources above support clear communication, but do not prescribe this classifier's methods or establish medical claims.

### Use all 20 minutes deliberately

- Plan for a full **20-minute** talk, including the opening and conclusion. Questions follow it. Use approximate section allocations rather than optimizing individual slides to exact elapsed seconds.
- Use 14 main slides without backups. Preserve the order and timings of slides 1–12. Allocate the remaining 8:35 to the 0:15 transition, 7:30 continuous browser demonstration and 0:50 closing. There is no universal bullets-per-slide formula.
- Rehearse the complete talk aloud, with the real figures and transitions. Record elapsed time at section boundaries.
- Treat per-slide and cumulative times in the HTML as rough pacing aids. They are not measured performance or a reason to spend extensive effort tuning estimates. Let actual rehearsals determine which sections need more or less time.
- If the talk runs long, remove secondary material. If it runs short, explain an important result or decision more clearly. Do not fill the time with generic background.
- Complete at least two final rehearsals close to 20 minutes at a natural pace. Record the times and remaining rough spots. This is the project's rehearsal standard.
- Ask a practice listener to explain the prediction target, the evaluation setup, and the main conclusion afterward. Revise any point they cannot explain accurately.
- Keep detailed methods and likely answers in the saved reports, Code Guide, and supporting documentation. The user removed the former backup slides from this revision.
- If including a demonstration, time it as part of the talk and keep a local screenshot or recording available. Verify the deck and PDF on the intended display setup.

## Review for common AI-generated presentation problems

Before accepting a draft, check these points:

| Problem | Required revision |
| --- | --- |
| The opening contains a subtitle, tagline, model name, or results | Keep only the agreed title. State the research question aloud and introduce results after the relevant context. |
| A substantive topic has no visible support | Add a short cue where it aids understanding. Spoken elaboration and transitions can remain in the script. |
| The audience understands the research question but still asks why the project matters | Connect identifying rejection to treatment-related assessment, then explain the binary model comparison and the user of the scoring prototype. |
| A technical label has several possible meanings | Define it with ordinary words and use the same term on the slide and in the script. |
| The deck lists tools and job-description keywords | Show a decision, the work that supports it, and its consequence. |
| Every slide uses the same three-box layout | Choose the layout from the information the slide needs to explain. |
| Color substitutes for structure, or a definition list becomes a flowchart | Use normal dark bullets and bold labels. Keep diagrams for meaningful relationships or processes. |
| Explanations accumulate beneath an otherwise complete slide | Move each necessary explanation beside the item it describes. Remove repetition. |
| Dense paragraphs repeat the HTML speaking script | Keep only essential labels and the evidence needed on screen. |
| A figure looks polished but lacks sample counts or a comparison | Add the missing information and verify it against the saved analysis. |
| Words such as “transformative,” “robust,” or “actionable” substitute for a finding | State the measured result or the specific action the evidence supports. |
| A kidney image or diagram appears to be measured evidence | Label the illustration and replace it when actual study evidence is required. |
| The conclusion quietly expands beyond the tested population | State the population actually evaluated and the validation still needed. |

## Ready-to-present check

- [ ] The argument is understandable without specialist gene-expression knowledge.
- [ ] The title slide contains only **Classifying Kidney Transplant Rejection from Biopsy RNA**.
- [ ] The slide immediately after the biopsy explanation explains why the classifier comparison is useful within an established molecular application. Banff supports the application, and the project's measured contribution is clear.
- [ ] Substantive topics have readable visual support, the slide order matches the script, and spoken elaboration does not create unnecessary slide text.
- [ ] RNA measurements, reference measurements, specimen IDs, and recorded diagnoses have distinct, explained roles.
- [ ] The visible results match saved outputs, including cohort counts and metric definitions.
- [ ] Claims have supporting evidence or an explicit label describing their uncertainty.
- [ ] Figures remain readable at presentation size, with no clipped labels or crowded annotations.
- [ ] The candidate can explain each methodological choice without reading the slide.
- [ ] The separate HTML speaking script contains the complete spoken text and only useful delivery cues, and PowerPoint notes are empty.
- [ ] The presentation targets 20 minutes with approximate pacing, and actual final rehearsal times are recorded.
- [ ] The local deck, PDF, offline report, and demonstration fallback open successfully.
- [ ] Slides 1–12 preserve the agreed purpose, context and model-choice explanation. Slide 4 includes the KDIGO treatment connection and slide 12 uses teal emphasis. The 14-slide sequence and three browser stops total a planned 20 minutes.
- [ ] Source acknowledgments and links to supporting documents are complete.

Presentation-design source verification date: September 15, 2026. Clinical-rationale
sources and their review date are recorded in [Research context](RESEARCH_CONTEXT.md).
