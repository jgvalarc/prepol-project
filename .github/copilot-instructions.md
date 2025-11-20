# PrePol Project - AI Agent Instructions

## Project Overview
PrePol is a **predictive policing system** using machine learning to estimate crime probability across spatially discretized areas (H3 hexagons) over time. The core workflow converts raw Brazilian police reports (RDO files) into spatio-temporal crime forecasts using RandomForest regression.

**Key Insight**: Crime is not random - it follows spatio-temporal patterns. PrePol captures these through H3 spatial discretization + temporal aggregation + lag features.

## Architecture & Data Flow

```
RDO CSVs (2010-2017) → Analysis&Treatment.ipynb → rdo_optimized.csv
                                                          ↓
                                            H3Discretization.ipynb
                                                          ↓
                                     PrePol_panel_export.parquet
                                     (cell × time_period × features)
                                                          ↓
                                            ModelTraining.ipynb
                                                          ↓
                                     rf_crime_model_*.joblib + metadata
                                                          ↓
                                            ModelUsage.ipynb → predictions
```

### Core Components
- **`prepol/`**: Shared utilities module
  - `config.py`: Paths, column names, H3 resolution (9), time frequency ('D'=daily)
  - `helpers.py`: H3 wrappers, datetime parsing, CSV loading with normalization
- **`notebooks/`**: Jupyter-based pipeline (execute in order)
- **`model/`**: Trained RandomForest artifacts (joblib + JSON metadata)
- **Data directories** (gitignored):
  - `prepol_data/raw/`: RDO_1.csv, RDO_2.csv, RDO_3.csv
  - `prepol_data/clean/`: Cleaned/optimized datasets
  - `prepol_out/`: Panel data, predictions, models

## Critical Patterns & Conventions

### 1. H3 Spatial Discretization
- **Resolution 9** (~0.1 km² hexagons) defined in `config.H3_RES`
- Use `helpers.to_h3(lat, lon, res)` - handles multiple h3 library versions (geo_to_h3 vs latlng_to_cell)
- Neighbor features via `helpers.h3_neighbors(cell, k=1)` for spatial autocorrelation

### 2. Column Normalization
**Always** uppercase and strip column names:
```python
df = helpers.normalize_df_columns_to_upper(df)
```
Canonical columns: `LATITUDE`, `LONGITUDE`, `DATA_OCORRENCIA_BO`, `HORA_OCORRENCIA_BO`

### 3. DateTime Handling
Combine date + time columns with timezone awareness:
```python
time_delta = helpers._parse_time_to_timedelta(df[config.COL_TIME])
df['datetime'] = helpers._combine_date_time(
    df[config.COL_DATETIME], time_delta, tz=config.DEFAULT_TZ
)
```
Default timezone: `America/Recife`

### 4. Panel Data Structure
Complete spatio-temporal grid (all H3 cells × all time periods):
- **Zero-filling**: Missing cell-period combinations = 0 crimes (not NaN)
- **Lag features**: `y_lag_1`, `y_lag_2`, `y_lag_3` (temporal)
- **Rolling averages**: `y_rol_3`, `y_rol_7` (smoothed history)
- **Spatial neighbors**: `y_lag_1_vizinhos` (neighboring cells' crime counts)
- **Target variable**: `y` (crime count), `y_norm` (z-score normalized per cell)

### 5. Model Training
- **Temporal split**: Train on early periods, test on later (no shuffle!)
- **Features**: All lag/rolling/neighbor features + `time_period` (ordinal)
- **NaN handling**: Fill with 0 (typical for panel data with zero-inflated counts)
- **Export**: Model as `.joblib`, metadata as `.json` with timestamp suffix

### 6. File I/O Best Practices
- CSV engine: Use `helpers.choose_csv_engine()` → prefers pyarrow, fallback to python
- Parquet preferred for panel data (preserves dtypes)
- CSV separator: `;` (semicolon) for exports
- Timestamps in filenames: `%Y%m%d_%H%M%S` format

### 7. Probability Conversion (Predictions)
Convert predicted crime counts to probabilities using sigmoid:
```python
def count_to_probability(count, k=0.5):
    """Sigmoid: higher counts → higher probability (0-1 range)
    k controls sensitivity (0.5 default for counts 0-5)"""
    return 1 / (1 + np.exp(-k * count))

df['crime_probability'] = df['y_pred'].apply(lambda x: count_to_probability(x, k=0.5))
```
Alternative: Normalize by max: `df['probability'] = df['y_pred'] / df['y_pred'].max()`  
Use sigmoid for interpretable probabilities; normalize for relative comparison.

## Development Workflows

### Environment Setup
```powershell
# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies (add to requirements.txt if missing)
pip install pandas numpy h3 scikit-learn joblib geopandas folium pyarrow
```

### Notebook Execution Order
1. **Analysis&Treatment.ipynb** - Clean raw RDO files → `rdo_optimized.csv`
2. **H3Discretization.ipynb** - Spatial aggregation → `PrePol_panel_export.parquet`
3. **ModelTraining.ipynb** - Train RandomForest → `rf_crime_model_*.joblib`
4. **ModelUsage.ipynb** - Load model, make predictions → `prepol_predictions_*.csv`

Alternative: **PrePolFullPipeline.ipynb** - End-to-end in single notebook (longer, harder to debug)

**Important**: Each notebook expects to be run from the `notebooks/` directory and uses:
```python
project_root = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(project_root))
```
This pattern ensures `prepol` module imports work correctly.

### Adding Features
When adding new features to the panel:
1. Compute in `H3Discretization.ipynb` after basic aggregation
2. Add to `export_cols` list before CSV/Parquet export
3. Update `ModelTraining.ipynb` to include in `feature_cols`
4. Retrain model with new features

### Debugging Missing Data
- Check for `(0, 0)` or NaN coordinates → filtered out pre-H3
- H3 conversion failures → logged but dropped (see "Failed conversions" output)
- Missing lag features → Expected for first N periods per cell (fillna(0))

## Project-Specific Notes

### Why H3 Resolution 9?
Balances spatial granularity (~0.1 km²) with computational feasibility. For ~1 km² cells, use resolution 6. Changing requires full re-run from H3Discretization onward.

### Why Weekly Aggregation?
`TIME_FREQ = 'D'` (daily) but actual aggregation is configurable. Weekly (`'W'`) provides:
- Enough observations per cell-period for modeling
- Reduces zero-inflation (more cells have ≥1 crime per week)
- Captures weekly crime cycles

### Performance Optimization
- **Neighbor calculation**: Pre-build neighbor map as dict, use lookup instead of repeated h3.k_ring calls
- **Crime lookup**: Convert to dict `{(cell, period): count}` for O(1) access
- **Folium maps**: Use GeoJSON FeatureCollection instead of iterating individual polygons (10x+ faster)
  - Vectorize color/boundary calculations before loop
  - Build single GeoJSON object with all features
  - Use `folium.GeoJson()` instead of multiple `folium.Polygon()` calls
  - Example in `ModelUsage.ipynb` cell starting "Create map with predicted crime probabilities (OPTIMIZED)"
- **Parquet vs CSV**: Parquet loads ~5-10x faster for panel data (preserves dtypes, compression)

### Model Evaluation
Current metrics (from metadata):
- Test R²: 0.91 (excellent)
- Test MAE: 0.018 crimes/period
- Top feature: `y_norm` (84% importance) - normalized historical crime

## Common Pitfalls
❌ Modifying column names after normalization - always use uppercase constants  
❌ Shuffling time series data - breaks temporal dependencies  
❌ Forgetting to localize datetimes to `America/Recife` timezone  
❌ Assuming NaN = no data (in panel, 0 crimes ≠ NaN, both are valid)  
❌ Using raw lat/lon after H3 discretization (spatial unit is H3 cell, not point)

## Key Files to Reference
- `prepol/config.py` - All configurable parameters
- `prepol/helpers.py` - Reusable functions (start here for utilities)
- `notebooks/H3Discretization.ipynb` - Panel structure definition (lines 421-513: Folium map visualization)
- `notebooks/ModelUsage.ipynb` - Sigmoid probability conversion, GeoJSON optimization
- `model/rf_crime_model_meta_*.json` - Model performance baseline
- `PrePol&DatasetReport.md` - Original data documentation (Portuguese)

## Helper Functions Quick Reference
Common utilities from `prepol.helpers`:
- `normalize_df_columns_to_upper(df)` - **Always call first** on new DataFrames
- `carregar_dataset(path, nome, nrows=None)` - Load CSV with normalization
- `to_h3(lat, lon, res)` - Convert coordinates to H3 cell (handles library versions)
- `h3_neighbors(cell, k=1)` - Get k-ring neighbors for spatial features
- `h3_to_geo(cell)` - H3 cell to (lat, lon) centroid
- `h3_to_boundary(cell)` - H3 cell to polygon boundary coords
- `choose_csv_engine()` - Auto-select best CSV engine (pyarrow > python)
- `save_parquet_and_csv(df, parquet_path, csv_path)` - Dual export convenience

## Testing & Validation
No formal test suite yet. Validation approach:
1. Check panel completeness: `len(cells) × len(periods) == len(df_panel)`
2. Verify no NaN in final feature matrix after fillna
3. Temporal split sanity: `train_end < test_start`
4. Map visualization: Use Folium in H3Discretization to visually inspect cell boundaries
5. Model metrics: R² > 0.85 on test set expected
