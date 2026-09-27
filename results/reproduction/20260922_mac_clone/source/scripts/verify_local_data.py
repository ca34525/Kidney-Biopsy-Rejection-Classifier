"""Verify public input hashes and local paths without third-party packages or Git."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifest.json"


def local_path(relative: str) -> Path:
    """Reject absolute paths, traversal, and filesystem links outside this folder."""
    pure = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or ":" in relative
        or pure.is_absolute()
        or ".." in pure.parts
    ):
        raise ValueError(f"Expected a local relative path: {relative!r}")
    path = ROOT.joinpath(*pure.parts)
    for component in [path, *path.parents]:
        if component == ROOT:
            break
        if component.is_symlink() or component.is_junction():
            raise ValueError(f"Linked input is not a physical local file: {relative}")
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Input escapes the project folder: {relative}")
    return path


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def records() -> list[dict]:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    expected = {"GSE212160_RAW.tar", "GSE212160_series_matrix.txt.gz"}
    if len(entries) != 2 or {PurePosixPath(item["file"]).name for item in entries} != expected:
        raise ValueError("The input manifest must contain exactly the two GSE212160 inputs.")
    for item in entries:
        if item["gse"] != "GSE212160":
            raise ValueError("Only GSE212160 belongs to this project.")
        if not item["url"].startswith(
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE212nnn/GSE212160/"
        ):
            raise ValueError("Unexpected public input URL.")
        local_path(item["file"])
    return entries


def verify(path: Path, item: dict) -> None:
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {item['file']}; run experiments/rejection_public/download.py."
        )
    if path.stat().st_size != item["bytes"]:
        raise ValueError(f"Size mismatch: {item['file']}")
    if sha256(path) != item["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {item['file']}")


def main() -> None:
    entries = records()
    for item in entries:
        verify(local_path(item["file"]), item)
        print(f"Verified {item['file']}: {item['bytes']:,} bytes")
    print(
        f"PASS: {len(entries)} physical local inputs; {sum(item['bytes'] for item in entries):,} bytes."
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
