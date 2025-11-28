"""Helper utilities used by multiple notebooks in the PrePol project.
Keep functions pure and well-documented so notebooks can import them.
"""
from pathlib import Path
import os
import pandas as pd
import numpy as np
import json
from datetime import timedelta

try:
    import h3  # type: ignore
except Exception:
    h3 = None

from . import config


def normalize_df_columns_to_upper(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame column names: strip and uppercase."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip().str.upper()
    return df


def _to_float_coord(series: pd.Series) -> pd.Series:
    """Convert coordinate-like series to float (handles comma decimals)."""
    if series.dtype == object:
        series = series.str.replace(",", ".", regex=False).str.strip()
    return pd.to_numeric(series, errors="coerce")


def _parse_time_to_timedelta(s: pd.Series) -> pd.Series:
    """Parse 'HH:MM[:SS]' strings into pandas.Timedelta series."""
    s = s.astype(str).str.strip()
    t1 = pd.to_datetime(s, errors="coerce", format="%H:%M:%S")
    mask_na = t1.isna()
    if mask_na.any():
        t2 = pd.to_datetime(s[mask_na], errors="coerce", format="%H:%M")
        t1 = t1.where(~mask_na, t2)
    td_seconds = (
        t1.dt.hour.fillna(0).astype(int) * 3600
        + t1.dt.minute.fillna(0).astype(int) * 60
        + t1.dt.second.fillna(0).astype(int)
    )
    return pd.to_timedelta(td_seconds, unit="s")


def _combine_date_time(date_series: pd.Series, time_delta: pd.Series, tz: str = None) -> pd.Series:
    """Combine date series and timedelta series into timezone-aware datetimes.
    If tz is provided, localize naive datetimes to tz.
    """
    date_series = pd.to_datetime(date_series, errors="coerce")
    base = date_series.dt.normalize()
    default_td = pd.to_timedelta(12, unit="h")
    td = time_delta.fillna(default_td)
    dt_naive = base + td
    if tz is not None:
        try:
            return dt_naive.dt.tz_localize(tz)
        except Exception:
            try:
                return dt_naive.dt.tz_convert(tz)
            except Exception:
                return dt_naive
    return dt_naive


def categorize_hour_interval(hour: float) -> str:
    """Categorize hour (0-23) into 4-hour intervals.
    
    Parameters
    ----------
    hour : float
        Hour of the day (0-23). NaN values return 'DESCONHECIDO'.
    
    Returns
    -------
    str
        Hour interval category: '00-04h', '04-08h', '08-12h', '12-16h', '16-20h', '20-24h', or 'DESCONHECIDO'
    
    Examples
    --------
    >>> categorize_hour_interval(2.5)
    '00-04h'
    >>> categorize_hour_interval(15.0)
    '12-16h'
    >>> categorize_hour_interval(np.nan)
    'DESCONHECIDO'
    """
    if pd.isna(hour):
        return 'DESCONHECIDO'
    
    hour = int(hour)
    
    for start, end, label in config.HOUR_INTERVALS:
        if start <= hour < end:
            return label
    
    # Handle edge case (hour >= 24 or < 0)
    return 'DESCONHECIDO'


def extract_hour_from_time_string(time_str: str) -> float:
    """Extract hour from time string in format 'HHMM' (e.g., '1910' -> 19.0).
    
    Parameters
    ----------
    time_str : str
        Time string, often in format like '1910.0' (7:10 PM) or '0830' (8:30 AM)
    
    Returns
    -------
    float
        Hour (0-23) or NaN if parsing fails
    
    Examples
    --------
    >>> extract_hour_from_time_string('1910.0')
    19.0
    >>> extract_hour_from_time_string('0830')
    8.0
    >>> extract_hour_from_time_string('invalid')
    nan
    """
    try:
        # Remove .0 suffix if present
        time_str = str(time_str).replace('.0', '').strip()
        
        if len(time_str) == 0 or time_str == 'nan':
            return np.nan
        
        # Parse as integer and extract hour
        time_int = int(float(time_str))
        hour = time_int // 100  # e.g., 1910 // 100 = 19
        
        if 0 <= hour <= 23:
            return float(hour)
        else:
            return np.nan
    except (ValueError, TypeError):
        return np.nan


def choose_csv_engine() -> str:
    """Choose read_csv engine; prefer 'pyarrow' if available else 'python'."""
    try:
        import pyarrow  # type: ignore
        return "pyarrow"
    except Exception:
        return "python"


def carregar_dataset(path: Path, nome: str, nrows: int = None) -> pd.DataFrame:
    """Read CSV with normalization and safe defaults. Returns normalized DataFrame or raises.

    Parameters
    - path: Path to CSV
    - nome: label for logging
    - nrows: optional number of rows to read for sampling
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
    engine = choose_csv_engine()
    read_kwargs = {"encoding": "utf-8", "engine": engine}
    if engine == "python":
        read_kwargs["on_bad_lines"] = "warn"
    if nrows is not None:
        read_kwargs["nrows"] = nrows
    df = pd.read_csv(p, **read_kwargs)
    df = normalize_df_columns_to_upper(df)
    return df


# H3 wrappers
def to_h3(lat: float, lon: float, res: int) -> str:
    """Return H3 index for lat/lon using available h3 bindings."""
    if h3 is None:
        raise RuntimeError("h3 library is not installed")
    # try common function names
    if hasattr(h3, "geo_to_h3"):
        return h3.geo_to_h3(lat, lon, res)
    if hasattr(h3, "latlng_to_cell"):
        return h3.latlng_to_cell(lat, lon, res)
    # fallback — attempt to call h3.api
    try:
        return h3.latlng_to_cell(lat, lon, res)
    except Exception as e:
        raise


def h3_neighbors(cell: str, k: int = 1) -> list:
    """Return neighbor cells (k-ring)."""
    if h3 is None:
        return []
    if hasattr(h3, "k_ring"):
        return list(h3.k_ring(cell, k))
    if hasattr(h3, "grid_disk"):
        return list(h3.grid_disk(cell, k))
    return []


def h3_to_geo(cell: str) -> tuple:
    """Convert H3 cell to (lat, lon) centroid coordinates."""
    if h3 is None:
        raise RuntimeError("h3 library is not installed")
    if hasattr(h3, "h3_to_geo"):
        return h3.h3_to_geo(cell)
    if hasattr(h3, "cell_to_latlng"):
        return h3.cell_to_latlng(cell)
    # Fallback attempt
    try:
        return h3.cell_to_latlng(cell)
    except Exception as e:
        raise


def h3_to_boundary(cell: str) -> list:
    """Convert H3 cell to boundary polygon coordinates as list of (lat, lon) tuples."""
    if h3 is None:
        raise RuntimeError("h3 library is not installed")
    if hasattr(h3, "h3_to_geo_boundary"):
        return h3.h3_to_geo_boundary(cell)
    if hasattr(h3, "cell_to_boundary"):
        boundary = h3.cell_to_boundary(cell)
        # Convert to list of tuples if needed
        return [(lat, lon) for lat, lon in boundary]
    # Fallback attempt
    try:
        boundary = h3.cell_to_boundary(cell)
        return [(lat, lon) for lat, lon in boundary]
    except Exception as e:
        raise


def ensure_output_dir():
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_parquet_and_csv(df: pd.DataFrame, parquet_path: Path, csv_path: Path, csv_sep: str = ";") -> None:
    ensure_output_dir()
    try:
        df.to_parquet(parquet_path, index=False)
    except Exception:
        pass
    try:
        df.to_csv(csv_path, index=False, sep=csv_sep, encoding="utf-8")
    except Exception:
        pass


def write_json(obj, path: Path) -> None:
    ensure_output_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
