#!/usr/bin/env python3
"""
Import Forecast Panel to MongoDB
Script to import forecast panel data from parquet files into MongoDB

SECURITY WARNING: Always use MONGODB_URI environment variable for credentials.
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError, DuplicateKeyError
import argparse
from datetime import datetime
import dotenv

# Load environment variables from .env file if present
dotenv.load_dotenv()

# Default MongoDB URI
MONGODB_URI = os.environ.get('MONGODB_URI')

def connect_mongodb(uri=None):
    """Connect to MongoDB and return client and database"""
    mongodb_uri = uri or os.environ.get('MONGODB_URI') or MONGODB_URI

    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        # Test connection
        client.admin.command('ping')
        db = client.prepol_db
        print("✅ Connected to MongoDB successfully")
        return client, db
    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def find_forecast_panels(panels_dir):
    """Find all forecast panel directories"""
    panels_path = Path(panels_dir)
    if not panels_path.exists():
        print(f"❌ Panels directory not found: {panels_path}")
        return []

    forecast_dirs = []
    for item in panels_path.iterdir():
        if item.is_dir() and item.name.startswith('PrepolForecast_'):
            forecast_dirs.append(item)

    return sorted(forecast_dirs)

def load_forecast_data(forecast_dir):
    """Load forecast parquet and metadata"""
    forecast_name = forecast_dir.name

    # Find parquet and metadata files
    parquet_file = forecast_dir / f"{forecast_name}.parquet"
    metadata_file = forecast_dir / f"{forecast_name}_metadata.json"

    if not parquet_file.exists():
        print(f"❌ Parquet file not found: {parquet_file}")
        return None, None

    if not metadata_file.exists():
        print(f"❌ Metadata file not found: {metadata_file}")
        return None, None

    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load parquet data
        df = pd.read_parquet(parquet_file)

        print(f"✓ Loaded forecast data: {forecast_name}")
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {list(df.columns)}")

        return df, metadata

    except Exception as e:
        print(f"❌ Error loading forecast data: {e}")
        return None, None

def validate_forecast_document(doc, row_idx):
    """Validate a forecast document before insertion
    
    Returns: (is_valid, error_message)
    """
    # Required fields
    required_fields = ['h3_cell', 'forecast_week', 'forecast_year', 'predicted_total', 'crime_probability']
    for field in required_fields:
        if field not in doc:
            return False, f"Missing required field '{field}' at row {row_idx}"
    
    # Validate data types and ranges
    try:
        # Week should be 1-53
        if not (1 <= doc['forecast_week'] <= 53):
            return False, f"Invalid forecast_week at row {row_idx}: {doc['forecast_week']} (must be 1-53)"
        
        # Year should be reasonable (allow 1970 for testing/debugging, but warn)
        if doc['forecast_year'] == 1970:
            # This is likely a metadata error - try to infer correct year from current date
            import datetime
            current_year = datetime.datetime.now().year
            doc['forecast_year'] = current_year
        elif not (2000 <= doc['forecast_year'] <= 2100):
            return False, f"Invalid forecast_year at row {row_idx}: {doc['forecast_year']}"
        
        # Probability should be 0-1
        if not (0 <= doc['crime_probability'] <= 1):
            return False, f"Invalid crime_probability at row {row_idx}: {doc['crime_probability']} (must be 0-1)"
        
        # Predictions should be non-negative
        if doc['predicted_total'] < 0:
            return False, f"Invalid predicted_total at row {row_idx}: {doc['predicted_total']} (must be >= 0)"
        
        # Coordinates should be valid
        if 'coords' in doc:
            lat = doc['coords'].get('lat', 0)
            lon = doc['coords'].get('lon', 0)
            if not (-90 <= lat <= 90):
                return False, f"Invalid latitude at row {row_idx}: {lat}"
            if not (-180 <= lon <= 180):
                return False, f"Invalid longitude at row {row_idx}: {lon}"
        
        return True, None
        
    except (TypeError, ValueError) as e:
        return False, f"Validation error at row {row_idx}: {e}"

def prepare_forecast_documents(df, metadata):
    """Prepare forecast documents for MongoDB insertion with validation"""
    documents = []
    validation_errors = []

    forecast_info = metadata.get('forecast_info', {})
    week_of_year = forecast_info.get('forecast_period', {}).get('week_of_year')
    year = forecast_info.get('forecast_period', {}).get('year')

    # Check for metadata year issue (1970 = Unix epoch, likely wrong)
    if year == 1970:
        import datetime
        current_year = datetime.datetime.now().year
        print(f"⚠️  WARNING: Metadata shows year 1970 (likely incorrect). Auto-correcting to {current_year}.")
        year = current_year
    
    print(f"📅 Preparing documents for Week {week_of_year} of {year}...")

    for idx, row in df.iterrows():
        # Base document structure for forecast data
        doc = {
            'h3_cell': str(row['h3_cell']),  # Ensure string type
            'forecast_week': int(week_of_year),
            'forecast_year': int(year),
            'period': row.get('period'),
            'predicted_daily_avg': float(row['predicted_daily_avg']),
            'predicted_total': float(row['predicted_total']),
            'crime_probability': float(row['crime_probability']),
            'n_days': int(row.get('n_days', 7)),
            'coords': {
                'lat': float(row['lat']),
                'lon': float(row['lon'])
            },
            'forecast_generated': metadata.get('forecast_info', {}).get('generated_at'),
            'model_info': metadata.get('model_info', {}),
            'is_forecast': True  # Mark as forecast data
        }

        # Add any additional columns from the dataframe (like crime_type)
        for col in df.columns:
            if col not in ['h3_cell', 'period', 'predicted_daily_avg', 'predicted_total',
                          'crime_probability', 'n_days', 'lat', 'lon']:
                if pd.notna(row[col]):
                    value = row[col]
                    if isinstance(value, (pd.Timestamp, datetime)):
                        doc[col] = value
                    elif pd.api.types.is_integer_dtype(type(value)):
                        doc[col] = int(value)
                    elif pd.api.types.is_float_dtype(type(value)):
                        doc[col] = float(value)
                    else:
                        doc[col] = str(value)
        
        # Validate document
        is_valid, error_msg = validate_forecast_document(doc, idx)
        if not is_valid:
            validation_errors.append(error_msg)
            continue
        
        documents.append(doc)

    # Report validation results
    if validation_errors:
        print(f"⚠️  Validation warnings ({len(validation_errors)} documents skipped):")
        for error in validation_errors[:5]:
            print(f"   - {error}")
        if len(validation_errors) > 5:
            print(f"   ... and {len(validation_errors) - 5} more errors")
    
    print(f"✓ Prepared {len(documents):,} valid forecast documents")
    return documents

def create_forecast_collection_indexes(db, collection_name):
    """Create appropriate indexes for forecast collection with duplicate prevention"""
    collection = db[collection_name]

    print(f"🔧 Creating indexes for collection '{collection_name}'...")
    
    # Create unique compound index to prevent duplicates (CRITICAL FIX)
    try:
        collection.create_index(
            [('h3_cell', 1), ('forecast_week', 1), ('forecast_year', 1)],
            unique=True,
            name='unique_cell_week_year'
        )
        print(f"  ✓ Created UNIQUE compound index: h3_cell + forecast_week + forecast_year")
        print(f"     This prevents duplicate forecasts for the same cell/week/year")
    except Exception as e:
        print(f"  ⚠️  Unique index creation failed (may already exist): {e}")
    
    # Create other indexes for efficient querying
    other_indexes = [
        ('h3_cell', 1),
        ('forecast_week', 1),
        ('forecast_year', 1),
        ('crime_probability', -1),
        ('predicted_total', -1),
        ('is_forecast', 1)
    ]
    
    # Add crime_type index if it exists
    if collection.count_documents({'crime_type': {'$exists': True}}) > 0:
        other_indexes.append(('crime_type', 1))

    for index_spec in other_indexes:
        try:
            field, direction = index_spec
            collection.create_index([(field, direction)])
            print(f"  ✓ Created index: {field} ({direction})")
        except Exception as e:
            print(f"  ⚠️  Index creation failed (may already exist): {e}")

def import_forecast_to_mongodb(db, forecast_dir, collection_name="forecast_data", drop_existing=False):
    """Import forecast data to MongoDB with integrity checks
    
    NOTE: Default collection changed from 'forecast_panels' to 'forecast_data' (production collection)
    """
    print(f"📦 Importing to collection: {collection_name}")
    
    # Load data
    df, metadata = load_forecast_data(forecast_dir)
    if df is None or metadata is None:
        return False

    # Prepare documents with validation
    documents = prepare_forecast_documents(df, metadata)
    
    if not documents:
        print("❌ No valid documents to import")
        return False

    # Get or create collection
    collection = db[collection_name]

    # Check if forecast already exists
    forecast_info = metadata.get('forecast_info', {})
    week_of_year = forecast_info.get('forecast_period', {}).get('week_of_year')
    year = forecast_info.get('forecast_period', {}).get('year')

    existing_count = collection.count_documents({
        'forecast_week': week_of_year,
        'forecast_year': year
    })

    if existing_count > 0:
        if drop_existing:
            print(f"🗑️  Removing existing forecast data for Week {week_of_year} of {year}...")
            collection.delete_many({
                'forecast_week': week_of_year,
                'forecast_year': year
            })
        else:
            print(f"⚠️  Forecast data already exists for Week {week_of_year} of {year} ({existing_count:,} documents)")
            print("  Use --drop-existing to overwrite")
            return False

    # Create indexes if collection is new or empty
    if collection.count_documents({}) == 0:
        create_forecast_collection_indexes(db, collection_name)

    # Insert documents with error handling for duplicates
    print(f"📤 Inserting {len(documents):,} forecast documents...")
    
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    try:
        # Try bulk insert first (faster)
        result = collection.insert_many(documents, ordered=False)
        inserted_count = len(result.inserted_ids)
        print(f"✅ Successfully inserted {inserted_count:,} documents")
        return True
        
    except BulkWriteError as e:
        # Handle partial success
        write_errors = e.details.get('writeErrors', [])
        inserted_count = e.details.get('nInserted', 0)
        
        # Count duplicate key errors vs other errors
        for error in write_errors:
            if error.get('code') == 11000:  # Duplicate key error
                duplicate_count += 1
            else:
                error_count += 1
        
        print(f"⚠️  Bulk write completed with errors:")
        print(f"   ✓ Successfully inserted: {inserted_count:,} documents")
        if duplicate_count > 0:
            print(f"   ⚠️  Duplicates skipped: {duplicate_count:,} documents")
        if error_count > 0:
            print(f"   ❌ Other errors: {error_count:,} documents")
            for error in write_errors[:3]:
                if error.get('code') != 11000:
                    print(f"      Error: {error.get('errmsg', 'Unknown error')}")
        
        return inserted_count > 0
        
    except Exception as e:
        print(f"❌ Error inserting documents: {e}")
        return False

def list_available_forecasts(panels_dir):
    """List all available forecast panels"""
    forecast_dirs = find_forecast_panels(panels_dir)

    if not forecast_dirs:
        print("❌ No forecast panels found")
        return

    print(f"📁 Available forecast panels in {panels_dir}:")
    print("-" * 60)

    for forecast_dir in forecast_dirs:
        forecast_name = forecast_dir.name
        metadata_file = forecast_dir / f"{forecast_name}_metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                forecast_info = metadata.get('forecast_info', {})
                period = forecast_info.get('forecast_period', {})
                week = period.get('week_of_year', 'N/A')
                year = period.get('year', 'N/A')
                generated = forecast_info.get('generated_at', 'N/A')

                print(f"• {forecast_name}")
                print(f"  Week {week} of {year}")
                print(f"  Generated: {generated}")
                print()

            except Exception as e:
                print(f"• {forecast_name} (metadata error: {e})")
        else:
            print(f"• {forecast_name} (no metadata)")

def main():
    parser = argparse.ArgumentParser(
        description='Import forecast panel data to MongoDB',
        epilog='SECURITY: Set MONGODB_URI environment variable instead of using --mongodb-uri'
    )
    parser.add_argument('--panels-dir', default='../../panels',
                       help='Directory containing forecast panels (default: ../../panels)')
    parser.add_argument('--forecast-name', help='Specific forecast folder name to import')
    parser.add_argument('--collection', default='forecast_data',
                       help='MongoDB collection name (default: forecast_data)')
    parser.add_argument('--drop-existing', action='store_true',
                       help='Drop existing forecast data before importing')
    parser.add_argument('--list', action='store_true',
                       help='List available forecast panels')
    parser.add_argument('--mongodb-uri', help='MongoDB URI (INSECURE: use MONGODB_URI env var instead)')

    args = parser.parse_args()
    
    # Security warning for command-line URI
    if args.mongodb_uri:
        print("⚠️  WARNING: Passing MongoDB URI via command line is insecure!")
        print("   Use environment variable instead: $env:MONGODB_URI = 'your_uri'")
        print()

    # Convert relative path to absolute
    panels_dir = Path(args.panels_dir).resolve()

    if args.list:
        list_available_forecasts(panels_dir)
        return

    # Connect to MongoDB
    client, db = connect_mongodb(args.mongodb_uri)

    try:
        if args.forecast_name:
            # Import specific forecast
            forecast_dir = panels_dir / args.forecast_name
            if not forecast_dir.exists():
                print(f"❌ Forecast directory not found: {forecast_dir}")
                sys.exit(1)

            success = import_forecast_to_mongodb(db, forecast_dir, args.collection, args.drop_existing)
            if success:
                print("✅ Forecast import completed successfully")
            else:
                print("❌ Forecast import failed")
                sys.exit(1)

        else:
            # Import all available forecasts
            forecast_dirs = find_forecast_panels(panels_dir)

            if not forecast_dirs:
                print(f"❌ No forecast panels found in {panels_dir}")
                sys.exit(1)

            print(f"📤 Importing {len(forecast_dirs)} forecast panels...")

            success_count = 0
            for forecast_dir in forecast_dirs:
                print(f"\n{'='*50}")
                print(f"Importing: {forecast_dir.name}")
                print('='*50)

                if import_forecast_to_mongodb(db, forecast_dir, args.collection, args.drop_existing):
                    success_count += 1
                else:
                    print(f"❌ Failed to import {forecast_dir.name}")

            print(f"\n📊 Import Summary: {success_count}/{len(forecast_dirs)} successful")

            if success_count == len(forecast_dirs):
                print("✅ All forecast imports completed successfully")
            else:
                print("⚠️  Some imports failed")
                sys.exit(1)

    finally:
        client.close()

if __name__ == "__main__":
    main()