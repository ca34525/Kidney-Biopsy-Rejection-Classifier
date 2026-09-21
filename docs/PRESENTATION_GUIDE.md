# Presentation guide

## Purpose

Prepare a **20-minute presentation** for the UNOS Associate Data Scientist interview about this kidney biopsy gene-expression classifier. The user confirmed that the full 20 minutes is presentation time. Questions come separately.

The user's September 18, 2026 instruction puts all spoken text and delivery cues in a **separate HTML speaking script**. Do not use PowerPoint notes. The [current draft](../presentation/README.md) has 20 main slides, 8 backup slides, and a complete script planned for 20 minutes. Real timed rehearsals remain pending.

The user's September 19, 2026 feedback sets the order and level of explanation. Open with only the title, **Classifying Kidney Transplant Rejection from Biopsy RNA**. Explain rejection and the biopsy with bold definition labels and evidence sub-bullets. Then use two matching, explicitly hypothetical examples to explain why a molecular second opinion could help. Follow the supporting research with the dataset, the outcome being classified, and the measurements used to predict it. Move the assay terminology to the appendix. Use ordinary bullets for parallel points and unbulleted accent lines for the requested summaries. Group explanations with their evidence. Substantive topics need visible support, but spoken elaboration and transitions do not each need a separate cue. These are the user's presentation preferences, separate from the external guidance summarized below.

The user’s latest feedback gives slide 14 the paired-bootstrap calculation and the reason for a separate development-split check: the bootstrap held training and selection fixed, and one training/screening assignment might favor a model. Slide 15 explains how the 20 discovery-only splits were made and presents the 13/20 CatBoost and 7/20 all-RNA logistic regression selections in an editable table. Remove the assessment-error dot plots from the slides; preserve the saved analysis outputs. The deck has 20 main slides and 8 backups. The comparison labels distinguish “IFNG only (Logistic regression)” from “All RNA (Logistic Regression).” Slide 11 remains unchanged.

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

- Assume a mixed audience of data scientists and transplant-domain colleagues until the panel composition is known. Explain the prediction target before introducing model terminology.
- Define biopsy and RNA in plain language before explaining the measurements. Keep assay, instrument, and panel terminology in backup slide 21. Give only the biological context needed to understand the data and label in the main talk.
- Immediately after explaining the biopsy, state the intended use: a molecular second opinion could give specialists additional evidence when a transplant biopsy is uncertain or conflicts with other findings. Explain that tissue appearance and gene activity provide different information from the existing tissue.
- Make the positive case with its evidence. Current Banff guidance considers validated molecular tests in difficult cases, and research using the B-HOT panel supports investigating information beyond the initial microscopic diagnosis. Then identify the contribution here: a reproducible classifier and software for further evaluation. Added benefit in uncertain cases remains the next research question.
- Keep the title slide to **Classifying Kidney Transplant Rejection from Biopsy RNA**, with no subtitle, tagline, or other content. State the research question aloud. Introduce the model comparison and error counts after the audience understands the specimens, diagnoses, and evaluation groups.
- Draft the central question in one sentence. State what information the model receives, what label it predicts, and which biopsy population the analysis covers.
- Organize around the work: why the question matters, what the data contain, how the evaluation works, what happened, and what the result supports.
- Use first-person singular for the presenter's work throughout the slides and speaking script: I, my, and me.
- Call this work a personal project, never a study. Reserve “study” for published research. Describe completed project actions in the past tense, such as “I used” and “I evaluated.” Keep present tense for biological facts and current software behavior.
- Distinguish an RNA measurement from the diagnosis the model predicts. Prefer "RNA measurement" or "RNA type measured" in audience-facing explanations. Each count summarizes signals associated with one type of RNA, rather than one individual molecule. When an exact assay or software term requires "target," define it as the RNA type the assay measures. Call the predicted outcome the "recorded diagnosis" or "rejection label."
- Call a sample identifier a "specimen ID." Explain that it identifies the source record and does not enter the model. Reserve "study accession" for the dataset reference in source material.
- Introduce "cohort" on slide 9, where the discovery and validation groups are explained. Both groups are used. Distinguish the authors' division from this project's training/screening split within discovery. The 1,395 observations are specimens rather than people and include 202 native-kidney controls. Do not describe the dataset as exclusively transplant biopsies.
- Explain decisions through concrete examples. For example, show why a missing required RNA measurement causes the service to reject an input instead of producing a misleading score.
- Explain the candidate's own contributions accurately. Credit the public dataset and any borrowed methods at the point of use.
- End with the measured finding, its main limitation, and the next justified step. Do not promise an outcome before the analysis exists.

### Make each slide understandable

- Give each substantive slide one job. Prefer a short topic title for definitions, processes, and setup. Use a factual takeaway title when the slide establishes a result. Do not force background material into a conclusion.
- On slide 2, keep the gaps between visible definition blocks consistent, accounting for wrapped lines. Avoid an oversized gap after the single-line rejection definition.
- On slide 4, explain in plain language that unnecessary rejection treatment can weaken infection defenses. Keep that clinical rationale separate from any claim that this project's error tradeoff improves care; the [biopsy-care review](references/BIOPSY_CARE_20260919.md) records the evidence.
- Slide 16 should clearly introduce the prediction service and demonstration. Present slide 19 as possible extensions of a personal project. On slide 20, separate the model comparison from the service/demo, show percentages with denominators, and close on completed work without another next-step bullet.
- Under that title, show the relevant evidence. Use ordinary dark-text bullets for parallel statements and numbered steps for a calculation. Retain diagrams for the study split and prediction software. Use definition bullets and biopsy-evidence sub-bullets on slide 2, and paired hypothetical-example boxes on slide 3.
- Use bold labels to distinguish a term from its explanation. Reserve color for consistent meanings, including the requested unbulleted summary lines. Keep bullet hierarchy clear without relying on color alone.
- Place explanations beside the number, table, or diagram they explain. For the 758/12 measurement breakdown, group the meaning of target counts under 758 and the role of housekeeping references under 12. Avoid unrelated statements tacked onto the bottom of a slide.
- Show backup slide 21 as a clear bullet explanation of RNA, the NanoString nCounter measurement system, the B-HOT panel, and an example. On slide 5, use two compact table schemas with specimen ID as the one-to-one key. Explain in the script that code assembles these analysis tables from public files. Omit the redundant on-slide caption about assembling the tables.
- Explain the housekeeping references on the measurements slide as a way to adjust for differences in how much RNA each specimen supplies. Keep the normalization slide focused on the compact numbered calculation for each of the 758 target counts, without repeating that explanation. Keep the separate training-fitted scaling explanation with the relevant model or backup methods.
- Keep qualifications short and close to the claim they qualify. Give the scope statement on slide 4 visual emphasis: "This project measures agreement with recorded diagnoses. Its value in ambiguous biopsies needs direct evaluation." Put the patient and referring-center separation note on slide 5, directly under the line with 1,193 transplant biopsies and 202 native-kidney controls. Make both lines bullets with identical font size and no asterisk. Keep slide 9 focused on the study split. Do not repeat obvious process statements or data QA results on slides whose purpose is to explain the data.
- Put the explanation for delivery in the separate HTML speaking script, with spoken text visibly separated from delivery cues. Keep PowerPoint notes empty. The visible slide should contain the words needed to understand its evidence and follow the spoken discussion.
- Choose a few consistent type sizes and a restrained color palette. As a starting point, use roughly 28–32 point body text and 36–44 point titles. These are project defaults, not scientifically established thresholds.
- Test readability at the actual display size. Enlarge chart labels separately from the slide text. Move secondary detail to an appendix when it cannot remain readable.
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
- Give each metric a short interpretation. On slide 11, show recall (sensitivity) as recorded rejection cases detected over all recorded rejection cases, and precision as flags with recorded rejection over all positive flags. Use stacked fractions with words instead of abbreviations or "proportion of" definitions. Define false negatives as missed cases and false positives as incorrect flags. Keep those terms visible on the validation-results chart.
- Describe the actual screening rule: require at least 90% recall, then minimize false positives. The second criterion directly maximizes specificity. In the saved screening comparison, each candidate detected 157 rejection specimens, so fewer false positives also meant higher precision among those choices. In general, the recall floor permits different true-positive counts and the two objectives can differ. Mark 90% as an experiment choice, and state that validation recall fell below it. Clinical error costs depend on how the score is used. The original study discusses harm from additional immunosuppression when infection is mistaken for rejection, so do not treat false negatives as uniformly more consequential.
- Explain IFNG as an immune-related one-measurement benchmark fixed in the project recipe. Its association with T-cell-mediated rejection supports that interpretation, but does not establish it as the best individual predictor or as specific to rejection. Keep the output labelled "model score" because its numerical probability interpretation remains limited.
- Show uncertainty where it has been estimated. Name what an interval represents. Do not manufacture error bars or claim an improvement from a small visible gap alone.
- On slide 14, explain the confidence interval calculation. CatBoost detected eight more of the 169 rejection specimens, a +4.73 percentage-point recall difference. The paired bootstrap resampled 345 validation specimens with replacement 2,000 times, with fixed models and thresholds and the same draws for both models. For each draw, subtract all-RNA logistic regression recall from CatBoost recall. The middle 95% of differences, bounded by the 2.5th and 97.5th percentiles, gave approximately −0.01 to +9.74 percentage points. The interval includes zero. Below this, explain why a separate development-split check was needed: one training/screening assignment might favor a model, and the bootstrap did not repeat training or selection. Ask whether changing those assignments changed the selected model. Keep split counts, design, and results on slide 15.
- On slide 15, explain the 20 fixed-seed random splits of 1,050 discovery specimens. Hold out 210 assessment specimens, then 210 screening specimens, leaving 630 for fitting; both steps approximately preserve the four diagnosis proportions. Both families used identical partitions and all 758 measurements. Screening required at least 90% recall, then selected by fewest false flags, using ROC-AUC to break ties. Assessment measured later errors without changing selection; the 345 author-validation specimens were not used. Present the selection counts in an editable table: CatBoost 13/20 and All RNA (Logistic Regression) 7/20. Omit the assessment-error dot plots. The repetitions overlap, so they are not independent trials and the counts do not prove a winner. This follow-up did not change the demonstrated model. Link the saved design, summary, selections, and report from the script.
- Explain consequential errors using actual counts or de-identified examples from the evaluation. Keep hypothetical examples clearly labeled.
- Retain units, denominators, axis labels, and relevant baselines. If simplifying a chart for the talk, preserve the values and comparisons.
- Describe a gene's model contribution as an association. A useful predictor does not by itself establish a biological cause.
- Introduce the plausible use before the methods, with a brief qualification that this prototype tests classification of recorded diagnoses. Later, explain how a study of uncertain biopsies could test whether adding the molecular score improves assessment. Keep the distinction clear without letting a list of limitations replace the project's purpose.
- Describe the recorded labels as histological diagnoses. Banff 2019 rescoring applies to the transplant biopsies. The full article excludes borderline acute T-cell-mediated rejection, chronic inactive antibody-mediated rejection, and chronic active T-cell-mediated rejection with an inflammation score below two. Explain those specific exclusions in the backup script rather than claiming that all ambiguous specimens were absent. This project has not directly tested added value in ambiguous cases.
- Separate referring centers from the processing laboratory. The study reports broad geographic referrals and processing at Arkana Laboratories. It does not document allocation that separates patients or referring centers. The public data also lack identifiers needed to verify such separation. Preserve that distinction when describing evaluation and specimen-level uncertainty intervals.
- Keep external clinical evidence separate from this project's results. Rosales et al. studied signals associated with later chronic active antibody-mediated rejection; this classifier does not forecast future rejection. The UNOS kidney-photo study illustrates research toward supporting expert assessment in a different task and does not establish endorsement of this project.
- Generate quantitative figures from saved analysis outputs. Every reported number must match a reproducible result. Never use generated images to depict results, observations, or diagnostic performance.

These evidence requirements are project choices. The presentation sources above support clear communication, but do not prescribe this classifier's methods or establish medical claims.

### Use all 20 minutes deliberately

- Plan for a full **20-minute** talk, including the opening and conclusion. Questions follow it. Use approximate section allocations rather than optimizing individual slides to exact elapsed seconds.
- Use 20 main slides and 8 backup slides for this revision, following the user’s request for a dedicated model-choice results slide. The assay explanation remains the first backup. Keep the planned talk at 20 minutes by reallocating approximate time within the existing sections. There is no universal bullets-per-slide formula.
- Rehearse the complete talk aloud, with the real figures and transitions. Record elapsed time at section boundaries.
- Treat per-slide and cumulative times in the HTML as rough pacing aids. They are not measured performance or a reason to spend extensive effort tuning estimates. Let actual rehearsals determine which sections need more or less time.
- If the talk runs long, remove secondary material. If it runs short, explain an important result or decision more clearly. Do not fill the time with generic background.
- Complete at least two final rehearsals close to 20 minutes at a natural pace. Record the times and remaining rough spots. This is the project's rehearsal standard.
- Ask a practice listener to explain the prediction target, the evaluation setup, and the main conclusion afterward. Revise any point they cannot explain accurately.
- Put detailed methods and likely answers in backup slides after the conclusion. They are outside the planned 20-minute sequence.
- If including a demonstration, time it as part of the talk and keep a local screenshot or recording available. Verify the deck and PDF on the intended display setup.

## Review for common AI-generated presentation problems

Before accepting a draft, check these points:

| Problem | Required revision |
| --- | --- |
| The opening contains a subtitle, tagline, model name, or results | Keep only the agreed title. State the research question aloud and introduce results after the relevant context. |
| A substantive topic has no visible support | Add a short cue where it aids understanding. Spoken elaboration and transitions can remain in the script. |
| The biopsy explanation leaves the audience asking why another assessment is needed | Put the molecular-second-opinion use case immediately after it, then show the external evidence and the part this project tests. |
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
- [ ] The slide immediately after the biopsy explanation states who could use molecular evidence and when it could help. External support and the project's measured contribution are distinguishable.
- [ ] Substantive topics have readable visual support, the slide order matches the script, and spoken elaboration does not create unnecessary slide text.
- [ ] RNA measurements, reference measurements, specimen IDs, and recorded diagnoses have distinct, explained roles.
- [ ] The visible results match saved outputs, including cohort counts and metric definitions.
- [ ] Claims have supporting evidence or an explicit label describing their uncertainty.
- [ ] Figures remain readable at presentation size, with no clipped labels or crowded annotations.
- [ ] The candidate can explain each methodological choice without reading the slide.
- [ ] The separate HTML speaking script contains the complete spoken text and only useful delivery cues, and PowerPoint notes are empty.
- [ ] The presentation targets 20 minutes with approximate pacing, and actual final rehearsal times are recorded.
- [ ] A local deck, PDF, and any demonstration backup open successfully.
- [ ] Source acknowledgments and backup slides are complete.

Presentation-design source verification date: September 15, 2026. Clinical-rationale
sources and their review date are recorded in [Research context](RESEARCH_CONTEXT.md).
