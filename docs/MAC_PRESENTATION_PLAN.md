# Laptop presentation plan

Decision recorded September 22, 2026 UTC: use this laptop's completed Mac run
as the canonical source for the presentation in two days. This means the talk,
live application and offline fallback should all describe the same local run.
It does not mean that every desktop result reproduced exactly.

Work on `codex/mac-presentation`. Keep `main` at its existing revision for now.
Keep newly generated CSV files Git-ignored. Preserve the historical desktop runs
and the Mac comparison record. Defer investigation of cross-platform differences
until after the presentation, when the original desktop artifacts can be supplied.

## Frozen presentation sources

| Item | Canonical local source |
| --- | --- |
| Primary run | `results/reproduction/20260922_mac_clone` |
| Fitted models | `data/processed/models/20260922_mac_clone` |
| Model version | `20260922_mac_clone:any_rejection:catboost_all_depth4` |
| Threshold | `0.8765880870219773` |
| Primary report | `results/analysis/20260922_mac_clone` |
| Stability follow-up | `results/followup/20260922_mac_clone_stability` |
| Subtype follow-up, for questions | `results/followup/20260922_mac_clone_subtypes` |
| Public examples | `data/demo/20260922_mac_clone` |
| Software verification | `results/checks/20260922_mac_clone` |

The main validation counts are unchanged: CatBoost missed 25 of 169 rejection
cases and falsely flagged 8 of 176 no-rejection cases; logistic regression
missed 33 with 8 false flags. All 20 stability selections match the desktop
record: CatBoost 13, logistic 7. The current local checks include 94 passing
tests and agreement across HTTP, CLI and saved local scores for 345 specimens.

Freeze these models, thresholds, dependency versions and results for the talk.
Do not retrain, tune, change the evaluation method, or pursue exact desktop
reproduction before the presentation. Address a newly discovered material error
if one appears; otherwise spend the remaining time on presentation consistency
and rehearsal.

## Today: make the presentation use this run

1. Preserve the existing presentation snapshot and generated deliverables before
   updating them. Use the Mac run's actual identity; do not rename it to the
   desktop model version.
2. Update the presentation's evidence sources to the Mac report, stability
   records, configuration and HTTP check. The current builders still hardcode
   desktop paths. Keep this choice explicit in a small shared configuration or
   command arguments so capture, build, launch and checks use the same sources.
3. Capture new valid and invalid responses and the public-specimen walkthrough
   from the Mac model. Rebuild the engineering demonstration and its embedded
   source records. The existing page checks model version and threshold against
   its saved snapshot and will otherwise reject the Mac service as a different
   model. Preserve this check.
4. Refresh the HTML report and speaking script wherever they identify a run,
   show an actual response, or give launch instructions. Check the slides against
   the Mac evidence; retain the established structure and charts where the
   displayed values agree. Rebuild the deck/PDF only for necessary corrections.
   Keep PowerPoint notes empty.
5. Date verification claims accurately. Use the new local HTTP and test records.
   Label the existing Docker check as earlier desktop evidence if it remains in
   the talk. Preparing a serving bundle is not a Mac container verification.
   Docker or cloud deployment is not required to prepare this presentation.
6. Verify one presentation launch command, all three browser stops, the valid
   specimen, the incomplete-file rejection, and the saved-response fallback.
   Confirm that live and saved views display the same model version, threshold
   and example result. Check local links with the network unavailable.

Completion: the slide deck, script, engineering page and live service tell one
consistent story from the frozen Mac run. This update is planned, not yet done.

## Tomorrow: rehearse and prepare the fallback

1. Complete two timed rehearsals of the full 20-minute talk, including the
   transition after slide 13, the continuous browser demonstration, and the
   return to slide 14. Keep questions outside the 20 minutes.
2. Record actual timing and rough spots. Shorten secondary detail if necessary;
   preserve the clinical motivation, model comparison and software explanation.
3. Rehearse an interruption: stop the service and continue using the clearly
   labeled saved response. Verify the PDF and HTML files open independently.
4. Save a separate local presentation backup containing the final deck, PDF,
   script, self-contained engineering page and its source/version manifest.
   When external storage is available, copy the presentation package and the
   required ignored model/example artifacts as a separate backup. Git alone does
   not back up these ignored files. Do not plan to copy the Mac virtual environment
   to Windows; use the lockfile to create an environment there.
5. Freeze the verified presentation package after rehearsal. Keep only fixes
   needed for an actual presentation problem within the remaining scope.

## Presentation day

Open the files on this laptop, start the verified presentation launcher, confirm
the page says Live application, and test the valid and incomplete examples once.
Keep the PDF and saved-response fallback immediately available. Check display
scaling, screen sharing and the PowerPoint/browser transitions on the intended
display. Use the frozen package without another training or dependency update.

## Windows compatibility and Git boundaries

The only existing tracked code change from setup is a test assertion using
`Path.resolve()`, matching the application's existing path handling. This is
portable Python and does not introduce a known Windows incompatibility. Windows
tests have not been rerun. The ignored `.sh` launch helpers require a Unix shell;
they do not replace the repository's PowerShell instructions.

Make subsequent presentation configuration work portable through Python,
project-relative paths and environment variables; do not make model selection
depend implicitly on the operating system. Provide the corresponding PowerShell
launch form when updating the presentation instructions.

At the start of this plan, the Git index was empty. Creating the branch does not
commit changes or back up generated results. Stage only deliberately selected
code/documentation/presentation files when preparing a commit. The repository's
ignore rules exclude new CSVs (regardless of extension case), `.DS_Store` and
macOS resource-fork files from ordinary staging. Historical CSV evidence already
tracked by Git remains tracked. Review the staged file list before committing.

After the presentation, compare original desktop predictions with the saved Mac
predictions, investigate the documented differences, and decide which portable
setup improvements should merge into `main`.
