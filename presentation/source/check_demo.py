"""Verify the browser artifact and actual service example without fitting a model."""

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
    args = parser.parse_args()
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
        assert hashlib.sha256(source).hexdigest() == record["sha256"], record["path"]
        assert source.decode("utf-8") == record["raw"], record["path"]
    status, served = request(args.url, "/presentation/engineering_demo.html")
    assert status == 200 and served.decode("utf-8") == html
    status, model_body = request(args.url, "/model")
    model = json.loads(model_body)
    assert status == 200 and model["model_version"] == snapshot["model_version"]
    assert model["threshold"] == snapshot["threshold"]
    status, valid_body = request(args.url, "/predict", snapshot["valid_csv"].encode("utf-8"))
    assert status == 200 and json.loads(valid_body) == snapshot["valid_response"]
    _, invalid_csv = request(args.url, "/demo/examples/missing-target")
    invalid_status, invalid_body = request(args.url, "/predict", invalid_csv)
    assert invalid_status == 422 and json.loads(invalid_body) == snapshot["invalid_response"]
    assert "predictions" not in json.loads(invalid_body)
    for route in ["/", "/assets/app.js", "/assets/style.css", "/presentation/speaking_script.html"]:
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
            "all_embedded_reference_bytes_and_hashes_match_sources",
            "self_contained_static_content_without_external_asset_dependencies",
            "three_stop_navigation_structure_and_unique_ids",
            "real_http_valid_response_matches_saved_response",
            "real_http_missing_target_rejected_without_predictions",
            "expected_model_version_and_threshold",
            "existing_application_and_assets_available",
            "14_slides_and_three_browser_stops_in_script_order_total_1200_seconds",
        ],
        "embedded_reference_count": len(payload["references"]),
        "model_version": model["model_version"],
        "changed_retained_slide_renders": changed,
        "prior_render_comparison": "passed"
        if changed is not None
        else "unavailable: private prior revision is absent",
        "scope": "Presentation integration and one public example. Does not rerun model comparison, the historical 345-specimen check, hosted CI or container validation.",
    }
    (ROOT / args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
