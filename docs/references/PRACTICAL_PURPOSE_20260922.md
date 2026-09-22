# Practical purpose and opening narrative

September 22, 2026. This records the user's accepted distinction between a
plausible practical application and proven clinical benefit. It supersedes the
purpose wording in the September 21 note and the slide 3 proposal in the earlier
September 22 context pass. Historical notes remain unchanged.

## Rationale

Whether rejection is present can affect decisions about further treatment to
suppress the immune system. A binary molecular score could supply additional
evidence during that assessment, while subtype and other findings would still
guide treatment. This potential role supplies a concrete reason to study the
binary endpoint. The project does not need to establish a new clinical use or
demonstrate patient benefit to have a meaningful applied purpose.

The distinction is relevant, and the current experiment tests agreement with
recorded diagnoses. Whether this particular score helps assessment is open for
further investigation. Avoid letting repeated qualifications displace the purpose.

## Evidence and interpretation

- [Zhang et al., 2024](https://doi.org/10.1016/j.labinv.2023.100304), Discussion,
  page 13, explicitly prioritizes whether a biopsy diagnosis prompts further
  immunosuppression. The authors explain why they included infection controls
  to reduce harmful rejection diagnoses. The locally preserved main article
  and supplements are recorded in `rejection_source_manifest.json`.
- [KDIGO transplant-recipient guideline summary, 2009](https://kdigo.org/wp-content/uploads/2017/02/KITxpGL_summary.pdf),
  recommendations 6.1–6.4, connects biopsy assessment and rejection treatment and
  distinguishes treatment for different rejection types. Reviewed again for
  this revision. This supports the decision's relevance; it does not evaluate
  this project's score.
- The [September 19 biopsy-care review](BIOPSY_CARE_20260919.md) documents the
  infection example and the distinction between clinical context and model benefit.
- The potential role for this binary score is an inference from that context.
  Neither these sources nor the current model evaluation proves added clinical value.

## Two aims and presentation sequence

**Model comparison:** How do logistic regression and CatBoost compare in
classifying any recorded rejection versus no rejection from B-HOT biopsy RNA,
particularly in missed cases and incorrect flags?

**Software engineering:** Make preprocessing, training and evaluation reproducible.
Build a tested scoring service and prototype application that let a user submit
a specimen's RNA counts and inspect its model score, threshold and rejection flag.

The prototype lets an analyst or molecular laboratory researcher try the selected
model on compatible inputs and inspect the output. Its API makes the same scoring
procedure available to other software. The immediate software demonstration is
concrete even though a clinician-facing use of this score remains to be studied.

Slide 2 defines the biopsy measurements. Slide 3 provides the treatment-related
motivation and gives the two aims equal visual weight. Slide 4 provides Banff and
Zhang context. The closing narration returns to the comparison and software
evidence. Detailed qualifications and alternative research tasks belong in the
supporting documents and next-step discussion.

The different training endpoint is a substantive difference from Zhang's study.
It does not establish superiority or novelty. Binary and four-class accuracy are
not directly comparable. Faithfully reconstructing Zhang and predicting future
rejection are possible extensions with different analytical requirements, recorded
in [Next steps](../NEXT_STEPS.md).

This revision changes narrative and presentation artifacts. It leaves the saved
analysis, fitted models, thresholds and application behavior intact. Consolidating
the engineering demonstration into one browser sequence is a separate presentation
change still to be implemented.
