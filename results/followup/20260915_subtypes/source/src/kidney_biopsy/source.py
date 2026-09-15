"""Public-source readers shared by training and local source-data prediction."""
from __future__ import annotations

import csv
import gzip
import io
from pathlib import Path
import re
import tarfile

import pandas as pd

from .preprocessing import validate_counts


def read_geo_matrix(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        text = stream.read()
    pre, table = text.split("!series_matrix_table_begin", 1)
    rows = [next(csv.reader([line], delimiter="\t")) for line in pre.splitlines() if line.startswith("!Sample_")]
    ids = next(row[1:] for row in rows if row[0] == "!Sample_geo_accession")
    if not ids or len(set(ids)) != len(ids) or any(not ident.strip() for ident in ids):
        raise ValueError("GEO metadata specimen IDs must be present and unique.")
    meta = pd.DataFrame(index=ids)
    for row in rows:
        if len(row) != len(ids) + 1:
            raise ValueError("GEO metadata row does not match the specimen count.")
        if row[0] == "!Sample_characteristics_ch1":
            for ident, value in zip(ids, row[1:]):
                if ": " in value:
                    key, value = value.split(": ", 1)
                    meta.loc[ident, key] = value
        elif row[0] in ("!Sample_title", "!Sample_source_name_ch1"):
            meta[row[0].removeprefix("!Sample_")] = row[1:]
    values = pd.read_csv(io.StringIO(table.split("!series_matrix_table_end")[0].strip()), sep="\t", index_col=0).T
    if not values.index.is_unique or set(values.index) != set(meta.index):
        raise ValueError("GEO expression and metadata specimen IDs differ.")
    if "histology diganosis of rejection" in meta:
        meta["histology_diagnosis"] = meta["histology diganosis of rejection"]
    return values, meta


def read_rcc_archive(path: str | Path, specimen_ids=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read endogenous/housekeeping counts without extracting archive files to disk."""
    records = {}
    batches = {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            ident = Path(member.name).name.split("_")[0]
            if not ident or ident in records:
                raise ValueError("Raw assay archive contains missing or duplicate specimen IDs.")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Cannot read a raw assay archive member.")
            text = gzip.decompress(stream.read()).decode()
            body = text.split("<Code_Summary>")[1].split("</Code_Summary>")[0].strip()
            table = pd.read_csv(io.StringIO(body))
            table = table[table.CodeClass.isin(["Endogenous", "Housekeeping"])]
            if table.Name.isna().any() or table.Name.duplicated().any():
                raise ValueError(f"Raw assay has missing or duplicate targets for {ident}.")
            records[ident] = dict(zip(table.Name, table.Count))
            batches[ident] = dict(re.findall(r"^(Date|CartridgeID|ScannerID),([^\r\n]*)", text, flags=re.M))
    counts = pd.DataFrame.from_dict(records, orient="index")
    if len(counts.columns) != 770:
        raise ValueError("The GSE212160 raw B-HOT panel must contain exactly 770 targets.")
    if specimen_ids is not None:
        index = pd.Index(specimen_ids)
        if not index.is_unique or set(counts.index) != set(index):
            raise ValueError("Raw assay and metadata specimen IDs must match exactly.")
        counts = counts.loc[index]
    counts = validate_counts(counts)
    return counts, pd.DataFrame.from_dict(batches, orient="index").loc[counts.index]
