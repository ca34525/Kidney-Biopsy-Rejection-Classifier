"""Start the API with the model and examples selected when this image was built."""

import json
import os
from pathlib import Path

import uvicorn


def main():
    runtime = Path(__file__).resolve().parent / "runtime"
    bundle = json.loads((runtime / "bundle.json").read_text(encoding="utf-8"))
    if bundle["bundle_version"] != 1:
        raise ValueError("Unsupported container bundle version.")
    os.environ["KIDNEY_BIOPSY_PROJECT_ROOT"] = str(runtime)
    os.environ["KIDNEY_BIOPSY_RESULTS_DIR"] = bundle["run_dir"]
    os.environ["KIDNEY_BIOPSY_DEMO_DIR"] = bundle["demo_dir"]
    uvicorn.run("kidney_biopsy.api:app", host="0.0.0.0", port=8000, access_log=False)


if __name__ == "__main__":
    main()
