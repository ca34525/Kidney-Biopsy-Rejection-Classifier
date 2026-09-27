# Current project status

Updated September 27, 2026. The analysis, scoring application and presentation
package are built. The user reports that the presentation has taken place.
Three [analysis notebooks](../notebooks/README.md) now add data-quality checks,
EDA, and RNA contribution plots as a retrospective deliverable.

## Start here

| Need | Read |
| --- | --- |
| Question, main error counts, setup and reproduction | [Project README](../README.md) |
| Read the executed data checks, EDA, and model explanations | [Analysis notebooks](../notebooks/README.md) |
| Deliverables and analytical contract | [Project specification](PROJECT_SPEC.md) |
| Clinical motivation and source evidence | [Research context](RESEARCH_CONTEXT.md) |
| Relationship to the interview role | [Job requirements](JOB_REQUIREMENTS.md) |
| Run the application or use the API | [Application guide](API.md) |
| Use the same branch on Windows and macOS | [Setup guide](SETUP.md) |
| Follow preprocessing and prediction | [Code guide](CODE_GUIDE.md) |
| Run checks and find dated evidence | [Verification](VERIFICATION.md) |
| Present, rehearse or rebuild | [Presentation package](../presentation/README.md) |
| Deferred research | [Next steps](NEXT_STEPS.md) |

## Runs and evidence

The presentation launcher defaults to
`results/reproduction/20260922_mac_clone` through
`presentation/source/demo_config.json`. The generic CLI/API default remains
`results/reproduction/20260915_shared`; these are separate launch configurations.
Windows now uses the same presentation launcher with explicit `--run-dir` and
`--demo-dir` options for its preserved model. The [September 27 checks](../results/checks/20260927_portability/README.md)
record 105 installed-package tests and HTTP/CLI/saved agreement on all 345 specimens.
CI now checks Windows, macOS and Linux; the PR reports the hosted run status.
The presentation's [source record](../presentation/README.md#frozen-run-and-evidence)
distinguishes the Mac demonstration from the earlier desktop reports and container
checks still included in its reference library.

| Evidence | What it establishes |
| --- | --- |
| [Primary analysis](../results/analysis/20260915_baseline/REPORT.md) | Same-row errors, paired uncertainty and score reliability on 345 specimens. CatBoost missed 25/169 rejection cases and flagged 8/176 no-rejection cases; logistic missed 33 with 8 false flags. |
| [Discovery stability](../results/followup/20260917_stability/REPORT.md) | CatBoost selected in 13 of 20 overlapping development splits, logistic in 7; a dependable preference remains unsettled. |
| [Mac reproduction and checks](../results/checks/20260922_mac_clone/README.md) | Main model choices and validation counts agree with the desktop record; 94 tests passed and all 345 local HTTP/CLI/saved scores agree within tolerance. Some cross-platform numeric differences remain. |
| [Windows/Mac investigation](../results/checks/20260922_windows_mac_investigation/README.md) | Later direct comparison found matching saved primary, subtype and stability flags and investigated training differences. |
| [Source-study review](references/STUDY_AUDIT_20260919.md) and [methodology review](METHODOLOGY_REVIEW.md) | Establish the transplant/native-control composition and distinguish the project's methods from the published model. |
| [Subtype follow-up](../results/followup/20260915_subtypes/REPORT.md) and [viral review](../results/analysis/20260915_viral/REPORT.md) | Supporting analyses; neither replaced the binary service. |

The 345-specimen evaluation includes 334 transplant biopsies and 11 native-kidney
controls. Patient and referring-center separation are not documented. The work
establishes agreement with recorded diagnoses and consistent software scoring;
added clinical value remains untested. The [AWS procedure](AWS_DEPLOYMENT.md)
exists, but no cloud deployment has been performed.
