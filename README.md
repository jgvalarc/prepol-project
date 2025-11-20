# PrePol - Predictive Policing System

A machine learning-based predictive policing system that estimates crime probability across spatially discretized areas over time using Brazilian police report data.

## Overview

PrePol uses spatio-temporal analysis to forecast crime patterns by converting raw police reports (RDO files) into crime forecasts using RandomForest regression. The system discretizes geographic areas into H3 hexagons and analyzes temporal patterns to predict future crime occurrences.

**Key Insight**: Crime follows predictable spatio-temporal patterns. PrePol captures these through H3 spatial discretization, temporal aggregation, and lag features to build accurate forecasts.

## Features

- **H3 Spatial Discretization**: Uses Uber's H3 hexagonal grid system (resolution 9, ~0.1 km² cells) for uniform spatial analysis
- **Temporal Analysis**: Daily/weekly aggregation with configurable time frequencies
- **Feature Engineering**: 
  - Temporal lag features (1-3 periods)
  - Rolling averages (3 and 7 periods)
  - Spatial neighbor features for capturing crime spillover effects
- **RandomForest Model**: Achieves R² > 0.91 on test data
- **Interactive Visualization**: Folium-based maps for exploring predictions

## Project Structure

```
prepol-project/
├── prepol/                          # Core utilities module
│   ├── config.py                   # Configuration (paths, H3 resolution, time frequency)
│   └── helpers.py                  # Reusable functions (H3, datetime, CSV loading)
├── notebooks/                       # Jupyter pipeline (execute in order)
│   ├── Analysis&Treatment.ipynb    # 1. Clean raw RDO files
│   ├── H3Discretization.ipynb      # 2. Spatial aggregation & panel creation
│   ├── ModelTraining.ipynb         # 3. Train RandomForest model
│   ├── ModelUsage.ipynb            # 4. Generate predictions
│   └── PrePolFullPipeline.ipynb    # Alternative: end-to-end pipeline
├── model/                           # Trained models
│   ├── rf_crime_model_*.joblib     # Serialized RandomForest
│   └── rf_crime_model_meta_*.json  # Model metadata & performance metrics
├── prepol_data/                     # Data directories (gitignored)
│   ├── raw/                        # Original RDO CSVs (2010-2017)
│   └── clean/                      # Processed datasets
└── prepol_out/                      # Pipeline outputs (gitignored)
    ├── PrePol_panel_export.parquet # Spatio-temporal panel data
    └── prepol_predictions_*.csv    # Crime forecasts
```

## Data Flow

```
RDO CSVs (2010-2017)
    ↓
Analysis&Treatment.ipynb → rdo_optimized.csv
    ↓
H3Discretization.ipynb → PrePol_panel_export.parquet
    ↓
ModelTraining.ipynb → rf_crime_model_*.joblib
    ↓
ModelUsage.ipynb → predictions
```

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup

```powershell
# Clone the repository
git clone https://github.com/jgvalarc/prepol-project.git
cd prepol-project

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # PowerShell
# or
venv\Scripts\activate.bat    # CMD

# Install dependencies
pip install -r requirements.txt
```

### Required Packages
- pandas
- numpy
- h3
- scikit-learn
- joblib
- geopandas
- folium
- pyarrow

## Usage

### Quick Start

Execute notebooks in sequence:

1. **Data Cleaning**: Run `Analysis&Treatment.ipynb` to clean raw RDO files
2. **Spatial Discretization**: Run `H3Discretization.ipynb` to create H3-based panel data
3. **Model Training**: Run `ModelTraining.ipynb` to train the RandomForest model
4. **Predictions**: Run `ModelUsage.ipynb` to generate crime forecasts

### Panel Data Structure

The system creates a complete spatio-temporal grid with:
- **Spatial units**: H3 hexagonal cells at resolution 9
- **Temporal units**: Configurable periods (daily/weekly)
- **Features**:
  - `y`: Crime count (target variable)
  - `y_norm`: Z-score normalized crime count per cell
  - `y_lag_1`, `y_lag_2`, `y_lag_3`: Temporal lag features
  - `y_rol_3`, `y_rol_7`: Rolling averages
  - `y_lag_1_vizinhos`: Neighboring cells' crime counts
  - `time_period`: Ordinal time index

### Model Training

The RandomForest model uses:
- **Temporal split**: Train on early periods, test on later (no shuffle to preserve temporal order)
- **Features**: All lag/rolling/neighbor features + time_period
- **Performance**: R² > 0.91, MAE < 0.02 crimes/period

## Configuration

Key parameters in `prepol/config.py`:

- `H3_RES = 9`: H3 resolution (~0.1 km² hexagons)
- `TIME_FREQ = 'D'`: Time aggregation frequency (D=daily, W=weekly)
- `DEFAULT_TZ = 'America/Recife'`: Timezone for datetime localization

## Performance Optimization

- **Neighbor calculations**: Pre-built lookup dictionaries for O(1) access
- **Folium maps**: GeoJSON FeatureCollections instead of individual polygons (10x+ faster)
- **Parquet format**: Preferred for panel data (preserves dtypes, faster I/O)

## Current Model Performance

- Test R²: 0.91
- Test MAE: 0.018 crimes/period
- Top feature: `y_norm` (84% importance) - normalized historical crime

## Contributing

This is a research project. For contributions or questions, please contact the repository owner.

## Data Source

The project uses RDO (Registro Digital de Ocorrência) files from Brazilian police reports covering the period 2010-2017. Data is not included in the repository due to size and privacy considerations.

## License

[Add license information]

## Citation

If you use this project in your research, please cite appropriately.

## Contact

Repository maintained by [@jgvalarc](https://github.com/jgvalarc)
