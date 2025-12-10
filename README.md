# PrePol - Predictive Policing System

A machine learning-based predictive policing system that estimates crime probability across spatially discretized areas over time using Brazilian police report data.

## Overview

PrePol is a full-stack predictive policing system that uses machine learning to forecast crime patterns. The system consists of:

- **Offline Pipeline**: Jupyter notebooks process police reports (RDO files) through H3 spatial discretization and RandomForest regression to generate weekly crime forecasts
- **Production API**: Flask backend serves pre-computed forecasts via REST API
- **Web Frontend**: React application visualizes crime probability heatmaps with interactive crime type filtering
- **Database**: MongoDB Atlas stores forecast data for production deployment

**Architecture**: Forecasts are pre-computed offline and stored in MongoDB, enabling fast API responses without on-demand prediction computation.

**Deployment**: Backend on Render, frontend on Vercel, data on MongoDB Atlas.

## Features

### Machine Learning Pipeline
- **H3 Spatial Discretization**: Uber's H3 hexagonal grid (resolution 9, ~0.1 km² cells)
- **Advanced Feature Engineering**: Temporal lags (1-3 periods), rolling averages, spatial neighbor effects
- **RandomForest Model**: R² = 0.93, MAE = 0.0039 on test data
- **Weekly Forecasts**: Pre-computed predictions with crime type classification

### Web Application
- **Interactive Map**: Leaflet-based heatmap with crime probability visualization
- **Crime Type Filtering**: Toggle between specific crime types (Furto, Roubo, etc.) or view all
- **Prediction Intervals**: Display 68% and 95% confidence intervals with error margins
- **Real-time Statistics**: Live summary panel with forecast metadata

### Production Infrastructure
- **REST API**: Flask backend with CORS support and health monitoring
- **MongoDB Integration**: Cloud database for forecast storage and retrieval
- **Scalable Deployment**: Containerized backend on Render, static frontend on Vercel

## Project Structure

```
prepol-project/
├── api/                             # Production Flask API
│   ├── server.py                   # Main API server with endpoints
│   ├── wsgi.py                     # Gunicorn WSGI entry point
│   └── requirements.txt            # Production dependencies
├── front/                           # React frontend application
│   ├── src/
│   │   ├── CrimeMap.jsx            # Main map component with layers
│   │   ├── Home.jsx                # Landing page
│   │   └── Components/             # Reusable UI components
│   ├── vite.config.js              # Vite build configuration
│   └── package.json                # Frontend dependencies
├── notebooks/                       # Data processing & ML pipeline
│   ├── Analysis&Treatment.ipynb    # 1. Clean raw RDO files
│   ├── H3Discretization.ipynb      # 2. Spatial aggregation & panel creation
│   ├── ModelTraining.ipynb         # 3. Train RandomForest model
│   ├── GenerateWeeklyPrediction.ipynb  # 4. Generate forecast panels
│   └── ModelUsage.ipynb            # Interactive testing & visualization
├── prepol/                          # Core utilities module
│   ├── config.py                   # Global configuration
│   └── helpers.py                  # H3 wrappers, datetime, CSV utilities
├── model/                           # Trained ML models
│   ├── rf_crime_model_*.joblib     # Serialized RandomForest
│   └── rf_crime_model_meta_*.json  # Model performance metrics
├── panels/                          # Pre-computed forecast data
│   ├── PrepolForecast_02/          # Forecast panel #2
│   │   ├── PrepolForecast_02.parquet
│   │   └── PrepolForecast_02_metadata.json
│   └── PrepolForecast_03/          # Forecast panel #3 (current)
├── scripts/                         # Utility scripts
│   └── mongodb/                    # MongoDB management tools
│       ├── import_forecast_to_mongodb.py
│       └── MongoControl.py         # Interactive MongoDB CLI
└── requirements.txt                 # Development dependencies
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OFFLINE PIPELINE (Jupyter)                   │
├─────────────────────────────────────────────────────────────────┤
│ RDO CSVs → Analysis&Treatment.ipynb → rdo_optimized.csv        │
│         ↓                                                        │
│ H3Discretization.ipynb → PrePol_panel_export.parquet           │
│         ↓                                                        │
│ ModelTraining.ipynb → rf_crime_model_*.joblib                   │
│         ↓                                                        │
│ GenerateWeeklyPrediction.ipynb → panels/PrepolForecast_XX/     │
│         ↓                                                        │
│ import_forecast_to_mongodb.py → MongoDB Atlas                   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                  PRODUCTION SYSTEM (Online)                     │
├─────────────────────────────────────────────────────────────────┤
│ React Frontend (Vercel) ←→ Flask API (Render) ←→ MongoDB       │
│   - Interactive map       - GET /api/forecast     - forecast_data
│   - Crime type layers     - GET /api/metadata     - 51K+ cells  │
│   - Statistics panel      - GET /api/health                     │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.11 (required for scikit-learn 1.3.0 compatibility)
- Node.js 18+ (for frontend development)
- MongoDB Atlas account (for production deployment)

### Backend Setup

```powershell
# Clone the repository
git clone https://github.com/jgvalarc/prepol-project.git
cd prepol-project

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # PowerShell

# Install API dependencies
pip install -r api/requirements.txt

# Set environment variables
$env:MONGODB_URI = "mongodb+srv://..."  # For using MongoDB

# Run backend locally
cd api
python server.py  # Runs on http://localhost:5000
```

### Frontend Setup

```powershell
# Navigate to frontend directory
cd front

# Install dependencies
npm install

# Run development server
npm run dev  # Runs on http://localhost:5173
```

### Development Dependencies (Notebooks)

```powershell
# For running Jupyter notebooks
pip install -r requirements.txt
```

**Key Packages**:
- **ML Stack**: pandas, numpy, scikit-learn==1.3.0, h3, pyarrow
- **API**: flask, flask-cors, gunicorn, pymongo
- **Visualization**: folium, geopandas, matplotlib

## Usage

### Development Workflow

#### 1. Data Processing Pipeline (One-time/Retraining)

Execute notebooks in sequence from `notebooks/` directory:

```powershell
# 1. Clean and normalize RDO data
Analysis&Treatment.ipynb → rdo_optimized.csv

# 2. Create H3 spatial panel with temporal features
H3Discretization.ipynb → PrePol_panel_export.parquet

# 3. Train RandomForest model
ModelTraining.ipynb → rf_crime_model_*.joblib
```

#### 2. Generate Weekly Forecasts

```powershell
# Generate forecast panel
GenerateWeeklyPrediction.ipynb → panels/PrepolForecast_XX/

# Upload to MongoDB (production)
cd scripts\mongodb
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_03
```

#### 3. Run Local Development Server

```powershell
# Terminal 1: Backend (Flask API)
cd api
python server.py

# Terminal 2: Frontend (React + Vite)
cd front
npm run dev

# Access application at http://localhost:5173
```

### API Endpoints

```http
GET /api/health          # Server status and data source info
GET /api/metadata        # Forecast period and statistics
GET /api/forecast        # Complete forecast as GeoJSON
GET /api/model-info      # Model performance metrics
```

### Production Deployment

**Backend (Render)**:
- Build: `pip install -r api/requirements.txt`
- Start: `gunicorn --chdir api wsgi:app --timeout 180`
- Env: `MONGODB_URI`, `PYTHON_VERSION=3.11.0`

**Frontend (Vercel)**:
- Root: `front/`
- Build: `npm run build`
- Env: `VITE_API_URL=https://prepol-api.onrender.com`

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

- `H3_RES = 10`: H3 resolution (config default; production forecasts use resolution 9)
- `TIME_FREQ = 'W'`: Time aggregation frequency (W=weekly, D=daily)
- `DEFAULT_TZ = 'America/Recife'`: Timezone for RDO datetime localization

Data source toggle in `api/server.py`:

- `USE_MONGODB_FORECAST = False`: Load from local parquet (development)
- `USE_MONGODB_FORECAST = True`: Load from MongoDB Atlas (production)

## Performance Optimization

- **Neighbor calculations**: Pre-built lookup dictionaries for O(1) access
- **Folium maps**: GeoJSON FeatureCollections instead of individual polygons (10x+ faster)
- **Parquet format**: Preferred for panel data (preserves dtypes, faster I/O)

## Model Performance

**Current Model** (`rf_crime_model_20251125_1448.joblib`):
- Test R²: **0.93** (excellent fit)
- Test MAE: **0.0039** crimes/period
- Test RMSE: 0.056
- Top feature: `y_norm` (normalized historical crime)
- Training data: 2013-2016 RDO reports (~1M records, 12K+ cells)

**Forecast Statistics** (PrepolForecast_03):
- Cells: 51,577 H3 hexagons (resolution 9)
- Total predicted crimes: ~1,412 crimes/week
- High-risk cells (>80% probability): 1 cell
- Crime types: Multi-type classification (Furto, Roubo, etc.)

## Technology Stack

**Machine Learning**:
- scikit-learn 1.3.0 (RandomForest)
- pandas, numpy (data processing)
- h3 (spatial discretization)
- pyarrow (parquet I/O)

**Backend**:
- Flask 3.0+ (REST API)
- pymongo (MongoDB driver)
- gunicorn (WSGI server)
- python-dotenv (environment management)

**Frontend**:
- React 18 (UI framework)
- Vite (build tool)
- Leaflet + react-leaflet (mapping)
- Material-UI (component library)

**Infrastructure**:
- MongoDB Atlas (cloud database)
- Render (backend hosting)
- Vercel (frontend hosting)

## Data Source

The project uses **RDO (Registro Digital de Ocorrência)** files from Brazilian police reports covering **2010-2017**. Crime data includes:
- Geographic coordinates (latitude/longitude)
- Timestamp (date and time of occurrence)
- Crime type classification (RUBRICA)
- ~1M+ crime records across Recife metropolitan area

Data is not included in the repository due to size and privacy considerations.

## Contributing

This is a research project. For contributions, bug reports, or questions:
- Open an issue on GitHub
- Submit a pull request with improvements
- Contact the repository maintainer

## Contact

Repository maintained by [@jgvalarc](https://github.com/jgvalarc)
