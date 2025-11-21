"""
PrePol Flask API Server
Serves crime probability predictions from trained RandomForest model.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
import sys
import os

# Add prepol module to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import prepol.config as config
import prepol.helpers as helpers

app = Flask(__name__)

# Configure CORS - allow all origins for prototype (restrict in production)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # In production, replace with your Vercel domain
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Global variables for model and data
rf_model = None
metadata = None
df_panel = None

def count_to_probability(daily_avg_count):
    """Convert daily average crime count to probability using Poisson distribution.
    
    P(≥1 crime on a day) = 1 - P(0 crimes) = 1 - e^(-λ)
    where λ = daily average crime count
    """
    return 1 - np.exp(-daily_avg_count)

def load_model():
    """Load trained model and metadata on startup."""
    global rf_model, metadata
    
    model_dir = project_root / "model"
    
    print(f"Looking for model in: {model_dir}")
    print(f"Model directory exists: {model_dir.exists()}")
    
    if model_dir.exists():
        model_files = sorted(model_dir.glob(f"{config.MODEL_PREFIX}_*.joblib"))
        print(f"Found {len(model_files)} model files")
    else:
        print(f"❌ Model directory not found: {model_dir}")
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    
    if not model_files:
        print(f"❌ No model found matching pattern: {config.MODEL_PREFIX}_*.joblib")
        raise FileNotFoundError(f"No model found in {model_dir}")
    
    model_path = model_files[-1]
    meta_path = model_path.with_name(
        model_path.stem.replace(config.MODEL_PREFIX, f"{config.MODEL_PREFIX}_meta") + ".json"
    )
    
    print(f"Loading model: {model_path}")
    print(f"Model file exists: {model_path.exists()}")
    
    rf_model = joblib.load(model_path)
    
    print(f"Loading metadata: {meta_path}")
    print(f"Metadata file exists: {meta_path.exists()}")
    
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"✓ Model loaded - Test R²: {metadata['metrics']['test']['r2']:.4f}")

def load_panel_data():
    """Load panel data on startup."""
    global df_panel
    
    panel_path = project_root / "notebooks" / "prepol_out" / "PrePol_panel_export.parquet"
    
    print(f"Looking for panel data at: {panel_path}")
    print(f"Panel file exists: {panel_path.exists()}")
    print(f"Parent directory exists: {panel_path.parent.exists()}")
    
    if panel_path.parent.exists():
        print(f"Files in {panel_path.parent}:")
        for f in panel_path.parent.iterdir():
            print(f"  - {f.name}")
    
    if not panel_path.exists():
        print(f"❌ Panel data not found: {panel_path}")
        raise FileNotFoundError(f"Panel data not found: {panel_path}")
    
    print(f"Loading panel data from {panel_path.name}...")
    df_panel = pd.read_parquet(panel_path)
    
    # Convert Period to string for easier handling
    if 'time_period' in df_panel.columns:
        if pd.api.types.is_period_dtype(df_panel['time_period']):
            df_panel['time_period_str'] = df_panel['time_period'].astype(str)
        else:
            df_panel['time_period_str'] = df_panel['time_period']
    
    print(f"✓ Panel loaded: {df_panel.shape[0]:,} records")
    print(f"  Date range: {df_panel['timestamp'].min()} to {df_panel['timestamp'].max()}")
    print(f"  H3 cells: {df_panel['h3_cell'].nunique():,}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model_loaded': rf_model is not None,
        'panel_loaded': df_panel is not None
    })

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Return available date range and model info."""
    if df_panel is None:
        return jsonify({'error': 'Panel data not loaded'}), 500
    
    return jsonify({
        'date_range': {
            'min': df_panel['timestamp'].min().strftime('%Y-%m-%d'),
            'max': df_panel['timestamp'].max().strftime('%Y-%m-%d')
        },
        'total_cells': int(df_panel['h3_cell'].nunique()),
        'model_metrics': metadata['metrics']['test'] if metadata else {}
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """Generate crime probability predictions for date range.
    
    Request JSON:
    {
        "start_date": "2016-12-01",
        "end_date": "2016-12-07"
    }
    
    Returns GeoJSON FeatureCollection with crime probabilities per H3 cell.
    """
    try:
        data = request.get_json()
        
        if not data or 'start_date' not in data or 'end_date' not in data:
            return jsonify({'error': 'Missing start_date or end_date'}), 400
        
        start_date = data['start_date']
        end_date = data['end_date']
        
        print(f"\n🎯 Prediction request: {start_date} to {end_date}")
        
        # Validate date format
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
        except Exception as e:
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
        
        # Validate date range (max 31 days for performance)
        days_diff = (end_dt - start_dt).days + 1
        if days_diff < 1:
            return jsonify({'error': 'End date must be after start date'}), 400
        if days_diff > 31:
            return jsonify({'error': 'Date range cannot exceed 31 days'}), 400
        
        # Filter panel data for target date range
        df_target = df_panel[
            (df_panel['time_period_str'] >= start_date) & 
            (df_panel['time_period_str'] <= end_date)
        ].copy()
        
        if len(df_target) == 0:
            return jsonify({'error': 'No data available for this date range'}), 404
        
        print(f"  Found {len(df_target):,} records for prediction")
        
        # Prepare features for prediction
        df_prep = df_target.copy()
        
        # Convert Period to ordinal if needed
        for col in df_prep.columns:
            if pd.api.types.is_period_dtype(df_prep[col]):
                df_prep[col] = df_prep[col].apply(lambda x: x.ordinal if pd.notna(x) else np.nan)
        
        # Extract features and predict
        feature_cols = metadata['feature_columns']
        X_target = df_prep[feature_cols].fillna(0)
        y_pred = rf_model.predict(X_target)
        
        # Add predictions to dataframe
        df_target['y_pred'] = np.clip(y_pred, 0, None)
        
        # Add coordinates
        df_target['lat'] = df_target['h3_cell'].apply(lambda x: helpers.h3_to_geo(x)[0])
        df_target['lon'] = df_target['h3_cell'].apply(lambda x: helpers.h3_to_geo(x)[1])
        
        # Aggregate by cell (temporal averaging)
        df_cell_agg = df_target.groupby('h3_cell').agg({
            'y': 'sum',
            'y_pred': 'mean',
            'lat': 'first',
            'lon': 'first',
            'time_period_str': 'count'
        }).reset_index()
        
        df_cell_agg.rename(columns={'time_period_str': 'n_days'}, inplace=True)
        
        # Calculate probability with Poisson distribution
        df_cell_agg['crime_probability'] = df_cell_agg['y_pred'].apply(count_to_probability)
        df_cell_agg['y_pred_total'] = df_cell_agg['y_pred'] * df_cell_agg['n_days']
        
        # Filter cells with meaningful probability (>5%)
        df_map = df_cell_agg[df_cell_agg['crime_probability'] > 0.05].copy()
        
        print(f"  Aggregated to {len(df_cell_agg):,} cells, {len(df_map):,} with >5% probability")
        
        # Build GeoJSON FeatureCollection
        features = []
        
        for idx, row in df_map.iterrows():
            # Get H3 cell boundary
            boundary = helpers.h3_to_boundary(row['h3_cell'])
            coords = [[[lon, lat] for lat, lon in boundary]]
            
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': coords
                },
                'properties': {
                    'h3_cell': row['h3_cell'],
                    'probability': float(row['crime_probability']),
                    'predicted_daily_avg': float(row['y_pred']),
                    'predicted_total': float(row['y_pred_total']),
                    'actual_total': int(row['y']),
                    'n_days': int(row['n_days']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon'])
                }
            }
            features.append(feature)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        # Calculate summary statistics
        summary = {
            'total_cells': int(len(df_cell_agg)),
            'displayed_cells': int(len(df_map)),
            'date_range': {
                'start': start_date,
                'end': end_date,
                'days': int(days_diff)
            },
            'statistics': {
                'mean_probability': float(df_cell_agg['crime_probability'].mean()),
                'median_probability': float(df_cell_agg['crime_probability'].median()),
                'total_predicted': float(df_cell_agg['y_pred_total'].sum()),
                'total_actual': int(df_cell_agg['y'].sum()),
                'high_risk_cells': int((df_cell_agg['crime_probability'] > 0.8).sum())
            }
        }
        
        print(f"✓ Prediction complete - returning {len(features)} features")
        
        return jsonify({
            'geojson': geojson,
            'summary': summary
        })
        
    except Exception as e:
        print(f"❌ Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("="*60)
    print("PrePol API Server - Starting")
    print("="*60)
    
    # Print library versions
    print("\n📚 Installed Libraries:")
    try:
        import flask
        print(f"  • Flask: {flask.__version__}")
    except ImportError:
        print("  • Flask: Not installed")
    
    try:
        print(f"  • Pandas: {pd.__version__}")
    except:
        print("  • Pandas: Not installed")
    
    try:
        print(f"  • NumPy: {np.__version__}")
    except:
        print("  • NumPy: Not installed")
    
    try:
        import sklearn
        print(f"  • scikit-learn: {sklearn.__version__}")
    except ImportError:
        print("  • scikit-learn: Not installed")
    
    try:
        import joblib
        print(f"  • joblib: {joblib.__version__}")
    except ImportError:
        print("  • joblib: Not installed")
    
    try:
        import h3
        print(f"  • h3: {h3.__version__}")
    except ImportError:
        print("  • h3: Not installed")
    
    try:
        import pyarrow
        print(f"  • pyarrow: {pyarrow.__version__}")
    except ImportError:
        print("  • pyarrow: Not installed")
    
    print()
    
    # Print working directory and project structure
    print(f"Working directory: {Path.cwd()}")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    print()
    
    try:
        load_model()
        load_panel_data()
        
        print("\n" + "="*60)
        print("✓ Server ready!")
        print("="*60)
        print(f"API running at: http://localhost:5000")
        print(f"Health check: http://localhost:5000/api/health")
        print(f"Metadata: http://localhost:5000/api/metadata")
        print("="*60 + "\n")
        
        # Get port from environment variable (Render uses PORT env var)
        port = int(os.environ.get('PORT', 5000))
        # Get host - use 0.0.0.0 for production, allows external connections
        host = '0.0.0.0'
        # Disable debug mode in production
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        
        app.run(debug=debug_mode, host=host, port=port)
        
    except Exception as e:
        print(f"\n❌ Failed to start server: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
