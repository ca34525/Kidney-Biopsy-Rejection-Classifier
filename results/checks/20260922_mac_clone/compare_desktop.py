"""Compare this clone's reruns with committed desktop evidence, without rewriting it.

Run from the project root. Missing original predictions cannot be reconstructed
from hashes; matching aggregate metrics is reported separately from score identity.
"""

import argparse
import csv
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "results/reproduction/20260922_mac_clone"
TOLERANCE = 1e-12
IGNORED_TIMINGS = {"seconds", "fit_seconds"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def compare_values(old, new, location="", differences=None):
    if differences is None:
        differences = []
    if isinstance(old, dict) and isinstance(new, dict):
        assert set(old) == set(new), f"Keys differ: {location}"
        for key in old:
            if key not in IGNORED_TIMINGS:
                compare_values(old[key], new[key], f"{location}/{key}", differences)
    elif isinstance(old, list) and isinstance(new, list):
        assert len(old) == len(new), f"Lengths differ: {location}"
        for index, (a, b) in enumerate(zip(old, new, strict=True)):
            compare_values(a, b, f"{location}/{index}", differences)
    elif old != new:
        # CSV numeric cells are strings. Empty cells, labels, booleans and
        # integer JSON counts must agree exactly; finite floats use atol only.
        if old is None or new is None or isinstance(old, bool) or isinstance(new, bool):
            raise AssertionError(f"Value differs: {location}: {old!r} != {new!r}")
        if isinstance(old, int) and isinstance(new, int):
            raise AssertionError(f"Count differs: {location}: {old} != {new}")
        try:
            a, b = float(old), float(new)
        except (TypeError, ValueError) as error:
            raise AssertionError(f"Text differs: {location}: {old!r} != {new!r}") from error
        assert math.isfinite(a) and math.isfinite(b), f"Nonfinite value: {location}"
        difference = abs(a - b)
        differences.append({"field": location, "absolute_difference": difference})
    return differences


def compare_file(old, new):
    if old.suffix == ".csv":
        with old.open(newline="", encoding="utf-8-sig") as stream:
            a = list(csv.DictReader(stream))
        with new.open(newline="", encoding="utf-8-sig") as stream:
            b = list(csv.DictReader(stream))
    else:
        a, b = read_json(old), read_json(new)
    differences = []
    record = {
        "reference": old.relative_to(ROOT).as_posix(),
        "current": new.relative_to(ROOT).as_posix(),
        "reference_sha256": digest(old),
        "current_sha256": digest(new),
    }
    try:
        compare_values(a, b, differences=differences)
        record["passed"] = all(item["absolute_difference"] <= TOLERANCE for item in differences)
    except AssertionError as error:
        record.update(passed=False, error=str(error))
    record["max_absolute_numeric_difference"] = max(
        (item["absolute_difference"] for item in differences), default=0
    )
    record["numeric_differences"] = differences
    return record


def hash_comparison(path, record):
    data = path.read_bytes()
    lf = data.replace(b"\r\n", b"\n")
    variants = {"unchanged_bytes": data, "LF": lf, "CRLF": lf.replace(b"\n", b"\r\n")}
    match = next(
        (name for name, value in variants.items()
         if hashlib.sha256(value).hexdigest() == record["sha256"]),
        None,
    )
    return {
        "reference_file": record["file"],
        "current_file": path.relative_to(ROOT).as_posix(),
        "reference_sha256": record["sha256"],
        "current_sha256": digest(path),
        "matching_serialization": match,
        "content_proven_identical": match is not None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = ROOT / args.output
    if output.exists():
        parser.error("Choose a new output path; preserve previous evidence.")
    comparisons, hash_checks, integrity, frozen = [], [], [], []
    current_manifest = read_json(RUN / "run_manifest.json")
    for reference_name in ("baseline", "20260915_shared"):
        reference = ROOT / "results/reproduction" / reference_name
        manifest = read_json(reference / "run_manifest.json")
        for name in ("biopsy_results.json", "biopsy_screen.csv"):
            comparisons.append(compare_file(reference / name, RUN / name))
        for path in sorted(reference.glob("*_frozen.json")):
            a, b = read_json(path), read_json(RUN / path.name)
            fields = ["target", "selected_model", "threshold", "features", "train_n", "screen_n", "test_n"]
            if "schema" in a:
                fields.append("schema")
            differences = compare_values({k: a[k] for k in fields}, {k: b[k] for k in fields})
            frozen.append({
                "reference": path.relative_to(ROOT).as_posix(),
                "fields_compared": fields,
                "selected_model": b["selected_model"],
                "reference_threshold": a["threshold"],
                "current_threshold": b["threshold"],
                "passed": all(item["absolute_difference"] <= TOLERANCE for item in differences),
                "numeric_differences": differences,
            })
        present, missing = 0, 0
        for item in manifest["artifacts"]:
            old_path = ROOT / item["file"]
            if old_path.exists():
                assert digest(old_path) == item["sha256"], f"Changed reference: {old_path}"
                assert old_path.stat().st_size == item["bytes"]
                present += 1
            else:
                missing += 1
            name = old_path.name
            if name in {"biopsy_split.csv", "raw_batch_identifiers.csv"} or name.endswith(
                ("_test_predictions.csv", "_screen_predictions.csv")
            ):
                hash_checks.append(hash_comparison(RUN / name, item))
        integrity.append({"reference_run": reference_name, "existing_artifacts_verified": present,
                          "artifacts_absent_from_clone": missing,
                          "python_matches": manifest["python"] == current_manifest["python"],
                          "modeling_dependencies_match": manifest["dependencies"] == current_manifest["dependencies"],
                          "seeds_match": manifest["seeds"] == current_manifest["seeds"]})
    for item in current_manifest["artifacts"]:
        assert digest(ROOT / item["file"]) == item["sha256"], f"Changed new artifact: {item['file']}"
    for reference, current in [
        ("results/analysis/20260915_baseline", "results/analysis/20260922_mac_clone"),
        ("results/analysis/20260915_viral", "results/analysis/20260922_mac_clone_viral"),
        ("results/followup/20260915_subtypes", "results/followup/20260922_mac_clone_subtypes"),
        ("results/followup/20260917_stability", "results/followup/20260922_mac_clone_stability"),
    ]:
        for old in sorted((ROOT / reference).glob("*.csv")):
            comparisons.append(compare_file(old, ROOT / current / old.name))
    for reference, current in [
        ("results/analysis/20260915_baseline/model_metrics.json", "results/analysis/20260922_mac_clone/model_metrics.json"),
        ("results/followup/20260917_stability/summary.json", "results/followup/20260922_mac_clone_stability/summary.json"),
        ("results/reproduction/20260915_shared/data_audit.json", "results/reproduction/20260922_mac_clone/data_audit.json"),
        ("results/reproduction/20260915_shared/configuration.json", "results/reproduction/20260922_mac_clone/configuration.json"),
    ]:
        comparisons.append(compare_file(ROOT / reference, ROOT / current))
    raw = read_json(ROOT / "data/manifest.json")
    for item in raw:
        assert digest(ROOT / item["file"]) == item["sha256"]
        assert (ROOT / item["file"]).stat().st_size == item["bytes"]
    passed = all(item["passed"] for item in comparisons + frozen)
    result = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "python": platform.python_version(),
        "script_sha256": digest(Path(__file__)),
        "source_commit": "ccbaf31abcaa049be946efe849b7d2f243378976",
        "current_manifest_sha256": digest(RUN / "run_manifest.json"),
        "raw_inputs_sha256_verified": raw,
        "aggregate_comparisons_passed": passed,
        "absolute_tolerance": TOLERANCE, "relative_tolerance": 0,
        "excluded_timing_fields": sorted(IGNORED_TIMINGS),
        "aggregate_comparisons": comparisons, "frozen_choices": frozen,
        "original_evidence_integrity": integrity,
        "new_run_artifacts_verified": len(current_manifest["artifacts"]),
        "split_and_prediction_hash_comparisons": hash_checks,
        "limits": [
            "Original specimen-level prediction tables and fitted models were not committed.",
            "A matching hash after only newline conversion proves text content identity. A mismatching hash cannot quantify score differences or prove identical individual flags.",
            "Aggregate agreement within 1e-12 is distinct from an original-versus-current per-specimen score comparison.",
            "Fresh model binary hashes and run identifiers are not expected to match the desktop artifacts.",
        ],
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"aggregate_comparisons_passed": passed, "files_compared": len(comparisons),
                      "failed": [c for c in comparisons if not c["passed"]],
                      "hash_matches": sum(c["content_proven_identical"] for c in hash_checks),
                      "hash_comparisons": len(hash_checks)}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
