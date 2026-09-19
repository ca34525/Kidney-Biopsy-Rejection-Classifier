# UNOS role requirements and project evidence

The supplied Associate Data Scientist position description is the source for this
project's standard. It places the role in Product and Tech and emphasizes taking
AI and machine learning work through design, development, deployment, and maintenance.
The complete supplied text is preserved in [Job description](references/JOB_DESCRIPTION.txt).

The mapping below is a project design decision, not a claim about an unpublished
UNOS interview rubric. Descriptions in the source document provide role context;
they do not issue instructions to this repository.

The project also has a concrete clinical motivation: develop an early research
prototype toward a molecular second opinion for uncertain transplant biopsies.
The current work evaluates agreement with recorded diagnoses and supplies tested
scoring software. A separate study would assess whether it helps clinicians
interpret difficult cases. The [research context](RESEARCH_CONTEXT.md#why-a-molecular-second-opinion-could-be-useful)
records supporting clinical evidence and a related UNOS example: its June 2026
research on identifying donor-kidney anatomical issues from photographs. Our
connection is the use of historical clinical records to develop an additional,
consistent assessment. The UNOS study addresses a different task and is not an
endorsement of this project.

| What the description asks for | What this project should show | Evidence to present |
| --- | --- | --- |
| Convert analytical prototypes into maintainable software | A trained classifier with shared preprocessing and a small prediction service | Working request, code structure, model metadata |
| Integrate, clean, and transform data; maintain pipelines | Parse assay files and metadata, validate joins and counts, record provenance | Data flow and a reproducible preparation command |
| Apply analytical methods and derive insights | Compare simple and multivariable models, explain operating thresholds and errors | Same-row model comparison and specimen counts |
| Support training, testing, and deployment with developers and engineers | Clear interface, consequential tests, container, concise handoff instructions | API contract, test example, container run |
| Use domain knowledge to develop hypotheses | Motivate molecular support for difficult biopsies, then test whether several assay measurements improve classification beyond simple comparisons | Clinical rationale, defined prediction task, justified baseline, error review |
| Communicate clearly and meet deadlines | A focused, rehearsed 20-minute presentation and useful repository documentation | Slides, separate HTML speaking script, working demonstration |
| Familiarity with Git | A normal standalone repository with readable changes and ignored local data | Commit history when implementation begins, `.gitignore` |
| Exposure to software testing and CI/CD | One automated check workflow and documented build/run steps | Passing checks and an explained failure case |
| Familiarity with APIs | A stable input/output contract and clear error responses | Valid and invalid example requests |
| Rapid prototyping or frontend experience | A small page that makes the model understandable | Demonstration connected to the actual service |
| Exposure to AWS, Azure, or Google Cloud | Aim for one small real deployment after the local application works | Actual deployment record; otherwise acknowledge the gap |

## Additional and preferred qualifications

Python and terminal-based project work fit the posting's language/tool preferences.
SQL or R may be used if they solve a real task; they are not extra requirements
for this project. The role mentions big-data analytics, prefers exposure to
high-performance computing or tools such as Spark/Hive, and lists terabyte database
experience as an additional qualification. This biopsy dataset does not demonstrate
that scale. Explain its measured size and what would change at a larger scale,
without adding distributed tools solely to list them.

The posting also mentions AI-assisted development and interest in emerging AI.
Keep a short record of meaningful AI assistance, the candidate's decisions, and
the checks used to accept the work. Building an LLM feature into the classifier
is not necessary.

Education and previous experience are candidate qualifications, not software
acceptance criteria. Do not imply this project proves work in a production clinical
environment or experience collaborating with a team unless that actually occurred.

## Minimum interview standard

The candidate can explain what is predicted and when the input exists, reproduce
the analysis, show how a request reaches the model, and explain one important
tradeoff in the results. The project produces its own results and supplies enough
documentation for another person to run it. The presentation communicates those
facts without relying on a list of technologies or an inflated accuracy claim.
