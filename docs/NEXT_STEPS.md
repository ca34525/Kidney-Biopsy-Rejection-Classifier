# Questions for later work

These ideas are deferred. They are not changes to the frozen service or additions
to the current implementation scope. The latest completed work is a specimen
walkthrough, a [discovery-only stability comparison](../results/followup/20260917_stability/REPORT.md),
presentation figures, and small consistency fixes. The presentation now explains
the molecular-second-opinion rationale, supported by the sources in
[Research context](RESEARCH_CONTEXT.md). Timed rehearsals remain required delivery
work.

## Short version for a slide

1. **Does the score help specialists assess uncertain biopsies?** Compare usual
   assessment with assessment that also includes the molecular score.
2. **Does the comparison hold in a new, assay-compatible cohort?** Establish
   patient and center identities and review laboratory quality before evaluation.

Calibration and feature-sensitivity analyses remain useful supporting questions.

## What each question would add

### Added benefit for uncertain biopsies

The intended use is additional evidence for specialists interpreting an uncertain
kidney transplant biopsy, including cases whose tissue findings conflict with
other evidence. A direct study would compare usual assessment with assessment
that also includes a molecular score. It would predefine what counts as an
uncertain case, separate training from evaluation, and use independent expert
review or relevant follow-up outcomes to assess the interpretations. Simply
agreeing with the original training labels would not answer this question.

Measure whether the score helps resolve uncertainty correctly and how often it
misleads review. Record assay failures, time, and cost so that an improvement in
interpretation can be weighed against the extra work. This would test the
project's proposed clinical role. It is future research, supported by the
clinical rationale in [Research context](RESEARCH_CONTEXT.md), rather than a
change to the frozen classifier or the current implementation scope.

### An independent comparison

The current author technical-validation cohort is held out from this project's
model selection, but it is part of the same deposited study. All biopsies were
processed at Arkana Laboratories; patient and referring-center separation between
cohorts is not documented. Repeating discovery splits measures a different
uncertainty: dependence on the development specimens.

The [September 19 source review](references/STUDY_AUDIT_20260919.md) also establishes
that the dataset includes 202 native-kidney controls alongside 1,193 transplant
biopsies. Eleven native-kidney controls are in technical validation. Obtaining the
specimen-level mapping would allow a separate assessment restricted to transplant
biopsies; the public metadata do not currently supply that mapping.

The next useful preparation would be a feasibility check for another public
cohort with compatible raw targets, labels, and preprocessing. Fix the inclusion
rules and evaluation procedure before inspecting its results. Obtain patient and
center identities sufficient to check independence, and document laboratory
quality checks. A compatible new
cohort would add evidence about generalization; a mismatched assay would instead
require a separately described adaptation study. No suitable external cohort has
been established here. See the [GSE212160 deposit](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE212160)
and [source study](https://pubmed.ncbi.nlm.nih.gov/38092179/) for the present data's scope.

### Assay and feature sensitivity

The files contain control probes and assay metadata, but the project has not
independently repeated laboratory QC. The [viral review](../results/analysis/20260915_viral/REPORT.md)
also found prominent BK-target importance and a small high-signal group confined
to recorded no-rejection specimens. This association alone does not show that
viral measurements caused a prediction or that they are inappropriate inputs.

Three separate, predeclared follow-ups could help: review available QC fields
against applicable manufacturer guidance; repeat development evaluation with
assay groups held apart where diagnosis coverage permits; and fit comparisons
with specified viral targets removed. Record how many specimens or features each
change affects, then compare error counts. None establishes patient independence,
and batch-group results cannot separate processing from specimen composition by
themselves. The raw material exists, but the QC rules and grouped-split feasibility
still need review. Sources: [manufacturer analysis guidance](https://brukerspatialbiology.com/support/knowledgebase/ncounter-data-analysis/),
[B-HOT consensus and panel description](https://pmc.ncbi.nlm.nih.gov/articles/PMC7496585/),
and [study Supplementary Methods](https://ars.els-cdn.com/content/image/1-s2.0-S0023683723002477-mmc6.docx).

### Better score interpretation

The current reliability analysis supports calling the output a model score.
It has not fitted a calibration model. A bounded comparison could fit calibration
using discovery data with separation from model fitting, then evaluate reliability
and practical error counts. Threshold selection and calibration answer different
questions; improving one does not establish the other.

This would add evidence about how score ranges relate to observed rejection
fractions. It would not establish a reliable probability for a new individual or
a clinically justified decision threshold. A calibration fit is feasible with the
existing data, but the already inspected technical-validation results must be
reported as follow-up evidence. See [scikit-learn's calibration guidance](https://scikit-learn.org/stable/modules/calibration.html)
and the [current reliability results](../results/analysis/20260915_baseline/REPORT.md#score-reliability).

## Other ideas kept out of the current work

| Idea | Why defer it; evidence a later implementation could add |
| --- | --- |
| Cloud demonstration | The deployment procedure exists, but actual account deployment is separate work. A verified endpoint would demonstrate cloud execution. |
| Deployment latency, capacity, and recovery exercise | A controlled run could measure startup, request times, memory, and restoration of a previous model. Local container correctness checks do not establish these measurements. |
| Threshold explorer | Could teach the missed-case/false-flag tradeoff. It would need explicit exploratory labeling and must not change the service's frozen threshold. |
| SHAP or other individual feature explanation | Could describe model contributions, but would need careful treatment of correlated targets and would not identify the biological cause of an error. |
| More model families or larger tuning searches | The main uncertainty is the stability and usefulness of a small observed difference, not a shortage of algorithms. |

UNOS's [public predictive-analytics description](https://unos.org/technology/predictive-analytics/)
connects models to a user workflow and ongoing updates. Its historical
[2023 presentation, pages 12–13](https://hrsa.unos.org/media/a2nmkekk/predictive-analytics-in-donornet-for-website-posting.pdf)
discusses monitoring, calibration, and population limits. Those sources motivate
clear model documentation and future maintenance questions; they do not establish
the current implementation of UNOS systems or a requirement to copy their tools.

Existing source context was reviewed September 15–19, 2026. Recheck methods and
service documentation before implementing any deferred work.
