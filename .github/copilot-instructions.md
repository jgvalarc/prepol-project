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
**`api/server.py` line ~34**: `USE_MONGODB_FORECAST = True/False` switches forecast data source:
- **MongoDB mode** (`True`): Loads latest forecast from MongoDB Atlas `forecast_data` collection. Required for production. Requires `MONGODB_URI` env var.
- **Parquet mode** (`False`): Loads forecast from local `panels/PrepolForecast_XX/*.parquet` file. Use for local development/testing.

**Important**: This is NOT the old panel data toggle - the old `USE_MONGODB` variable is DEPRECATED. The system now serves pre-computed forecasts, not on-demand predictions from panel data.

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
- **Resolution 9** (~0.1 km²) defined in `prepol/config.py:H3_RES` (note: config shows 10, but system uses 9 in practice - verify before changes).
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
- `api/requirements.txt`: Production dependencies (pinned sklearn==1.3.0, numpy<2.0)
- `requirements.txt`: Development/notebook dependencies (flask not included)
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
python server.py

# Terminal 2: Frontend (port 5173)
cd front
npm install  # First time only
npm run dev
```

**Testing data source**:
- Local: Set `USE_MONGODB_FORECAST = False` in `server.py`, ensure parquet in `panels/PrepolForecast_XX/`
- Production-like: Set `USE_MONGODB_FORECAST = True`, export `$env:MONGODB_URI = "..."`

Health check: `http://localhost:5000/api/health` (shows data source + status)

**API Endpoints** (changed from old architecture):
- `/api/health` — Server status + forecast data source
- `/api/metadata` — Forecast period info + statistics (no date selection needed)
- `/api/forecast` — Returns entire pre-computed forecast as GeoJSON (no POST body)

**Common startup issues**:
- "Model not found": Verify `model/rf_crime_model_*.joblib` exists
- "Forecast not found": Check `panels/PrepolForecast_XX/PrepolForecast_XX.parquet` for parquet mode
- "No forecast data in MongoDB": Run `import_forecast_to_mongodb.py` to upload forecasts
- "pymongo not installed": Install with `pip install pymongo` for MongoDB mode
- Port 5000 in use: Kill process or use `$env:PORT = "5001"`

### Forecast Upload to MongoDB (Production Setup)
```powershell
# 1. Generate forecast panel
# Run GenerateWeeklyPrediction.ipynb → exports to panels/PrepolForecast_XX/

# 2. Upload forecast to MongoDB Atlas
cd scripts/mongodb
python import_forecast_to_mongodb.py --list  # List available forecasts
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_02  # Upload specific forecast
python import_forecast_to_mongodb.py  # Upload all forecasts

# 3. Verify forecast in MongoDB
$env:MONGODB_URI = "mongodb+srv://..."
# Check collection: prepol_db.forecast_data
```

**After upload**: Update `api/server.py` to `USE_MONGODB_FORECAST = True` and deploy.

### Deployment (Vercel + Render)
See `DEPLOYMENT.md` for full guide. Key points:

**Render (Backend)**:
- Build: `pip install -r api/requirements.txt`
- Start: `gunicorn --chdir api wsgi:app --timeout 180`
- Env vars: `PYTHON_VERSION=3.11.0`, `MONGODB_URI=mongodb+srv://...`
- Free tier: 512MB RAM, spins down after 15min idle

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
for cell in cells:
    neighbors = h3_neighbors(cell, k=1)
```

**Do** build lookup dict:
```python
# ✅ O(1) lookups
neighbor_map = {cell: set(h3_neighbors(cell, k=1)) for cell in unique_cells}
for cell in cells:
    neighbors = neighbor_map[cell]
```

## Common Pitfalls

❌ **Forgetting normalization** → `df = helpers.normalize_df_columns_to_upper(df)` is mandatory  
❌ **Shuffling time series** → Breaks temporal dependencies (use `shuffle=False`)  
❌ **Wrong timezone** → Must use `America/Recife` for RDO data  
❌ **Deploying parquet mode** → Exceeds Render 512MB limit (use MongoDB forecast mode)  
❌ **Using old panel_data collection** → System now requires forecast_data collection with sparse forecasts  
❌ **Python 3.13** → scikit-learn 1.3.0 build fails (use 3.11)  
❌ **Raw h3 calls** → API differences break across versions (use helpers)  
❌ **Individual Folium polygons** → 10x slower than GeoJSON (vectorize)  
❌ **Assuming NaN = missing** → In panel data, 0 crimes ≠ NaN (both valid)  
❌ **Missing venv activation** → Import errors, wrong Python version (activate `.\venv\Scripts\Activate.ps1`)  
❌ **Running notebooks from wrong directory** → Path errors (must run from `notebooks/` or handle `project_root`)

## Key Files Reference

- **`prepol/config.py`** — All constants (H3_RES=10, TIME_FREQ='W', paths)
- **`prepol/helpers.py`** — Reusable utilities (h3, datetime, CSV loading)
- **`api/server.py`** — Flask endpoints (`/api/health`, `/api/metadata`, `/api/forecast`)
- **`front/src/CrimeMap.jsx`** — Leaflet map with GeoJSON rendering + stats panel + crime type layers
- **`model/rf_crime_model_meta_*.json`** — Model performance (R²=0.93)
- **`notebooks/GenerateWeeklyPrediction.ipynb`** — Generate weekly forecast panels
- **`scripts/mongodb/import_forecast_to_mongodb.py`** — Upload forecasts to MongoDB
- **`panels/PrepolForecast_XX/`** — Pre-computed forecast panels (parquet + metadata)
- **`front/vite.config.js`** — Vite build config (proxy settings for dev)
- **`api/wsgi.py`** — Gunicorn entry point (imports app from server.py)

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
