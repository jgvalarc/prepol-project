from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
# Data is stored in notebooks folder (historical structure)
DATA_DIR = BASE_DIR / "notebooks" / "prepol_data" / "raw"
OUTPUT_DIR = BASE_DIR / "notebooks" / "prepol_out"

# RDO files (expected names)
RDO_FILES = {
    "RDO_1": DATA_DIR / "RDO_1.csv",
    "RDO_2": DATA_DIR / "RDO_2.csv",
    "RDO_3": DATA_DIR / "RDO_3.csv",
}

# Defaults for processing
TIME_FREQ = "D"  # 'D' daily, 'W' weekly, 'M' monthly
H3_RES = 10
DEFAULT_TZ = "America/Recife"
RANDOM_STATE = 42

# Canonical column names
COL_LAT = "LATITUDE"
COL_LON = "LONGITUDE"
COL_DATETIME = "DATA_OCORRENCIA_BO"
COL_TIME = "HORA_OCORRENCIA_BO"
COL_CRIMETYPE = "RUBRICA"

# Hour interval categories (4-hour blocks)
HOUR_INTERVALS = [
    (0, 4, "00-04h"),
    (4, 8, "04-08h"),
    (8, 12, "08-12h"),
    (12, 16, "12-16h"),
    (16, 20, "16-20h"),
    (20, 24, "20-24h")
]

# Export filenames
RDO_CLEAN_PARQUET = OUTPUT_DIR / "rdo_clean.parquet"
RDO_CLEAN_CSV = OUTPUT_DIR / "rdo_clean.csv"
DF_PANEL_PARQUET = OUTPUT_DIR / "df_panel.parquet"

# Model naming helper
MODEL_PREFIX = "rf_crime_model"
