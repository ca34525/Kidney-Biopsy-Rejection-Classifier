"""The B-HOT input contract and specimen-level housekeeping normalization.

All invalid batches fail as a whole. Extra targets are rejected when a frozen
schema is supplied, including diagnosis or batch metadata. Reordered targets are
accepted by name. Numeric validation cannot verify the assay's origin.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import numpy as np
import pandas as pd

HOUSEKEEPING_TARGETS = (
    "ABCF1", "G6PD", "GUSB", "NRDE2", "OAZ1", "POLR2A", "PPIA", "SDHA",
    "STK11IP", "TBC1D10B", "TBP", "UBB",
)
SCHEMA_VERSION = "bhot-v1"
PREPROCESSING_VERSION = "log2-housekeeping-v1"
DIAGNOSES = {
    "No Rejection": 0,
    "Antibody-mediated Rejection": 1,
    "T cell-mediated Rejection": 1,
    "Mixed Rejection": 1,
}


@dataclass(frozen=True)
class AssaySchema:
    features: tuple[str, ...]
    schema_version: str = SCHEMA_VERSION
    preprocessing_version: str = PREPROCESSING_VERSION
    housekeeping_targets: tuple[str, ...] = HOUSEKEEPING_TARGETS
    extra_targets: str = "reject"

    def __post_init__(self):
        object.__setattr__(self, "features", tuple(self.features))
        object.__setattr__(self, "housekeeping_targets", tuple(self.housekeeping_targets))
        if (self.schema_version != SCHEMA_VERSION
                or self.preprocessing_version != PREPROCESSING_VERSION):
            raise ValueError("Unsupported assay schema or preprocessing version.")
        if self.housekeeping_targets != HOUSEKEEPING_TARGETS:
            raise ValueError("Schema must use the exact 12 B-HOT housekeeping targets.")
        if self.extra_targets != "reject":
            raise ValueError("Only the reject-extra-targets policy is supported.")
        if not self.features or any(not isinstance(x, str) or not x.strip() for x in self.features):
            raise ValueError("Schema needs nonempty target names.")
        if len(set(self.features)) != len(self.features):
            raise ValueError("Schema contains duplicate assay targets.")
        if set(self.features).intersection(HOUSEKEEPING_TARGETS):
            raise ValueError("Housekeeping targets cannot be model predictors.")

    @property
    def required_targets(self) -> tuple[str, ...]:
        return self.features + self.housekeeping_targets

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "preprocessing_version": self.preprocessing_version,
            "features": list(self.features),
            "housekeeping_targets": list(self.housekeeping_targets),
            "extra_targets": self.extra_targets,
        }

    @classmethod
    def from_dict(cls, value: dict) -> AssaySchema:
        expected = {"features", "schema_version", "preprocessing_version",
                    "housekeeping_targets", "extra_targets"}
        if not isinstance(value, dict) or set(value) != expected:
            raise ValueError("Frozen assay schema is missing required fields or has unknown fields.")
        return cls(**value)


def _validate_identifiers(frame: pd.DataFrame) -> None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("Counts need at least one specimen and one assay target.")
    if not frame.columns.is_unique:
        raise ValueError("Duplicate assay target names are not allowed.")
    if any(not isinstance(name, str) or not name.strip() for name in frame.columns):
        raise ValueError("Assay target names must be present strings.")
    if not frame.index.is_unique or frame.index.isna().any():
        raise ValueError("Specimen IDs must be present and unique.")
    if any(not isinstance(ident, str) or not ident.strip() for ident in frame.index):
        raise ValueError("Specimen IDs must be nonempty strings.")


def validate_counts(counts: pd.DataFrame, schema: AssaySchema | None = None) -> pd.DataFrame:
    """Validate a complete raw-count batch, returning numeric counts unchanged in order."""
    _validate_identifiers(counts)
    required = set(schema.required_targets if schema else HOUSEKEEPING_TARGETS)
    missing = sorted(required.difference(counts.columns))
    if missing:
        raise ValueError(f"Missing required assay targets: {', '.join(missing)}")
    if schema:
        extra = sorted(set(counts.columns).difference(required))
        if extra:
            raise ValueError(f"Unexpected assay targets or metadata columns: {', '.join(extra)}")
    elif not set(counts.columns).difference(HOUSEKEEPING_TARGETS):
        raise ValueError("Counts need at least one non-housekeeping assay target.")
    if any(isinstance(value, (bool, np.bool_, complex, np.complexfloating))
           for value in counts.to_numpy().flat):
        raise ValueError("Raw counts must be real numbers, not booleans or complex values.")
    try:
        numeric = counts.astype(float)
    except (ValueError, TypeError) as error:
        raise ValueError("Raw counts must be numeric and present for every assay target.") from error
    values = numeric.to_numpy()
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Raw counts must be finite, nonnegative, and present for every assay target.")
    return numeric


def normalize_counts(counts: pd.DataFrame, schema: AssaySchema | None = None) -> pd.DataFrame:
    """log2(count + 1) minus mean log2(count + 1) over the 12 housekeeping targets.

There is no fitted state and no cross-specimen information. Without a schema,
training preserves source target order. Prediction uses the frozen feature order.
"""
    numeric = validate_counts(counts, schema)
    log = np.log2(numeric + 1)
    normalized = log.sub(log[list(HOUSEKEEPING_TARGETS)].mean(axis=1), axis=0)
    features = list(schema.features) if schema else [c for c in counts.columns if c not in HOUSEKEEPING_TARGETS]
    return normalized.loc[:, features]


def read_counts_csv(source: str | Path | TextIO, schema: AssaySchema | None = None,
                    *, max_specimens: int = 1000) -> pd.DataFrame:
    """Read a CSV with specimen IDs first; reject duplicate headers before pandas can rename them."""
    if isinstance(source, (str, Path)):
        with Path(source).open(newline="", encoding="utf-8-sig") as stream:
            return read_counts_csv(stream, schema, max_specimens=max_specimens)
    if max_specimens < 1:
        raise ValueError("max_specimens must be positive.")
    try:
        reader = csv.reader(source, strict=True)
        header = next(reader, [])
        if len(header) < 2 or any(not value.strip() for value in header):
            raise ValueError("CSV needs a specimen ID header and named assay targets.")
        if len(set(header)) != len(header):
            raise ValueError("CSV contains duplicate target names or headers.")
        rows = []
        for row in reader:
            if len(row) != len(header):
                raise ValueError("Each CSV row must have the same number of fields as its header.")
            rows.append(row)
            if len(rows) > max_specimens:
                raise ValueError(f"CSV exceeds the {max_specimens}-specimen batch limit.")
    except csv.Error as error:
        raise ValueError("Malformed CSV input.") from error
    if not rows:
        raise ValueError("CSV needs at least one specimen.")
    counts = pd.DataFrame([row[1:] for row in rows], index=[row[0] for row in rows], columns=header[1:])
    counts.index.name = header[0]
    return validate_counts(counts, schema)


def map_diagnoses(diagnoses: pd.Series) -> pd.Series:
    """Map the four documented diagnoses; unknown and missing values are errors."""
    if diagnoses.empty or diagnoses.isna().any():
        raise ValueError("Recorded rejection diagnoses must be present.")
    unknown = sorted(set(diagnoses).difference(DIAGNOSES), key=str)
    if unknown:
        raise ValueError(f"Unexpected recorded rejection diagnoses: {unknown}")
    return diagnoses.map(DIAGNOSES).astype(int)
