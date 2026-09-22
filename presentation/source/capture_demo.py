"""Capture actual service responses for the offline presentation example."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from kidney_biopsy.api import create_app

ROOT = Path(__file__).resolve().parents[2]


def main():
    with TestClient(create_app(project_root=ROOT)) as client:
        assert client.get("/health").status_code == 200
        model = client.get("/model").json()
        valid_csv = client.get("/demo/examples/no-rejection")
        invalid_csv = client.get("/demo/examples/missing-target")
        assert valid_csv.status_code == invalid_csv.status_code == 200
        valid = client.post(
            "/predict", content=valid_csv.content, headers={"Content-Type": "text/csv"}
        )
        invalid = client.post(
            "/predict", content=invalid_csv.content, headers={"Content-Type": "text/csv"}
        )
        walkthrough = client.get("/demo/walkthrough/no-rejection")
        assert valid.status_code == walkthrough.status_code == 200
        assert invalid.status_code == 422
        assert "predictions" not in invalid.json()
        snapshot = {
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "method": "Actual local FastAPI application exercised with TestClient; no model fitting.",
            "model_version": model["model_version"],
            "threshold": model["threshold"],
            "valid_csv_sha256": hashlib.sha256(valid_csv.content).hexdigest(),
            "valid_csv": valid_csv.text,
            "valid_response": valid.json(),
            "invalid_status": invalid.status_code,
            "invalid_response": invalid.json(),
            "walkthrough": walkthrough.json(),
        }
    target = ROOT / "presentation/source/demo_snapshot.json"
    target.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": target.relative_to(ROOT).as_posix(),
                "model_version": snapshot["model_version"],
                "valid_status": valid.status_code,
                "invalid_status": invalid.status_code,
            }
        )
    )


if __name__ == "__main__":
    main()
