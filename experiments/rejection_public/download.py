"""Download or verify the two public GSE212160 inputs listed in data/manifest.json."""
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_local_data import local_path, records, verify


def main() -> None:
    for item in records():
        path = local_path(item["file"])
        if path.exists():
            verify(path, item)
            action = "Verified cached"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = local_path(item["file"] + ".part")
            request = Request(item["url"], headers={"User-Agent": "kidney-biopsy-research/0.1"})
            try:
                with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
                    shutil.copyfileobj(response, output)
                verify(temporary, item)
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
            action = "Downloaded and verified"
        print(f"{action} {item['file']} ({item['bytes']:,} bytes)")
    print(f"Verification completed {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
