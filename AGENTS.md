# Kidney biopsy rejection classifier

## Purpose

Build an independent, reproducible kidney biopsy rejection classifier and a
20-minute presentation for a UNOS Associate Data Scientist interview. The main
question is whether molecular measurements from an existing transplant biopsy
can classify its recorded rejection diagnosis. The project should demonstrate
sound analysis and the ability to turn a model into understandable, tested software.

The clinical motivation is a molecular second opinion for specialists interpreting
uncertain transplant biopsies. Explain why RNA could add useful evidence from tissue
already collected, using the sources in `docs/RESEARCH_CONTEXT.md`. Present this
purpose positively and distinguish it from the current project's evidence of
classification performance. Added value in uncertain cases needs direct evaluation.

Read `docs/PROJECT_SPEC.md`, `docs/JOB_REQUIREMENTS.md`, and `docs/PLAN.md` before
substantial implementation. For presentation work, also read
`docs/PRESENTATION_SPEC.md` and `docs/PRESENTATION_GUIDE.md`.

## Independence

- This folder contains its own code, raw data, environment, analysis, and outputs.
  Do not depend on another project through imports, paths, environment settings,
  symlinks, Git worktrees, submodules, remotes, or linked data directories.
- Raw public source files may be downloaded or physically copied here and checked
  against their public-source manifest. Keep data and model binaries Git-ignored.
- Train models and generate results here. Do not copy fitted models, predictions,
  scores, plots, or completed analyses from another project.
- Source URLs and academic citations belong in provenance records. Files and
  commands must use paths relative to this project's root.
- A clean checkout must be able to download its inputs and rerun the workflow.
  This populated folder must also work without downloading the inputs again.

## Priorities

1. Make the question, inputs, comparison, and practical error counts clear.
2. Produce reproducible model comparisons using this folder's own runs.
3. Build one small prediction service and a useful demonstration.
4. Prepare and rehearse the full 20-minute presentation.

Use the job description as the standard for project evidence, not as a requirement
to demonstrate every listed technology. Avoid unnecessary frameworks, a large
frontend, distributed computing, and production infrastructure for this dataset.
Do not reopen the search for a different project unless the user requests it.

## Modeling

- Primary target: any recorded rejection versus no rejection. Antibody-mediated,
  T-cell-mediated, and mixed rejection all count as positive. Reject unknown labels
  rather than silently assigning them to a class.
- Use the public raw NanoString B-HOT measurements. Keep diagnosis, cohort, sample
  identifiers, and assay batch metadata out of predictors.
- Normalize each specimen using its 12 housekeeping targets. Fit any additional
  learned transforms and feature selection on training data only.
- Preserve the authors' discovery/technical-validation cohort definition and a
  reproducible discovery training/screening split. Use discovery data to choose
  models and thresholds.
- Repeating the same fixed procedure is reproduction. If evaluation results guide
  a change, describe the resulting comparison as follow-up analysis. This is a
  short methods note, not a reason to stop useful work or impose approval gates.
- Compare a constant baseline, IFNG, regularized multivariable logistic regression,
  and CatBoost on the same rows. Favor the simpler model when performance is similar.
- Explain false rejection flags and missed rejection cases alongside summary
  metrics. There is no required accuracy score and no requirement that CatBoost win.
- Call the output a model score until probability calibration has been assessed.
  Distinguish threshold selection from probability calibration.
- Describe what the data establish. Avoid claims of clinical deployment, improved
  patient outcomes, future rejection prediction, or verified patient/center
  independence without evidence. Keep limitations proportional to the claim.

## Implementation

- Use Python 3.12 and `uv`, with this project's lockfile and local environment.
- Keep the working research scripts until a shared module gives a clear benefit.
  Training and the final prediction service must use the same preprocessing code.
- Preserve completed runs. Write changed experiments to a clearly named new run
  directory with configuration, input hashes, model version, and outputs.
- Add tests for consequential failure cases: missing or duplicate targets,
  non-finite counts, inconsistent preprocessing, unexpected labels, and broken
  model/schema compatibility. Avoid coverage targets and trivial mirrored tests.
- Never load a model supplied by an API caller. Use the project-controlled model
  artifact. Keep credentials and uploaded data out of logs and version control.
- Do routine reversible work autonomously. Ask only when missing information
  materially changes the work or an action needs authorization.

## Presentation and writing

Use the dated external sources in `docs/PRESENTATION_GUIDE.md`. The talk lasts
20 full minutes, with questions afterward. Slides are a required project deliverable.
They must show the project's own results and working software, with editable
evidence and a separate HTML speaking script. Keep PowerPoint notes empty. After
the biopsy explanation on slide 2, explain the molecular second-opinion purpose
on slide 3, then show the supporting research. Put secondary methods and detailed
tables in backup slides.

Use plain English and a human voice. Prefer one concrete point over jargon,
buzzwords, abstract claims, and keyword lists. Use literal wording instead of
decorative metaphors. Do not inflate novelty or describe planned work as completed.
Keep progress updates focused on useful findings and what is being built.
