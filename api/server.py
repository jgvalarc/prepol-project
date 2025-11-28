"""
PrePol Flask API Server
Serves pre-computed crime probability forecasts from MongoDB.

DATA SOURCE CONFIGURATION:
- Set USE_MONGODB_FORECAST = True to load forecast from MongoDB Atlas (requires MONGODB_URI env var)
- Set USE_MONGODB_FORECAST = False to load forecast from local parquet file (for testing)
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add prepol module to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import prepol.config as config
import prepol.helpers as helpers

# ============================================================================
# DATA SOURCE CONFIGURATION - Change this to switch between local and MongoDB forecast
# ============================================================================
USE_MONGODB_FORECAST = False  # Set to True to load forecast from MongoDB
# ============================================================================

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
df_forecast = None  # Forecast data loaded on startup
mongo_client = None  # Used when USE_MONGODB_FORECAST = True
mongo_forecast_collection = None  # Used when USE_MONGODB_FORECAST = True

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

def load_forecast_data_parquet():
    """Load forecast data from local parquet file (for testing only)."""
    global df_forecast
    
    # Look for latest forecast file
    forecast_dir = project_root / "panels" / "PrepolForecast_03"
    forecast_files = sorted(forecast_dir.glob("PrepolForecast_*.parquet"))
    
    if not forecast_files:
        raise FileNotFoundError("No forecast files found in panels/ directory")
    
    forecast_path = forecast_files[-1]  # Latest forecast
    
    print(f"Loading forecast from PARQUET: {forecast_path.name}")
    
    try:
        df_forecast = pd.read_parquet(forecast_path)
        print(f"✓ Forecast loaded (raw): {len(df_forecast):,} rows")

        # Ensure expected columns exist and compute probability if missing
        if 'crime_probability' not in df_forecast.columns and 'predicted_daily_avg' in df_forecast.columns:
            print("  Computing crime_probability from predicted_daily_avg (Poisson)")
            df_forecast['crime_probability'] = df_forecast['predicted_daily_avg'].apply(count_to_probability)

        # Filter out cells with negligible probability (match notebook visualization)
        if 'crime_probability' in df_forecast.columns:
            threshold = 0.05  # 5% default filter (notebook uses > 5%)
            before = len(df_forecast)
            df_forecast = df_forecast[df_forecast['crime_probability'] > threshold].reset_index(drop=True)
            after = len(df_forecast)
            print(f"  Filtered forecast: kept {after:,} of {before:,} rows (crime_probability > {threshold})")
        else:
            print("  Warning: 'crime_probability' column missing and could not be computed; no filtering applied")

        # Add coordinates if not present
        if 'lat' not in df_forecast.columns or 'lon' not in df_forecast.columns:
            print("  Computing H3 coordinates...")
            df_forecast['lat'] = df_forecast['h3_cell'].apply(lambda x: helpers.h3_to_geo(x)[0])
            df_forecast['lon'] = df_forecast['h3_cell'].apply(lambda x: helpers.h3_to_geo(x)[1])

        # Print crime types if available
        if 'crime_type' in df_forecast.columns:
            crime_types = df_forecast['crime_type'].unique()
            print(f"  Crime types: {len(crime_types)} ({', '.join(crime_types[:3])}{'...' if len(crime_types) > 3 else ''})")

    except Exception as e:
        print(f"❌ Failed to load forecast parquet: {str(e)}")
        raise

def load_forecast_data_mongodb():
    """Load latest forecast data from MongoDB forecast_data collection."""
    global df_forecast, mongo_client, mongo_forecast_collection
    
    print("Connecting to MongoDB for forecast data...")
    
    # Get MongoDB URI from environment
    MONGODB_URI = os.environ.get('MONGODB_URI')
    
    if not MONGODB_URI:
        print("❌ MONGODB_URI environment variable not set!")
        print("   Set it with: $env:MONGODB_URI = 'your-uri-here'")
        raise ValueError("MONGODB_URI environment variable is required when USE_MONGODB_FORECAST = True")
    
    try:
        from pymongo import MongoClient
        
        # Connect to MongoDB
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        mongo_client.admin.command('ping')
        
        # Get forecast collection
        db = mongo_client.prepol_db
        mongo_forecast_collection = db.forecast_data
        
        # Get latest forecast by generated_at
        latest_forecast_doc = mongo_forecast_collection.find_one(
            sort=[("generated_at", -1)]
        )
        
        if not latest_forecast_doc:
            raise ValueError("No forecast data found in MongoDB forecast_data collection")
        
        forecast_id = latest_forecast_doc.get('forecast_id')
        print(f"Loading forecast: {forecast_id}")
        
        # Load all documents for this forecast
        cursor = mongo_forecast_collection.find({"forecast_id": forecast_id})
        docs = list(cursor)
        
        if not docs:
            raise ValueError(f"No data found for forecast {forecast_id}")
        
        # Convert to DataFrame
        df_forecast = pd.DataFrame(docs)
        # Clean up MongoDB fields
        df_forecast = df_forecast.drop(['_id'], axis=1, errors='ignore')

        # If probability is missing but daily avg exists, compute it
        if 'crime_probability' not in df_forecast.columns and 'predicted_daily_avg' in df_forecast.columns:
            print("  Computing crime_probability from predicted_daily_avg (Poisson) [MongoDB]")
            df_forecast['crime_probability'] = df_forecast['predicted_daily_avg'].apply(count_to_probability)

        # Apply the same visualization filter as the notebook: keep only meaningful probabilities
        if 'crime_probability' in df_forecast.columns:
            threshold = 0.05
            before = len(df_forecast)
            df_forecast = df_forecast[df_forecast['crime_probability'] > threshold].reset_index(drop=True)
            after = len(df_forecast)
            print(f"  Filtered MongoDB forecast: kept {after:,} of {before:,} rows (crime_probability > {threshold})")
        else:
            print("  Warning: 'crime_probability' missing in MongoDB docs; no filtering applied")
        
        print("✓ Forecast loaded from MongoDB:")
        print(f"  Forecast ID: {forecast_id}")
        print(f"  Cells: {len(df_forecast):,}")
        print(f"  Generated: {latest_forecast_doc.get('generated_at', 'Unknown')}")
        print(f"  Period: {latest_forecast_doc.get('forecast_period', {}).get('start', 'Unknown')} to {latest_forecast_doc.get('forecast_period', {}).get('end', 'Unknown')}")
        
        # Print crime types if available
        if 'crime_type' in df_forecast.columns:
            crime_types = df_forecast['crime_type'].unique()
            print(f"  Crime types: {len(crime_types)} ({', '.join(crime_types[:3])}{'...' if len(crime_types) > 3 else ''})")
        
    except ImportError:
        print("❌ pymongo not installed!")
        print("   Install with: pip install pymongo")
        raise
    except Exception as e:
        print(f"❌ MongoDB forecast loading failed: {str(e)}")
        raise


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with forecast data status."""
    if USE_MONGODB_FORECAST:
        # MongoDB forecast mode
        forecast_loaded = mongo_forecast_collection is not None
        forecast_info = None
        
        if forecast_loaded and df_forecast is not None:
            forecast_info = {
                'cells': len(df_forecast),
                'crime_types': len(df_forecast['crime_type'].unique()) if 'crime_type' in df_forecast.columns else 0,
                'generated_at': str(df_forecast.iloc[0].get('generated_at', 'Unknown')) if len(df_forecast) > 0 else 'Unknown'
            }
        
        response = jsonify({
            'status': 'healthy',
            'data_source': 'mongodb_forecast',
            'model_loaded': rf_model is not None,
            'forecast_loaded': forecast_loaded and df_forecast is not None,
            'forecast_info': forecast_info
        })
    else:
        # Local parquet forecast mode
        response = jsonify({
            'status': 'healthy',
            'data_source': 'parquet_forecast',
            'model_loaded': rf_model is not None,
            'forecast_loaded': df_forecast is not None,
            'forecast_info': {
                'cells': len(df_forecast) if df_forecast is not None else 0,
                'crime_types': len(df_forecast['crime_type'].unique()) if df_forecast is not None and 'crime_type' in df_forecast.columns else 0
            } if df_forecast is not None else None
        })
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Return forecast metadata and model info."""
    try:
        if df_forecast is None:
            return jsonify({'error': 'Forecast data not loaded'}), 500
        
        # Get forecast info from first row
        forecast_info = df_forecast.iloc[0] if len(df_forecast) > 0 else {}
        
        crime_types = df_forecast['crime_type'].unique() if 'crime_type' in df_forecast.columns else []
        
        return jsonify({
            'forecast_period': forecast_info.get('forecast_period', {}),
            'total_cells': len(df_forecast),
            'crime_types': list(crime_types),
            'model_version': forecast_info.get('model_version', 'Unknown'),
            'generated_at': str(forecast_info.get('generated_at', 'Unknown')),
            'statistics': {
                'mean_probability': float(df_forecast['crime_probability'].mean()),
                'total_predicted_crimes': float(df_forecast['predicted_total'].sum()),
                'high_risk_cells': int((df_forecast['crime_probability'] > 0.8).sum())
            },
            'model_metrics': metadata['metrics']['test'] if metadata else {},
            'data_source': 'mongodb_forecast' if USE_MONGODB_FORECAST else 'parquet_forecast'
        })
    except Exception as e:
        print(f"❌ Metadata endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast', methods=['GET'])
def get_forecast():
    """Return entire pre-computed forecast as GeoJSON with crime type layers."""
    try:
        if df_forecast is None:
            return jsonify({'error': 'Forecast data not loaded'}), 500

        print("Generating forecast GeoJSON...")

        # Build GeoJSON features
        features = []

        for idx, row in df_forecast.iterrows():
            # Get H3 cell boundary
            boundary = helpers.h3_to_boundary(row['h3_cell'])
            coords = [[[lon, lat] for lat, lon in boundary]]

            # Color function (match notebook implementation)
            def get_red_gradient(prob):
                r = int(255 - (116 * prob))
                g = int(200 - (200 * prob))
                b = int(200 - (200 * prob))
                return f'#{r:02x}{g:02x}{b:02x}'

            fill_color = get_red_gradient(row['crime_probability'])

            # Popup content
            popup_html = f"""
            <div style='font-family: Arial, sans-serif; font-size: 12px;'>
            <b>Previsão de Crime</b><br/>
            <b>Probabilidade:</b> {row['crime_probability']*100:.1f}%<br/>
            <b>Previsão Diária:</b> {row['predicted_daily_avg']:.3f}<br/>
            <b>Total Semanal:</b> {row['predicted_total']:.2f}<br/>
            {'<b>Tipo:</b> ' + str(row.get('crime_type', 'N/A')) if 'crime_type' in row else ''}
            </div>
            """

            feature = {
                'type': 'Feature',
                'geometry': {'type': 'Polygon', 'coordinates': coords},
                'properties': {
                    'h3_cell': row['h3_cell'],
                    'probability': float(row['crime_probability']),
                    'predicted_daily_avg': float(row['predicted_daily_avg']),
                    'predicted_total': float(row['predicted_total']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'fillColor': fill_color,
                    'color': fill_color,
                    'weight': 1,
                    'fillOpacity': 0.6,
                    'popup': popup_html,
                    'tooltip': f"{row.get('crime_type', 'Crime')}: {row['crime_probability']*100:.1f}%",
                    'crime_type': str(row.get('crime_type', 'All'))
                }
            }
            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'total_cells': len(df_forecast),
                'crime_types': list(df_forecast['crime_type'].unique()) if 'crime_type' in df_forecast.columns else [],
                'generated_at': str(df_forecast.iloc[0].get('generated_at', 'Unknown')) if len(df_forecast) > 0 else 'Unknown',
                'forecast_period': df_forecast.iloc[0].get('forecast_period', {}) if len(df_forecast) > 0 else {}
            }
        }

        print(f"✓ Forecast GeoJSON generated: {len(features)} features")

        response = jsonify(geojson)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"❌ Error generating forecast: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Initialize model and data on module import (works with both Flask dev server and gunicorn)
def initialize_app():
    """Initialize model and forecast data."""
    print("="*60)
    print("PrePol API Server - Initializing")
    print("="*60)
    print(f"\n🔧 DATA SOURCE: {'MongoDB Forecast' if USE_MONGODB_FORECAST else 'Parquet Forecast'}")
    print(f"   To switch: Edit USE_MONGODB_FORECAST in server.py (line ~30)\n")
    
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
    
    if USE_MONGODB_FORECAST:
        try:
            import pymongo
            print(f"  • pymongo: {pymongo.__version__}")
        except ImportError:
            print("  • pymongo: NOT INSTALLED (required for MongoDB forecast mode)")
    
    print()
    
    # Print working directory and project structure
    print(f"Working directory: {Path.cwd()}")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    print()
    
    try:
        load_model()
        
        # Load forecast data based on USE_MONGODB_FORECAST flag
        if USE_MONGODB_FORECAST:
            load_forecast_data_mongodb()
        else:
            load_forecast_data_parquet()
        
        print("\n" + "="*60)
        print("✓ Server ready!")
        print(f"  Data source: {'MongoDB Forecast' if USE_MONGODB_FORECAST else 'Parquet Forecast'}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Failed to initialize: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# Initialize on module import (called by both gunicorn and direct execution)
initialize_app()

if __name__ == '__main__':
    # This block only runs when executing directly with python
    print(f"API running at: http://localhost:5000")
    print(f"Health check: http://localhost:5000/api/health")
    print(f"Metadata: http://localhost:5000/api/metadata")
    print(f"Forecast: http://localhost:5000/api/forecast")
    print("="*60 + "\n")
    
    # Get port from environment variable (Render uses PORT env var)
    port = int(os.environ.get('PORT', 5000))
    # Get host - use 0.0.0.0 for production, allows external connections
    host = '0.0.0.0'
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug_mode, host=host, port=port)
