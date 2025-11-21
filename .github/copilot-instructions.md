# PrePol - AI Coding Assistant Instructions

PrePol is a **predictive policing system** using RandomForest ML to forecast crime probabilities in H3 hexagonal cells. Three-tier architecture: Jupyter notebooks (ML pipeline) → Flask API (predictions) → React frontend (visualization).

## System Architecture & Data Flow

```
ML Pipeline (Jupyter):           Production Stack:
RDO CSVs → H3 cells              React (Vite) ←→ Flask API ←→ MongoDB Atlas
         → Panel data                      ↓              ↓
         → RandomForest                 Vercel        Render (512MB)
         → Model (.joblib)
```

**Critical separation**: Notebooks train models offline; backend serves predictions using pre-trained model. Never mix training code with API code.

## Critical Patterns & Conventions

### 1. Data Source Toggle (CRITICAL)
**`api/server.py` line ~30**: `USE_MONGODB = True/False` switches data source:
- **MongoDB mode** (`True`): Queries MongoDB Atlas dynamically, lazy-loads date ranges. Required for production (Render = 512MB RAM).
- **Parquet mode** (`False`): Loads full panel into memory (~2GB). Use only for local development.

When editing predictions: MongoDB uses `get_panel_data_mongodb(start, end)`; parquet filters `df_panel` in memory.

### 2. H3 Spatial System
- **Resolution 9** (~0.1 km²) in `prepol/config.py:H3_RES`. Use `prepol/helpers.py` wrappers:
  ```python
  to_h3(lat, lon, res)        # Handles h3 v3/v4 API differences
  h3_neighbors(cell, k=1)     # K-ring for spatial features
  h3_to_boundary(cell)        # → polygon coords for GeoJSON
  ```
- Why wrappers: h3 library changed API (geo_to_h3 → latlng_to_cell). Helpers ensure compatibility.

### 3. Column Normalization (Mandatory)
**Always** call first on RDO data:
```python
df = helpers.normalize_df_columns_to_upper(df)  # Strip + uppercase
```
Canonical: `LATITUDE`, `LONGITUDE`, `DATA_OCORRENCIA_BO`, `HORA_OCORRENCIA_BO`. Code breaks without this.

### 4. Probability Calculation
Backend converts daily crime counts using **Poisson distribution**:
```python
# api/server.py:count_to_probability()
def count_to_probability(daily_avg_count):
    """P(≥1 crime on a day) = 1 - e^(-λ)"""
    return 1 - np.exp(-daily_avg_count)
```
Not sigmoid! This is scientifically correct for count data. Frontend displays as %.

### 5. MongoDB Schema (Production)
Collection: `prepol_db.panel_data`
```javascript
{
  h3_cell: "89a6c462c3fffff",
  date: ISODate("2016-12-01"),
  y: 2,  // Actual crime count
  features: {
    y_norm: 0.5, y_lag_1: 1, y_lag_2: 0, y_lag_3: 1,
    y_rol_3: 0.67, y_rol_7: 0.71, y_lag_1_vizinhos: 3
  },
  coords: {lat: -8.05, lon: -34.9},
  time_period: 736329  // Period.ordinal for sklearn
}
```
**Indexes**: Compound `(h3_cell, date)` + single `date`. Query <500ms depends on these.

### 6. Temporal Integrity
- **No shuffle** in train/test splits—breaks temporal dependencies
- **Period serialization**: Convert `pd.Period` to `.ordinal` (int) before MongoDB/sklearn
- **Lag features**: First N periods per cell have NaN → `fillna(0)` before prediction
- **Date range limits**: Frontend capped at 31 days to prevent OOM on Render

### 7. Panel Data Structure
Complete spatio-temporal grid (all cells × all periods):
- **Zero-inflation**: Missing cell-period = 0 crimes (valid data, not NaN)
- **Features**: `y_norm`, `y_lag_1/2/3`, `y_rol_3/7`, `y_lag_1_vizinhos`, `time_period`
- **Target**: `y` (count), converted to probability in predictions
- Created in `H3Discretization.ipynb` using neighbor lookups + rolling windows

## Development Workflows

### Environment Setup
```powershell
# PowerShell (Windows)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt        # Jupyter dependencies
pip install -r api/requirements.txt    # Flask + ML stack
```

**Python version constraint**: Must use **Python 3.11** for Render. scikit-learn 1.3.0 incompatible with 3.13 (Cython errors).

### Notebook Execution Order
Each notebook expects `notebooks/` as cwd:
```python
project_root = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(project_root))
```

1. **Analysis&Treatment.ipynb** — Clean RDO CSVs → `rdo_optimized.csv`
2. **H3Discretization.ipynb** — Spatial aggregation → `PrePol_panel_export.parquet`
3. **ModelTraining.ipynb** — Train RandomForest → `rf_crime_model_*.joblib`
4. **ModelUsage.ipynb** — Predictions + Folium maps

Alternative: **PrePolFullPipeline.ipynb** (end-to-end, harder to debug).

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
- Local: Set `USE_MONGODB = False` in `server.py`, ensure parquet in `panels/`
- Production-like: Set `USE_MONGODB = True`, export `$env:MONGODB_URI = "..."`

Health check: `http://localhost:5000/api/health` (shows data source + status)

### MongoDB Migration (One-time Setup)
```powershell
# 1. Create reduced panel (Q4 2016 for 512MB RAM)
python scripts/create_reduced_panel.py

# 2. Migrate to MongoDB Atlas
python scripts/migrate_to_mongodb.py
# (Prompts for URI, inserts ~911K docs, creates indexes)

# 3. Verify health (8 diagnostic tests)
$env:MONGODB_URI = "mongodb+srv://..."
python check_mongodb_health.py
```

**After migration**: Update `api/server.py` to `USE_MONGODB = True` and deploy.

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
❌ **Deploying parquet mode** → Exceeds Render 512MB limit (use MongoDB)  
❌ **Python 3.13** → scikit-learn 1.3.0 build fails (use 3.11)  
❌ **Raw h3 calls** → API differences break across versions (use helpers)  
❌ **Individual Folium polygons** → 10x slower than GeoJSON (vectorize)  
❌ **Assuming NaN = missing** → In panel data, 0 crimes ≠ NaN (both valid)

## Key Files Reference

- **`prepol/config.py`** — All constants (H3_RES=9, TIME_FREQ='D', paths)
- **`prepol/helpers.py`** — Reusable utilities (h3, datetime, CSV loading)
- **`api/server.py`** — Flask endpoints (`/api/health`, `/api/metadata`, `/api/predict`)
- **`front/src/CrimeMap.jsx`** — Leaflet map with GeoJSON rendering + stats panel
- **`model/rf_crime_model_meta_*.json`** — Model performance (R²=0.91)
- **`scripts/migrate_to_mongodb.py`** — Parquet → MongoDB migration
- **`check_mongodb_health.py`** — 8-test diagnostic suite

## Testing & Validation

No formal test suite. Validation checklist:

**Notebooks**:
1. Panel completeness: `len(unique_cells) × len(periods) == len(df_panel)`
2. No NaN in features after `fillna(0)`
3. Temporal split: `train_end < test_start`
4. Visual inspection: Folium maps in `H3Discretization.ipynb`

**Backend**:
1. Health check: `/api/health` shows `model_loaded: true`
2. Date range: `/api/metadata` returns correct min/max
3. Prediction: POST to `/api/predict` with 7-day range
4. CORS: Frontend can fetch from different origin

**MongoDB**:
```powershell
python check_mongodb_health.py  # 8 diagnostic tests
```
Checks: connection, schema, indexes, query <500ms, integrity, model compat.

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
