# Code guide source

Open [the complete offline guide](../TECHNICAL_OWNERSHIP.html) in a browser.
It pairs workflow diagrams with detailed explanations, linked source and tests,
one prepared public specimen, change guidance, and exercises with answers.

All commands below run from the project root with the project's Python 3.12 environment:

```powershell
uv run --frozen python scripts/build_ownership_guide.py
uv run --frozen python scripts/build_ownership_guide.py --check
```

The ordinary build uses only Python's standard library, checked-in source, and
the stored public example. It does not need raw study files or model binaries.
The HTML embeds its styles, behavior, SVG diagrams, and source listings; it needs
no network connection. Related documentation and local-file links work within
the checkout. The internal source links work even when the HTML is copied alone.

## Editing

- `data.json` through `operations.json`: the six workflow chapters. Explain
  purpose, inputs, steps, outputs, reasoning, failures, changes, and checks.
- `diagrams.json`: editable node positions, script/function labels, and labeled
  call/read/write connections. Each function resolves to an explanation.
- `guide.css` and `guide.js`: responsive layout, navigation, search, expand/collapse,
  and printing. The print control expands explanations and exercise answers.
- `specimen.json`: a calculation using the prepared public no-rejection example
  and the frozen research predictor. Full-precision values and provenance are
  stored here; the HTML rounds them for reading.
- `build_manifest.json`: generated record of source revision, input hashes, and
  output hash. Keep it with the generated HTML.

To recalculate the example after changing its calculation code:

```powershell
uv run --frozen python scripts/build_ownership_guide.py --refresh-example
```

This optional operation needs the populated project's prepared examples and
frozen model. It verifies the example CSV and loads the model through the shared
loader; it does not train a model or overwrite completed research runs.

The builder checks that referenced Python/JavaScript symbols exist, all diagram
functions have explanations, all local links resolve, and all HTML IDs are unique.
`--check` also detects a stale output or input manifest. These checks do not prove
the prose is accurate: review changed explanations against the implementation.

The source reference is the most recent commit affecting the documented code.
Individual source hashes identify the exact working files used. The read-only
check preserves the build's recorded revision context, so a documentation-only
commit does not falsely make the guide stale; actual input changes are detected
through regenerated content and hashes. Embedded source excerpts are refreshed
on every build. No application behavior is changed by this documentation.
