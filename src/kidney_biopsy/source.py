"""Public-source readers shared by training and local source-data prediction."""

from __future__ import annotations

import csv
import gzip
import io
import re
import tarfile
from pathlib import Path

import pandas as pd

from .preprocessing import validate_counts


def read_geo_matrix(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the deposited expression table and its specimen metadata."""
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        text = stream.read()
    metadata_text, expression_text = text.split("!series_matrix_table_begin", 1)
    rows = [
        next(csv.reader([line], delimiter="\t"))
        for line in metadata_text.splitlines()
        if line.startswith("!Sample_")
    ]
    accession_rows = [row[1:] for row in rows if row[0] == "!Sample_geo_accession"]
    if len(accession_rows) != 1:
        raise ValueError("GEO metadata must contain exactly one specimen accession row.")
    specimen_ids = accession_rows[0]
    if (
        not specimen_ids
        or len(set(specimen_ids)) != len(specimen_ids)
        or any(not specimen_id.strip() for specimen_id in specimen_ids)
    ):
        raise ValueError("GEO metadata specimen IDs must be present and unique.")

    metadata = pd.DataFrame(index=specimen_ids)
    seen_fields = set()
    for row in rows:
        if len(row) != len(specimen_ids) + 1:
            raise ValueError("GEO metadata row does not match the specimen count.")
        if row[0] == "!Sample_characteristics_ch1":
            for specimen_id, value in zip(specimen_ids, row[1:]):
                if ": " in value:
                    field_name, value = value.split(": ", 1)
                    if (specimen_id, field_name) in seen_fields:
                        raise ValueError(
                            f"Duplicate GEO metadata field {field_name!r} for {specimen_id}."
                        )
                    seen_fields.add((specimen_id, field_name))
                    metadata.loc[specimen_id, field_name] = value
        elif row[0] in ("!Sample_title", "!Sample_source_name_ch1"):
            field_name = row[0].removeprefix("!Sample_")
            if field_name in metadata:
                raise ValueError(f"Duplicate GEO metadata field {field_name!r}.")
            seen_fields.update((specimen_id, field_name) for specimen_id in specimen_ids)
            metadata[field_name] = row[1:]

    expression_table = expression_text.split("!series_matrix_table_end")[0].strip()
    expression = pd.read_csv(io.StringIO(expression_table), sep="\t", index_col=0).T
    if not expression.index.is_unique or set(expression.index) != set(metadata.index):
        raise ValueError("GEO expression and metadata specimen IDs differ.")
    if "histology diganosis of rejection" in metadata:
        metadata["histology_diagnosis"] = metadata["histology diganosis of rejection"]
    return expression, metadata


def read_rcc_archive(path: str | Path, specimen_ids=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read endogenous/housekeeping counts without extracting archive files to disk."""
    specimen_counts = {}
    specimen_batches = {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            specimen_id = Path(member.name).name.split("_")[0]
            if not specimen_id or specimen_id in specimen_counts:
                raise ValueError("Raw assay archive contains missing or duplicate specimen IDs.")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Cannot read a raw assay archive member.")

            text = gzip.decompress(stream.read()).decode()
            code_summary = text.split("<Code_Summary>")[1].split("</Code_Summary>")[0].strip()
            table = pd.read_csv(io.StringIO(code_summary))
            table = table[table.CodeClass.isin(["Endogenous", "Housekeeping"])]
            if table.Name.isna().any() or table.Name.duplicated().any():
                raise ValueError(f"Raw assay has missing or duplicate targets for {specimen_id}.")
            specimen_counts[specimen_id] = dict(zip(table.Name, table.Count))
            specimen_batches[specimen_id] = dict(
                re.findall(r"^(Date|CartridgeID|ScannerID),([^\r\n]*)", text, flags=re.M)
            )

    counts = pd.DataFrame.from_dict(specimen_counts, orient="index")
    if len(counts.columns) != 770:
        raise ValueError("The GSE212160 raw B-HOT panel must contain exactly 770 targets.")
    if specimen_ids is not None:
        requested_order = pd.Index(specimen_ids)
        if not requested_order.is_unique or set(counts.index) != set(requested_order):
            raise ValueError("Raw assay and metadata specimen IDs must match exactly.")
        counts = counts.loc[requested_order]
    counts = validate_counts(counts)
    batches = pd.DataFrame.from_dict(specimen_batches, orient="index").loc[counts.index]
    return counts, batches
