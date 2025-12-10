# PrePol - AI Coding Assistant Instructions

PrePol is a **predictive policing system** using RandomForest ML to forecast crime probabilities in H3 hexagonal cells. 

## 🔄 Architecture Shift (Critical Understanding)

**OLD ARCHITECTURE (Deprecated):**
- User selects date range in frontend → Backend generates predictions on-demand → Returns GeoJSON

**NEW ARCHITECTURE (Current):**
- Offline: `GenerateWeeklyPrediction.ipynb` creates forecast panels → Exports to `panels/PrepolForecast_XX/`
- Production: Forecasts uploaded to MongoDB `forecast_data` collection
- Frontend: Fetches pre-computed forecasts from API (no date selection)

## System Architecture & Data Flow

```
OFFLINE (Jupyter):                    PRODUCTION (Online):
RDO CSVs → H3 cells                   React (Vite) ←→ Flask API ←→ MongoDB Atlas
         → Panel data                          ↓              ↓          ↓
         → RandomForest                     Vercel        Render    forecast_data
         → Trained model                                             collection
         ↓
GenerateWeeklyPrediction.ipynb
         ↓
PrepolForecast_XX/ folders
  • forecast.parquet (sparse, one row per H3 cell)
  • metadata.json
         ↓
import_forecast_to_mongodb.py
         ↓
MongoDB (forecast_data collection)
```

**Key principle**: Predictions are **view-ready** - no computation happens at request time.

## Critical Patterns & Conventions

### 1. Forecast Data Source Toggle (CRITICAL)
**`api/server.py` line 34**: `USE_MONGODB_FORECAST = True/False` switches forecast data source:
- **MongoDB mode** (`True`): Loads latest forecast from MongoDB Atlas `forecast_data` collection. Required for production. Requires `MONGODB_URI` env var and `pymongo>=4.6.0` installed.
- **Parquet mode** (`False`, **current default**): Loads forecast from local `panels/PrepolForecast_03/*.parquet` file. Use for local development/testing.

**Important**: This is NOT the old panel data toggle - the old `USE_MONGODB` variable is DEPRECATED. The system now serves pre-computed forecasts, not on-demand predictions from panel data. **MongoDB mode requires pymongo** which is installed via `api/requirements.txt` but missing from root `requirements.txt`.

### 2. Forecast Panel Structure (NEW)
Forecasts are **sparse** (one row per H3 cell, not time series):
```python
# Forecast columns (from GenerateWeeklyPrediction.ipynb)
{
  'h3_cell': str,              # H3 cell identifier
  'period': datetime,          # Forecast period timestamp
  'predicted_daily_avg': float, # Daily average crime count
  'predicted_total': float,    # Total weekly prediction
  'crime_probability': float,  # P(≥1 crime/day) via Poisson
  'lat': float, 'lon': float,  # Cell centroid
  'n_days': int,               # Forecast duration (7 for weekly)
  'crime_type': str            # Most probable crime type (if multi-type model)
}
```

Folders: `panels/PrepolForecast_XX/` with `PrepolForecast_XX.parquet` + `_metadata.json`

### 3. H3 Spatial System
- **Resolution MISMATCH**: `prepol/config.py` defines `H3_RES = 10` (~0.015 km²) but production forecasts use **resolution 9** (~0.1 km²). See `panels/PrepolForecast_02/_metadata.json: "h3_resolution": 9` and `GenerateWeeklyPrediction.ipynb`. This discrepancy must be reconciled before model retraining.
- Use `prepol/helpers.py` wrappers exclusively:
  ```python
  to_h3(lat, lon, res)        # Handles h3 v3/v4 API differences (geo_to_h3 vs latlng_to_cell)
  h3_neighbors(cell, k=1)     # K-ring for spatial features (k_ring vs grid_disk)
  h3_to_geo(cell)             # Cell → (lat, lon) centroid
  h3_to_boundary(cell)        # → list[(lat, lon)] for GeoJSON polygons
  ```
- **Never call h3 library directly** - API changed between versions (v3: `geo_to_h3`, v4: `latlng_to_cell`). Helpers ensure compatibility.

### 4. Column Normalization (Mandatory)
**Always** call first on RDO data - system crashes without this:
```python
df = helpers.normalize_df_columns_to_upper(df)  # Strip whitespace + uppercase
```
Canonical columns (must match exactly):
- `LATITUDE`, `LONGITUDE` — Coordinates (converted from comma decimals in raw data)
- `DATA_OCORRENCIA_BO`, `HORA_OCORRENCIA_BO` — Date/time (parsed to `America/Recife` timezone)
- `RUBRICA`, `DESCR_TIPO_BO` — Crime classification

Normalization handles: whitespace stripping, comma→dot decimal conversion, inconsistent casing from RDO exports.

### 5. Probability Calculation
Backend converts daily crime counts using **Poisson distribution**:
```python
# api/server.py:count_to_probability()
def count_to_probability(daily_avg_count):
    """P(≥1 crime on a day) = 1 - e^(-λ)"""
    return 1 - np.exp(-daily_avg_count)
```
Not sigmoid! This is scientifically correct for count data. Frontend displays as %.

### 6. MongoDB Schema (Production)
**New schema** - `prepol_db.forecast_data` collection (replaces old panel_data):
```javascript
{
  h3_cell: "89a6c462c3fffff",
  forecast_week: 2,                    // Week of year
  forecast_year: 2025,
  period: ISODate("2025-01-08"),       // Forecast period start
  predicted_daily_avg: 0.0039,         // Daily average crime count
  predicted_total: 0.0274,             // Total weekly prediction
  crime_probability: 0.0035,           // P(≥1 crime/day) via Poisson
  n_days: 7,                           // Forecast duration
  coords: {lat: -8.05, lon: -34.9},
  forecast_generated: ISODate("..."),
  model_info: {...},
  crime_type: "Furto",                 // Most probable crime type (optional)
  is_forecast: true
}
```
**Indexes**: `(h3_cell, forecast_week, forecast_year)` compound + singles on `forecast_week`, `crime_probability` (desc), `predicted_total` (desc).

**Old panel_data schema** (deprecated for predictions, kept for historical reference):
```javascript
{
  h3_cell: "89a6c462c3fffff",
  date: ISODate("2016-12-01"),
  y: 2,  // Actual crime count
  features: {...},
  coords: {lat: -8.05, lon: -34.9},
  time_period: 736329
}
```

### 7. Temporal Integrity
- **No shuffle** in train/test splits—breaks temporal dependencies
- **Period serialization**: Convert `pd.Period` to `.ordinal` (int) before MongoDB/sklearn
- **Lag features**: First N periods per cell have NaN → `fillna(0)` before prediction
- **Date range limits**: Frontend capped at 31 days to prevent OOM on Render

### 8. Panel Data Structure
Complete spatio-temporal grid (all cells × all periods):
- **Zero-inflation**: Missing cell-period = 0 crimes (valid data, not NaN). System creates complete grid: `len(unique_cells) × len(periods) == len(df_panel)` must be true.
- **Features**: `y_norm`, `y_lag_1/2/3`, `y_rol_3/7`, `y_lag_1_vizinhos`, `time_period`
- **Target**: `y` (count), converted to probability in predictions
- Created in `H3Discretization.ipynb` using neighbor lookups + rolling windows
- **Validation**: First lag periods per cell have NaN by design → `fillna(0)` before model training/prediction

## Development Workflows

### Environment Setup
```powershell
# PowerShell (Windows)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt        # Jupyter dependencies
pip install -r api/requirements.txt    # Flask + ML stack
```

**Python version constraint**: Must use **Python 3.11** for Render. scikit-learn 1.3.0 incompatible with 3.13 (Cython errors).

**Dependency notes**:
- `api/requirements.txt`: Production dependencies (pinned sklearn==1.3.0, numpy<2.0, **includes pymongo, gunicorn, python-dotenv**)
- `requirements.txt`: Root-level dependencies (simpler, **lacks pymongo, gunicorn, python-dotenv** - matches api/requirements.txt otherwise)
- **Critical difference**: `pymongo` is in `api/requirements.txt` but NOT in root `requirements.txt`. For MongoDB features in notebooks, install manually: `pip install pymongo>=4.6.0`
- Both need `pyarrow` for parquet I/O, `h3` for spatial operations

### Notebook Execution Order
Each notebook expects `notebooks/` as cwd:
```python
project_root = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(project_root))
```

**Training Pipeline (one-time or when retraining):**
1. **Analysis&Treatment.ipynb** — Clean RDO CSVs → `rdo_optimized.csv`
2. **H3Discretization.ipynb** — Spatial aggregation → `PrePol_panel_export.parquet`
3. **ModelTraining.ipynb** — Train RandomForest → `rf_crime_model_*.joblib`

**Forecast Generation Pipeline (weekly/periodic):**
4. **GenerateWeeklyPrediction.ipynb** — Load model + panel → Generate forecasts → Export to `panels/PrepolForecast_XX/`

**Legacy/Testing:**
- **ModelUsage.ipynb** — Predictions + Folium maps (interactive testing)
- **PrePolFullPipeline.ipynb** — End-to-end (harder to debug)

**Notebook best practices**:
- Run cells sequentially (execution count shows order)
- Validate panel completeness: `len(unique_cells) × len(periods) == len(df_panel)`
- Visual sanity checks: Use Folium maps in `H3Discretization.ipynb` to verify spatial aggregation
### Running Backend Locally
```powershell
# Terminal 1: Backend (port 5000)
cd api
python server.py  # Or: flask run

# Terminal 2: Frontend (port 5173)
cd front
npm install  # First time only
npm run dev
```

**Testing data source**:
- Local (default): `USE_MONGODB_FORECAST = False` in `server.py` line 34, ensure parquet in `panels/PrepolForecast_03/` (note: hardcoded to PrepolForecast_03, not dynamic)
- Production-like: Set `USE_MONGODB_FORECAST = True`, export `$env:MONGODB_URI = "mongodb+srv://..."`, ensure pymongo installed

Health check: `http://localhost:5000/api/health` (shows data source + status + forecast metadata)

**API Endpoints** (changed from old architecture):
- `GET /api/health` — Server status + forecast data source (MongoDB/parquet) + forecast metadata summary
- `GET /api/metadata` — Forecast period info + statistics (no date selection needed)
- `GET /api/forecast` — Returns entire pre-computed forecast as GeoJSON (no POST body, no pagination)
- `GET /api/model-info` — Model metadata (R², MAE, feature importance, training date)
- `/api/health` — Server status + forecast data source
**Common startup issues**:
- "Model not found": Verify `model/rf_crime_model_20251125_1448.joblib` exists (file with timestamp in name)
- "Forecast not found": Check `panels/PrepolForecast_03/PrepolForecast_03.parquet` exists (hardcoded path in `server.py:load_forecast_data_parquet()`)
- "No forecast data in MongoDB": Run `scripts/mongodb/import_forecast_to_mongodb.py` to upload forecasts
- "pymongo not installed": Install with `pip install pymongo>=4.6.0` (included in `api/requirements.txt` but not root)
- Port 5000 in use: Kill process with `Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process` or change port
- "MONGODB_URI not set": Export via `$env:MONGODB_URI = "mongodb+srv://..."` (required for MongoDB mode)olForecast_XX.parquet` for parquet mode
### Forecast Upload to MongoDB (Production Setup)
```powershell
# 1. Generate forecast panel
# Run notebooks/GenerateWeeklyPrediction.ipynb → exports to panels/PrepolForecast_XX/

# 2. Upload forecast to MongoDB Atlas
cd scripts\mongodb  # Note: Windows path separator
$env:MONGODB_URI = "mongodb+srv://..."  # Set before running
python import_forecast_to_mongodb.py --list  # List available forecasts
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_02  # Upload specific forecast
python import_forecast_to_mongodb.py  # Upload all forecasts (no args)

# 3. Verify forecast in MongoDB (optional)
python MongoControl.py  # Interactive terminal UI for MongoDB operations
# Or check collection directly: prepol_db.forecast_data

# 4. Health check via API
curl http://localhost:5000/api/health  # Should show MongoDB source + forecast_id
```

**After upload**: Update `api/server.py` line 34 to `USE_MONGODB_FORECAST = True` and deploy to Render.
### Deployment (Vercel + Render)
**Note**: `DEPLOYMENT.md` file does NOT exist - deployment info reconstructed from code.

**Render (Backend)**:
- Build command: `pip install -r api/requirements.txt`
- Start command: `gunicorn --chdir api wsgi:app --timeout 180` (see `api/wsgi.py` - imports `app` from `server.py`)
- Env vars required: 
  - `PYTHON_VERSION=3.11.0` (scikit-learn 1.3.0 incompatible with 3.13)
  - `MONGODB_URI=mongodb+srv://...` (if using MongoDB mode)
- Free tier limits: 512MB RAM, spins down after 15min idle (cold start ~30s)
- **Critical**: Set `USE_MONGODB_FORECAST = True` in `server.py` before deploying (parquet files exceed memory limit)

**Vercel (Frontend)**:
- Root directory: `front/`
- Framework preset: Vite
- Build command: `npm run build` (default)
- Output directory: `dist/` (default)
- Env vars: `VITE_API_URL=https://prepol-api.onrender.com` (build-time substitution)
- File: `front/vercel.json` exists (check for routing config)

**Alternative local deployment**:
- `Procfile` exists at root (Heroku-style process file) - contains `web: gunicorn --chdir api wsgi:app`
- `start-backend.ps1` exists (PowerShell script for local backend startup)

**Vercel (Frontend)**:
- Root: `front/`, Framework: Vite
- Build: `npm run build`, Output: `dist/`
- Env var: `VITE_API_URL=https://prepol-api.onrender.com`

## Performance Patterns

### Folium Map Optimization (10x speedup)
**Don’t** iterate polygons:
```python
# ❌ Slow (individual features)
for cell in cells:
    boundary = h3_to_boundary(cell)
    folium.Polygon(boundary, color=...).add_to(map)
```

**Do** use GeoJSON FeatureCollection:
```python
# ✅ Fast (single GeoJSON object)
features = [
    {
        'type': 'Feature',
        'geometry': {'type': 'Polygon', 'coordinates': [...]},
        'properties': {'probability': 0.75, ...}
    }
    for cell in cells
]
geojson = {'type': 'FeatureCollection', 'features': features}
folium.GeoJson(geojson, style_function=...).add_to(map)
```
See `ModelUsage.ipynb` "OPTIMIZED" cell for implementation.

### Data I/O
- **Parquet over CSV**: 5-10x faster load, preserves dtypes, compression
- **CSV engine**: `helpers.choose_csv_engine()` → pyarrow (fast) or python (fallback)
- **Timestamps**: `%Y%m%d_%H%M%S` format for model/prediction filenames

### Neighbor Pre-computation
**Don’t** call `h3_neighbors()` in loops:
```python
# ❌ O(n) lookups per cell
❌ **Forgetting normalization** → `df = helpers.normalize_df_columns_to_upper(df)` is mandatory first step for RDO data  
❌ **Shuffling time series** → Breaks temporal dependencies (use `shuffle=False` in train_test_split)  
❌ **Wrong timezone** → Must use `America/Recife` for RDO data (not UTC)  
❌ **Deploying parquet mode** → Exceeds Render 512MB limit (use MongoDB forecast mode: `USE_MONGODB_FORECAST = True`)  
❌ **Using old panel_data collection** → System now requires `forecast_data` collection with sparse forecasts  
❌ **Python 3.13** → scikit-learn 1.3.0 build fails with Cython errors (use 3.11 for Render compatibility)  
❌ **Raw h3 calls** → API differences between v3/v4 break code (`geo_to_h3` vs `latlng_to_cell`) - use helpers only  
❌ **Individual Folium polygons** → 10x slower than GeoJSON FeatureCollection (vectorize with single GeoJSON object)  
❌ **Assuming NaN = missing** → In panel data, 0 crimes ≠ NaN (both are valid; NaN only in first lag periods)  
❌ **Missing venv activation** → Import errors, wrong Python version (activate with `.\venv\Scripts\Activate.ps1` on Windows)  
❌ **Running notebooks from wrong directory** → Path errors (must run from `notebooks/` or handle `project_root` via `Path.cwd()`)  
❌ **H3 resolution mismatch** → `config.py` says 10, forecasts use 9 - reconcile before retraining  
❌ **Missing pymongo in root** → `requirements.txt` lacks pymongo (only in `api/requirements.txt`) - install manually for notebooks  
❌ **Hardcoded forecast path** → `server.py` hardcoded to `PrepolForecast_03` - update manually when new forecasts generated  
❌ **No .env files in repo** → Must create `.env.development` and `.env.production` locally (not committed to git)
## Key Files Reference

### Core Configuration
- **`prepol/config.py`** — All constants (H3_RES=10 but forecasts use 9!, TIME_FREQ='W', paths, timezone)
- **`prepol/helpers.py`** — Reusable utilities (h3 wrappers, datetime parsing, CSV loading, column normalization)

### Backend API
- **`api/server.py`** — Flask app with endpoints (491 lines):
  - Line 34: `USE_MONGODB_FORECAST` toggle
  - Line 61: `count_to_probability()` - Poisson conversion
  - Line 101: `load_forecast_data_parquet()` - local forecast loader (hardcoded to PrepolForecast_03)
  - Line 150: `load_forecast_data_mongodb()` - MongoDB forecast loader
- **`api/wsgi.py`** — Gunicorn entry point (imports `app` from `server.py`)
- **`api/requirements.txt`** — Production dependencies (11 packages including pymongo, gunicorn)

### Frontend
- **`front/src/CrimeMap.jsx`** — Main map component (416 lines):
  - GeoJSON rendering with crime type layers
  - Interactive layer control (LayersControl.Overlay)
  - Statistics panel (bottom-right overlay)
  - Popup with prediction intervals and error margins
- **`front/vite.config.js`** — Minimal Vite config (8 lines, no proxy)
- **`front/vercel.json`** — Vercel deployment config
- **`front/package.json`** — Frontend dependencies (React 18, MUI, Leaflet)

### Machine Learning
- **`model/rf_crime_model_20251125_1448.joblib`** — Trained RandomForest model (timestamped)
- **`model/rf_crime_model_meta_20251125_1448.json`** — Model metadata (R²=0.93, MAE=0.0039)

### Data Processing Notebooks
- **`notebooks/Analysis&Treatment.ipynb`** — RDO cleaning (step 1)
- **`notebooks/H3Discretization.ipynb`** — Spatial aggregation (step 2)
- **`notebooks/ModelTraining.ipynb`** — Train RandomForest (step 3)
- **`notebooks/GenerateWeeklyPrediction.ipynb`** — Generate forecasts (step 4) - uses H3 resolution 9!
- **`notebooks/ModelUsage.ipynb`** — Interactive testing with Folium maps

### Forecast Data
- **`panels/PrepolForecast_02/`** — Forecast panel #2 (week 2, 1970 - metadata artifact)
  - `PrepolForecast_02.parquet` — Sparse forecast (51,577 cells)
  - `PrepolForecast_02_metadata.json` — Forecast metadata (h3_resolution: 9)
- **`panels/PrepolForecast_03/`** — Forecast panel #3 (current default in server.py)

### MongoDB Scripts
- **`scripts/mongodb/import_forecast_to_mongodb.py`** — Upload forecasts to MongoDB (456 lines)
- **`scripts/mongodb/MongoControl.py`** — Interactive MongoDB terminal UI
- **`scripts/mongodb/README.md`** — MongoDB operations documentation (264 lines)

### Deployment
- **`Procfile`** — Heroku-style process file (`web: gunicorn --chdir api wsgi:app`)
- **`start-backend.ps1`** — PowerShell script for local backend startup
- **No `DEPLOYMENT.md`** — Deployment info must be inferred from config filesd)  
❌ **Missing venv activation** → Import errors, wrong Python version (activate `.\venv\Scripts\Activate.ps1`)  
## Frontend Architecture

**Tech Stack**: React 18 + Vite + Material-UI + react-leaflet  
**Key patterns**:
- **API URL**: Read from `import.meta.env.VITE_API_URL` (build-time substitution in Vite)
- **Development**: Runs on port 5173 (vite default), NO proxy - uses full API URLs
- **Production**: Uses `VITE_API_URL` env var on Vercel pointing to Render backend
- **Map rendering**: Uses GeoJSON layers with crime type filters (LayersControl.Overlay for each type)
- **Color scheme**: Red gradient based on probability (light red = low, dark red = high) - see `getRedGradient()` in `CrimeMap.jsx`
- **Crime type filtering**: Interactive layer control with toggleable crime types (e.g., "Furto", "Roubo", "All")
- **Error margins**: Displays prediction intervals (68% and 95%) in popups if `weekly_mae` present in data

**Environment variables** (note: .env files NOT in repo):
- `.env.development`: `VITE_API_URL=http://localhost:5000` (create manually)
- `.env.production`: `VITE_API_URL=https://prepol-api.onrender.com` (set in Vercel dashboard)
- **No .env files committed** - must create locally or set in hosting platform

**Build command**: `npm run build` → outputs to `front/dist/`

**Key components**:
- `CrimeMap.jsx`: Main map component (416 lines) - GeoJSON rendering, crime type layers, statistics panel
- `Home.jsx`, `NewHome.jsx`: Landing pages
- `HomeAppBar.jsx`, `MapAppBar.jsx`: Navigation components
- `LoginPage.jsx`, `LoginTab.jsx`: Authentication UI (functionality unclear - no backend auth endpoints found)
## Frontend Architecture

**Tech Stack**: React 18 + Vite + Material-UI + react-leaflet  
**Key patterns**:
- **API URL**: Read from `import.meta.env.VITE_API_URL` (build-time substitution)
- **Development**: Runs on port 5173, proxies API calls to localhost:5000
- **Production**: Uses `VITE_API_URL` env var on Vercel pointing to Render backend
- **Map rendering**: Uses GeoJSON layer for performance (not individual markers)
- **Color scheme**: Red gradient based on probability (light red = low, dark red = high)

**Environment variables**:
- `.env.development`: `VITE_API_URL=http://localhost:5000`
- `.env.production`: `VITE_API_URL=https://prepol-api.onrender.com`

**Build command**: `npm run build` → outputs to `front/dist/`

## Testing & Validation

No formal test suite. Validation checklist:

**Notebooks**:
1. Panel completeness: `len(unique_cells) × len(periods) == len(df_panel)`
2. No NaN in features after `fillna(0)`
3. Temporal split: `train_end < test_start`
4. Visual inspection: Folium maps in `H3Discretization.ipynb`

**Backend**:
1. Health check: `/api/health` shows `model_loaded: true` and `forecast_loaded: true`
2. Metadata: `/api/metadata` returns forecast period info and statistics
3. Forecast: GET `/api/forecast` returns full GeoJSON with pre-computed predictions
4. CORS: Frontend can fetch from different origin

**MongoDB**:
```powershell
python check_mongodb_health.py  # 8 diagnostic tests
```
Checks: connection, schema, indexes, query <500ms, integrity, model compat.

**Frontend**:
```powershell
cd front
npm run build  # Test production build
npm run preview  # Preview production build locally
```
Check browser console for errors, verify map renders correctly.

## Model Information

**Current Performance** (from metadata):
- Test R²: **0.91** (excellent fit)
- Test MAE: **0.018** crimes/period
- Top feature: `y_norm` (84% importance) — normalized historical crime
- Training: 2013-2016 RDO, ~1M records, ~12K H3 cells

**When to retrain**:
- New RDO data (2017+)
- Changing H3 resolution (requires full pipeline)
- Adding features (weather, demographics)
- Performance degrades (R² < 0.85)

Retrain by re-running notebooks 2-3 in sequence.
