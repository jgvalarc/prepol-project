"""
PrePol Flask API Server
Serves crime probability predictions from trained RandomForest model.

DATA SOURCE CONFIGURATION:
- Set USE_MONGODB = True to use MongoDB Atlas (requires MONGODB_URI env var)
- Set USE_MONGODB = False to use local parquet file (default for local testing)
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
# DATA SOURCE CONFIGURATION - Change this to switch between parquet and MongoDB
# ============================================================================
USE_MONGODB = True  # Set to True to use MongoDB, False to use local parquet
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
df_panel = None  # Used when USE_MONGODB = False
mongo_client = None  # Used when USE_MONGODB = True
mongo_collection = None  # Used when USE_MONGODB = True

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

def load_panel_data_parquet():
    """Load panel data from parquet file (local mode)."""
    global df_panel
    
    # Dataset to be used. Change filename as needed. Reminder: Full panel is too large for Render free tier.
    panel_path = project_root / "panels" / "PrePol_panel_2013-2016.parquet"
    
    print(f"Loading panel data from PARQUET...")
    print(f"Looking for panel data at: {panel_path}")
    print(f"Panel file exists: {panel_path.exists()}")
    
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
    
    print(f"✓ Parquet panel loaded: {df_panel.shape[0]:,} records")
    print(f"  Date range: {df_panel['timestamp'].min()} to {df_panel['timestamp'].max()}")
    print(f"  H3 cells: {df_panel['h3_cell'].nunique():,}")

def load_panel_data_mongodb():
    """Connect to MongoDB and set up collection access (MongoDB mode)."""
    global mongo_client, mongo_collection
    
    print(f"Connecting to MONGODB...")
    
    # Get MongoDB URI from environment
    MONGODB_URI = os.environ.get('MONGODB_URI')
    
    if not MONGODB_URI:
        print(f"❌ MONGODB_URI environment variable not set!")
        print(f"   Set it with: $env:MONGODB_URI = 'your-uri-here'")
        raise ValueError("MONGODB_URI environment variable is required when USE_MONGODB = True")
    
    try:
        from pymongo import MongoClient
        
        # Connect to MongoDB
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        
        # Test connection
        mongo_client.admin.command('ping')
        
        # Get collection
        db = mongo_client.prepol_db
        mongo_collection = db.panel_data
        
        # Get statistics
        total_docs = mongo_collection.count_documents({})
        
        # Get date range from metadata
        metadata_col = db.metadata
        metadata_doc = metadata_col.find_one({'_id': 'model_info'})
        
        print(f"✓ MongoDB connected: {total_docs:,} documents")
        if metadata_doc:
            date_range = metadata_doc.get('date_range', {})
            print(f"  Date range: {date_range.get('min')} to {date_range.get('max')}")
            print(f"  H3 cells: {metadata_doc.get('total_cells', 'N/A'):,}")
        
    except ImportError:
        print(f"❌ pymongo not installed!")
        print(f"   Install with: pip install pymongo")
        raise
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        raise

def get_panel_data_mongodb(start_date, end_date):
    """Query MongoDB for date range and return as DataFrame.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
    
    Returns:
        DataFrame with panel data for the date range
    """
    # Convert to datetime
    start_dt = pd.to_datetime(start_date).to_pydatetime()
    end_dt = pd.to_datetime(end_date).to_pydatetime()
    
    # Query MongoDB
    cursor = mongo_collection.find({
        'date': {'$gte': start_dt, '$lte': end_dt}
    })
    
    # Convert to list (this loads all documents into memory)
    docs = list(cursor)
    
    if not docs:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(docs)
    
    # Flatten nested features
    features_df = pd.json_normalize(df['features'])
    df = pd.concat([df.drop('features', axis=1), features_df], axis=1)
    
    # Add required columns
    df['timestamp'] = df['date']
    df['time_period_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Extract lat/lon from coords
    df['lat'] = df['coords'].apply(lambda x: x['lat'])
    df['lon'] = df['coords'].apply(lambda x: x['lon'])
    
    return df

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    if USE_MONGODB:
        # MongoDB mode
        panel_loaded = mongo_collection is not None
        date_range = None
        panel_shape = None
        
        if panel_loaded:
            try:
                # Get metadata from MongoDB
                metadata_col = mongo_client.prepol_db.metadata
                metadata_doc = metadata_col.find_one({'_id': 'model_info'})
                if metadata_doc:
                    dr = metadata_doc.get('date_range', {})
                    date_range = {
                        'min': dr.get('min').strftime('%Y-%m-%d') if dr.get('min') else None,
                        'max': dr.get('max').strftime('%Y-%m-%d') if dr.get('max') else None
                    }
                    total_docs = metadata_doc.get('total_records', 0)
                    total_cells = metadata_doc.get('total_cells', 0)
                    panel_shape = [total_docs, total_cells]
            except:
                pass
        
        response = jsonify({
            'status': 'healthy',
            'data_source': 'mongodb',
            'model_loaded': rf_model is not None,
            'panel_loaded': panel_loaded,
            'panel_shape': panel_shape,
            'date_range': date_range
        })
    else:
        # Parquet mode
        response = jsonify({
            'status': 'healthy',
            'data_source': 'parquet',
            'model_loaded': rf_model is not None,
            'panel_loaded': df_panel is not None,
            'panel_shape': df_panel.shape if df_panel is not None else None,
            'date_range': {
                'min': df_panel['timestamp'].min().strftime('%Y-%m-%d') if df_panel is not None else None,
                'max': df_panel['timestamp'].max().strftime('%Y-%m-%d') if df_panel is not None else None
            } if df_panel is not None else None
        })
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Return available date range and model info."""
    try:
        if USE_MONGODB:
            # MongoDB mode
            if mongo_collection is None:
                return jsonify({'error': 'MongoDB not connected'}), 500
            
            # Get metadata from MongoDB
            metadata_col = mongo_client.prepol_db.metadata
            metadata_doc = metadata_col.find_one({'_id': 'model_info'})
            
            if not metadata_doc:
                return jsonify({'error': 'Metadata not found in MongoDB'}), 500
            
            date_range = metadata_doc.get('date_range', {})
            return jsonify({
                'date_range': {
                    'min': date_range.get('min').strftime('%Y-%m-%d') if date_range.get('min') else None,
                    'max': date_range.get('max').strftime('%Y-%m-%d') if date_range.get('max') else None
                },
                'total_cells': int(metadata_doc.get('total_cells', 0)),
                'model_metrics': metadata['metrics']['test'] if metadata else {},
                'data_source': 'mongodb'
            })
        else:
            # Parquet mode
            if df_panel is None:
                return jsonify({'error': 'Panel data not loaded'}), 500
            
            return jsonify({
                'date_range': {
                    'min': df_panel['timestamp'].min().strftime('%Y-%m-%d'),
                    'max': df_panel['timestamp'].max().strftime('%Y-%m-%d')
                },
                'total_cells': int(df_panel['h3_cell'].nunique()),
                'model_metrics': metadata['metrics']['test'] if metadata else {},
                'data_source': 'parquet'
            })
    except Exception as e:
        print(f"❌ Metadata endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

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
        
        # Get panel data based on data source
        if USE_MONGODB:
            print(f"  Querying MongoDB for date range...")
            df_target = get_panel_data_mongodb(start_date, end_date)
        else:
            print(f"  Filtering parquet data for date range...")
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
        
        # Add coordinates (use existing coords if from MongoDB, otherwise compute)
        if USE_MONGODB and 'lat' in df_target.columns and 'lon' in df_target.columns:
            # Coordinates already extracted from MongoDB coords field
            pass
        else:
            # Compute coordinates from H3 cells
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

# Initialize model and data on module import (works with both Flask dev server and gunicorn)
def initialize_app():
    """Initialize model and panel data."""
    print("="*60)
    print("PrePol API Server - Initializing")
    print("="*60)
    print(f"\n🔧 DATA SOURCE: {'MongoDB' if USE_MONGODB else 'Parquet (Local)'}")
    print(f"   To switch: Edit USE_MONGODB in server.py (line ~30)\n")
    
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
    
    if USE_MONGODB:
        try:
            import pymongo
            print(f"  • pymongo: {pymongo.__version__}")
        except ImportError:
            print("  • pymongo: NOT INSTALLED (required for MongoDB mode)")
    
    print()
    
    # Print working directory and project structure
    print(f"Working directory: {Path.cwd()}")
    print(f"Project root: {project_root}")
    print(f"Project root exists: {project_root.exists()}")
    print()
    
    try:
        load_model()
        
        # Load data based on USE_MONGODB flag
        if USE_MONGODB:
            load_panel_data_mongodb()
        else:
            load_panel_data_parquet()
        
        print("\n" + "="*60)
        print("✓ Server ready!")
        print(f"  Data source: {'MongoDB' if USE_MONGODB else 'Parquet'}")
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
    print("="*60 + "\n")
    
    # Get port from environment variable (Render uses PORT env var)
    port = int(os.environ.get('PORT', 5000))
    # Get host - use 0.0.0.0 for production, allows external connections
    host = '0.0.0.0'
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(debug=debug_mode, host=host, port=port)
