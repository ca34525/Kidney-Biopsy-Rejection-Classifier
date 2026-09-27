"""Verify the browser artifact and actual service example without fitting a model."""

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check_reference(source, record):
    """Allow Git's LF/CRLF conversion while still rejecting changed source text."""
    raw = record["raw"].encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == record["sha256"], record["path"]
    assert source.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n"), record["path"]


def check_response(actual, expected):
    """Keep identities and flags exact; allow only rounding-level score differences."""
    assert actual.keys() == expected.keys()
    assert len(actual["predictions"]) == len(expected["predictions"])
    for key in actual.keys() - {"predictions"}:
        assert actual[key] == expected[key], key
    for found, saved in zip(actual["predictions"], expected["predictions"], strict=True):
        assert found.keys() == saved.keys()
        for key in found:
            if key in {"rejection_score", "threshold"}:
                assert math.isclose(found[key], saved[key], rel_tol=0, abs_tol=1e-12), key
            else:
                assert found[key] == saved[key], key


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.script_data = ""
        self.in_data = False
        self.external_assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script" and attrs.get("id") == "demo-data":
            self.in_data = True
        if tag in ("script", "img", "iframe") and attrs.get("src"):
            self.external_assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.external_assets.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_data = False

    def handle_data(self, data):
        if self.in_data:
            self.script_data += data


def request(base, route, content=None):
    req = urllib.request.Request(
        base + route, data=content, headers={"Content-Type": "text/csv"} if content else {}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766")
    parser.add_argument("--output", default="build/presentation/engineering-demo-checks.json")
    parser.add_argument(
        "--offline", action="store_true", help="Check tracked content without a server."
    )
    parser.add_argument(
        "--run-dir", help="Verify a different live run against its local frozen model."
    )
    args = parser.parse_args()
    if args.offline and args.run_dir:
        parser.error("--run-dir requires a live service; omit --offline.")
    html = (ROOT / "presentation/engineering_demo.html").read_text(encoding="utf-8")
    page = Page()
    page.feed(html)
    assert len(page.ids) == len(set(page.ids)), "Duplicate HTML ids"
    assert not page.external_assets, page.external_assets
    for name in [
        "evidence",
        "specimen",
        "engineering",
        "errors-view",
        "splits-view",
        "shared-view",
        "interface-view",
        "checks-view",
        "csv-preview",
        "application-link",
    ]:
        assert name in page.ids, name
    payload = json.loads(page.script_data)
    snapshot = payload["snapshot"]
    for record in payload["references"].values():
        source = (ROOT / record["path"]).read_bytes()
        check_reference(source, record)
    model = None
    if not args.offline:
        expected_response = snapshot["valid_response"]
        expected_version = snapshot["model_version"]
        expected_threshold = snapshot["threshold"]
        if args.run_dir:
            import io

            from kidney_biopsy.prediction import load_predictor
            from kidney_biopsy.preprocessing import read_counts_csv

            predictor = load_predictor(ROOT, args.run_dir)
            counts = read_counts_csv(io.StringIO(snapshot["valid_csv"]), predictor.schema)
            expected_response = {
                **expected_response,
                "predictions": predictor.predict(counts).to_dict(orient="records"),
            }
            expected_version = predictor.model_version
            expected_threshold = predictor.threshold
        status, served = request(args.url, "/presentation/engineering_demo.html")
        assert status == 200 and served.decode("utf-8") == html
        status, model_body = request(args.url, "/model")
        model = json.loads(model_body)
        assert status == 200 and model["model_version"] == expected_version
        assert math.isclose(model["threshold"], expected_threshold, rel_tol=0, abs_tol=1e-12)
        status, valid_body = request(args.url, "/predict", snapshot["valid_csv"].encode("utf-8"))
        assert status == 200
        check_response(json.loads(valid_body), expected_response)
        invalid_csv_status, invalid_csv = request(args.url, "/demo/examples/missing-target")
        assert invalid_csv_status == 200
        invalid_status, invalid_body = request(args.url, "/predict", invalid_csv)
        assert invalid_status == 422 and json.loads(invalid_body) == snapshot["invalid_response"]
        assert "predictions" not in json.loads(invalid_body)
        for route in [
            "/",
            "/assets/app.js",
            "/assets/style.css",
            "/presentation/speaking_script.html",
        ]:
            assert request(args.url, route)[0] == 200, route
    data = json.loads(
        (ROOT / "presentation/source/speaking_script.json").read_text(encoding="utf-8")
    )
    assert len(data["slides"]) == 14
    stops = data["browser_demo"]["stops"]
    assert len(stops) == 3 and data["browser_demo"]["after_slide"] == 13
    assert sum(item["seconds"] for item in data["slides"] + stops) == 1200
    script = (ROOT / "presentation/speaking_script.html").read_text(encoding="utf-8")
    for anchor in ["slide-13", "demo-evidence", "demo-specimen", "demo-engineering", "slide-14"]:
        assert f'id="{anchor}"' in script, anchor
    assert (
        script.index('id="slide-13"')
        < script.index('id="demo-evidence"')
        < script.index('id="demo-specimen"')
        < script.index('id="demo-engineering"')
        < script.index('id="slide-14"')
    )
    assert "\n+  --data-binary" not in html
    baseline = ROOT / "build/presentation/before-engineering-demo-20260922/presentation/slides"
    changed = None
    if baseline.exists():
        changed = [
            n
            for n in range(1, 13)
            if (ROOT / f"presentation/slides/slide-{n:02}.png").read_bytes()
            != (baseline / f"slide-{n:02}.png").read_bytes()
        ]
        assert changed == [4, 12], changed
    result = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "successful": True,
        "checks": [
            "embedded_reference_hashes_verified_and_sources_match_allowing_lf_crlf",
            "self_contained_static_content_without_external_asset_dependencies",
            "three_stop_navigation_structure_and_unique_ids",
            "14_slides_and_three_browser_stops_in_script_order_total_1200_seconds",
        ]
        + (
            []
            if args.offline
            else [
                "real_http_valid_response_matches_local_model"
                if args.run_dir
                else "real_http_valid_response_matches_saved_response",
                "real_http_missing_target_rejected_without_predictions",
                "expected_model_version_and_threshold",
                "existing_application_and_assets_available",
            ]
        ),
        "embedded_reference_count": len(payload["references"]),
        "model_version": model["model_version"] if model else None,
        "saved_example_model_version": snapshot["model_version"],
        "run_dir_override": args.run_dir,
        "offline": args.offline,
        "numeric_tolerance": 1e-12,
        "changed_retained_slide_renders": changed,
        "prior_render_comparison": "passed"
        if changed is not None
        else "unavailable: private prior revision is absent",
        "scope": "Static presentation checks only."
        if args.offline
        else "Presentation integration and one public example. Does not rerun model comparison, the historical 345-specimen check, hosted CI or container validation.",
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
