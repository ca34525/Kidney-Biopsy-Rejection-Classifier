# Can biopsy findings affect care?

Research checked September 19, 2026. Slide 3 was reviewed as a research question;
its content was not changed in this revision.

## Conventional biopsy findings

Yes. The [KDIGO transplant-recipient guideline (2009), summarized in its clinical
guide](https://kdigo.org/wp-content/uploads/2017/02/KDIGO_TX_NephsTool-Managing-Kidney-Transplant-Recipients.pdf),
page 4, recommendations 6.1 and 6.3, links biopsy diagnosis to treatment: obtain
a biopsy before treating suspected acute rejection unless it would substantially
delay care, and use corticosteroids initially for acute cellular rejection.
Recommendation 7.2 also links biopsy evidence of drug toxicity to medication
adjustment. These are examples of findings informing care, not advice for an
individual patient.

## Molecular biopsy measurements

[Kumar et al., Transplantation, August 2025](https://pubmed.ncbi.nlm.nih.gov/39710875/)
(online December 23, 2024; DOI 10.1097/TP.0000000000005296) reported incorporating
Molecular Microscope gene-expression results into care for suspected T-cell-mediated
rejection. The single-center study included 209 patients. Thirty cases with
histologic rejection but molecular quiescence did not receive rejection therapy;
35 with both findings received treatment. The untreated group had outcomes
comparable to the group without rejection.

This is direct evidence of molecular findings informing treatment decisions.
It is observational, so it does not establish that withholding therapy caused
better outcomes or that the same policy is safe for other patients. MMDx is a
different test from this project's raw B-HOT classifier.

## Why incorrect rejection calls matter

The [2024 Second International Consensus Guidelines on BK Polyomavirus](https://pmc.ncbi.nlm.nih.gov/articles/PMC11335089/),
Pathology and Management sections and Tables 4 and 7, explain that biopsy findings
must be interpreted with clinical and viral information. For sustained BK infection
or biopsy-proven BK nephropathy without concurrent rejection or high immunologic
risk, the main treatment is to reduce immune suppression.

Together with the rejection guidance, this supports the clinical concern that
mistaking infection for rejection could lead to unnecessary immune suppression
and worsen infection. Zhang et al. also explicitly discuss this concern on page
13 of the source study; see the [full-study audit](STUDY_AUDIT_20260919.md).

Plain slide wording: “Unnecessary rejection treatment can weaken the body’s
defenses and worsen an infection.” This describes a potential consequence of an
incorrect diagnosis, not an observed benefit of this project's score.

## What the model comparison establishes

The [saved evaluation](../../results/analysis/20260915_baseline/model_metrics.csv)
uses the same 169 recorded rejection and 176 no-rejection specimens for each model:

| Model | Missed rejection | Incorrect flags among no rejection |
| --- | ---: | ---: |
| IFNG | 14/169 (8.3%) | 75/176 (42.6%) |
| Logistic regression | 33/169 (19.5%) | 8/176 (4.5%) |
| CatBoost | 25/169 (14.8%) | 8/176 (4.5%) |

At the selected thresholds, CatBoost made 67 fewer incorrect flags and 11 more
misses than IFNG. Reducing incorrect flags is a reasonable research aim, but
these results do not establish a better clinical tradeoff. No treatment decisions
or patient outcomes were evaluated, and diagnostic labels are the reference.
CatBoost's evaluation recall was 85.2%, below the 90% screening target. Its
advantage over logistic regression remains uncertain in the paired analysis.

The presentation should explain both errors without inventing clinical cost
weights or changing the model after seeing this comparison. Possible clinical
extensions are hypothetical and would require collaborators and suitable data.
