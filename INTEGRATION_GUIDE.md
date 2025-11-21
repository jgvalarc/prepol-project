# PrePol Integration - Setup Guide

## Quick Start

### 1. Backend API Setup

```powershell
# Navigate to project root
cd d:\BackupSupremo\Work\prepol-project

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install API dependencies
pip install -r api\requirements.txt

# Start the Flask API server
python api\server.py
```

The API will start at `http://localhost:5000`

**Available endpoints:**
- `GET /api/health` - Health check
- `GET /api/metadata` - Available date range and model info
- `POST /api/predict` - Generate crime predictions

### 2. Frontend Setup

```powershell
# Navigate to frontend folder
cd front

# Install new dependencies (leaflet for maps)
npm install

# Start development server
npm run dev
```

The frontend will start at `http://localhost:5173`

## Usage

1. Open browser to `http://localhost:5173/Map`
2. Click the **Tune icon** (⚙️) in top-right corner
3. Select **start date** and **end date** (max 31 days)
4. Click **"Aplicar Filtros"** button
5. Map will display crime probability predictions:
   - **Light red**: Low probability (<33rd percentile)
   - **Medium red**: Medium probability (33rd-67th percentile)
   - **Dark red**: High probability (>67th percentile)
6. Click on any cell to see detailed stats

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│  (http://localhost:5173)                               │
│                                                         │
│  - PlaceholderImage.jsx (main container)               │
│  - MapAppBar.jsx (date picker controls)                │
│  - CrimeMap.jsx (Leaflet map + GeoJSON)                │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ HTTP POST /api/predict
                  │ { start_date, end_date }
                  │
┌─────────────────▼───────────────────────────────────────┐
│                  Flask API Backend                      │
│  (http://localhost:5000)                               │
│                                                         │
│  - Loads trained RF model (.joblib)                    │
│  - Loads panel data (.parquet)                         │
│  - Generates predictions for date range                │
│  - Aggregates by H3 cell (temporal averaging)          │
│  - Applies Poisson probability: 1 - e^(-λ)             │
│  - Returns GeoJSON with cell boundaries + probabilities │
└─────────────────┬───────────────────────────────────────┘
                  │
                  │ Reads from disk
                  │
┌─────────────────▼───────────────────────────────────────┐
│               Trained Model & Data                      │
│                                                         │
│  - model/rf_crime_model_*.joblib                       │
│  - notebooks/prepol_out/PrePol_panel_export.parquet    │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

1. **User selects date range** in MapAppBar date pickers
2. **Frontend sends POST request** to `/api/predict` with dates
3. **Backend filters panel data** for specified date range
4. **Model generates predictions** for each cell × day combination
5. **Backend aggregates** predictions by H3 cell (daily average)
6. **Poisson probability calculation**: `P(≥1 crime/day) = 1 - e^(-λ)`
   - λ = daily average crime count
   - Handles multiple crimes per day correctly
7. **Backend builds GeoJSON** with cell boundaries and properties
8. **Frontend renders** Leaflet map with colored polygons
9. **User interacts** with map (hover tooltips, click popups)

## Probability Interpretation

The system uses **Poisson distribution** to model crime occurrence:

| Daily Avg (λ) | Probability | Interpretation |
|---------------|-------------|----------------|
| 0.10 | 9.5% | Crime ~once per 10 days |
| 0.50 | 39.3% | Crime every 2-3 days |
| 1.00 | 63.2% | Crime most days |
| 2.00 | 86.5% | Crime almost every day |
| 3.00 | 95.0% | Crime virtually daily |

**Why Poisson?**
- Models discrete random events (crimes)
- Correctly handles multiple crimes per day
- `P(≥1 crime) = 1 - P(0 crimes) = 1 - e^(-λ)`

## API Request/Response Examples

### Request
```json
POST http://localhost:5000/api/predict
Content-Type: application/json

{
  "start_date": "2016-12-01",
  "end_date": "2016-12-07"
}
```

### Response
```json
{
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[-34.9, -8.05], ...]]
        },
        "properties": {
          "h3_cell": "89a8100d3ffffff",
          "probability": 0.452,
          "predicted_daily_avg": 0.147,
          "predicted_total": 4.6,
          "actual_total": 5,
          "n_days": 31,
          "lat": -8.0523,
          "lon": -34.9156
        }
      }
    ]
  },
  "summary": {
    "total_cells": 43251,
    "displayed_cells": 8432,
    "date_range": {
      "start": "2016-12-01",
      "end": "2016-12-31",
      "days": 31
    },
    "statistics": {
      "mean_probability": 0.251,
      "median_probability": 0.189,
      "total_predicted": 15234.2,
      "total_actual": 15680,
      "high_risk_cells": 342
    }
  }
}
```

## Troubleshooting

### Backend won't start
- **Check model files exist**: `model/rf_crime_model_*.joblib`
- **Check panel data exists**: `notebooks/prepol_out/PrePol_panel_export.parquet`
- **Run notebooks first**: Execute notebooks 1-3 to generate required data
- **Install dependencies**: `pip install -r api\requirements.txt`

### Frontend shows "Failed to fetch"
- **Backend not running**: Start `python api\server.py` first
- **CORS error**: Flask-CORS should be installed (check api/requirements.txt)
- **Port conflict**: Backend must be on port 5000

### Map doesn't render
- **Install Leaflet**: Run `npm install` in `front/` directory
- **Check console**: Browser DevTools → Console for errors
- **API returned error**: Check Network tab for API response

### Predictions taking too long
- **Reduce date range**: Limit to 7 days instead of 31
- **Check data size**: Panel has ~14M records, large ranges are slow
- **Optimize model**: Current RF has 100 trees, could reduce for speed

## Performance Notes

- **Small ranges (1-7 days)**: ~1-2 seconds
- **Medium ranges (8-14 days)**: ~2-4 seconds  
- **Large ranges (15-31 days)**: ~5-10 seconds
- **Max allowed range**: 31 days (enforced by API)

## Development Tips

1. **Keep both servers running**: Backend (port 5000) + Frontend (port 5173)
2. **Hot reload works**: Frontend changes auto-refresh, backend needs restart
3. **Check API logs**: Flask prints request details in terminal
4. **Use browser DevTools**: Network tab shows API calls, Console shows errors
5. **Test API directly**: Use Postman or curl for backend debugging

## Future Enhancements

- [ ] Add loading progress bar for long predictions
- [ ] Cache frequent date ranges server-side
- [ ] Add crime type filtering (model selection)
- [ ] Export predictions as CSV/JSON
- [ ] Add historical data comparison view
- [ ] Implement authentication (currently open)
- [ ] Deploy to production server
