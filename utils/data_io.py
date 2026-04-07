"""File loading and export helpers."""

from __future__ import annotations

import io
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


def _normalize_json_payload(file_bytes: bytes) -> pd.DataFrame:
    """Load JSON content into a dataframe with a few common shapes supported."""
    try:
        payload = json.loads(file_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("JSON files must be UTF-8 encoded.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("The JSON file could not be parsed.") from exc

    if isinstance(payload, list):
        return pd.json_normalize(payload)

    if isinstance(payload, dict):
        list_like_keys = [key for key, value in payload.items() if isinstance(value, list)]
        if list_like_keys:
            return pd.json_normalize(payload[list_like_keys[0]])
        return pd.json_normalize(payload)

    raise ValueError("Unsupported JSON structure. Use a list of records or a JSON object.")


@st.cache_data(show_spinner=False)
def load_uploaded_dataset(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    """Load an uploaded CSV, XLSX, or JSON file into a dataframe."""
    suffix = Path(file_name).suffix.lower()

    try:
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif suffix == ".xlsx":
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        elif suffix == ".json":
            df = _normalize_json_payload(file_bytes)
        else:
            raise ValueError("Unsupported file type. Please upload CSV, XLSX, or JSON.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Unable to load {file_name}. Please check the file format and contents.") from exc

    if df.empty:
        raise ValueError("The uploaded dataset is empty.")

    df.columns = [str(column) for column in df.columns]
    return df


@st.cache_data(show_spinner=False)
def load_sample_dataset(sample_path: str) -> pd.DataFrame:
    """Load a sample CSV dataset."""
    path = Path(sample_path)
    if not path.exists():
        raise ValueError(f"Sample dataset not found: {path.name}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise ValueError(f"Unable to load sample dataset {path.name}.") from exc

    if df.empty:
        raise ValueError(f"Sample dataset {path.name} is empty.")

    df.columns = [str(column) for column in df.columns]
    return df


def list_sample_datasets(sample_dir: str) -> list[Path]:
    """Return available sample dataset paths."""
    directory = Path(sample_dir)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.csv"))


def sanitize_filename(name: str) -> str:
    """Create a filesystem-safe base filename."""
    clean_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return clean_name or "dataset"


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize a dataframe to an Excel workbook."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="cleaned_data")
    buffer.seek(0)
    return buffer.read()


def json_to_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize a JSON-safe dictionary to bytes."""
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def text_to_bytes(text: str) -> bytes:
    """Encode plain text or markdown for download."""
    return text.encode("utf-8")
