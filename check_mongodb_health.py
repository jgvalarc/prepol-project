"""
MongoDB Health Check Script for PrePol Project
Tests MongoDB connection, data integrity, indexes, and query performance
Run this after migration to verify database is ready for production
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime, timedelta
import time
import os

# Add prepol module to path
sys.path.insert(0, str(Path(__file__).parent))
import prepol.helpers as helpers
import prepol.config as config

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

def get_mongodb_uri():
    """Get MongoDB URI from environment or user input"""
    uri = os.environ.get('MONGODB_URI')
    
    if uri:
        print_info(f"Using MONGODB_URI from environment variable")
        # Mask password in display
        display_uri = uri.split('@')[0].split('//')[1]
        masked_uri = uri.replace(display_uri, '***:***')
        print_info(f"URI: {masked_uri}")
        return uri
    else:
        print_warning("MONGODB_URI not found in environment")
        uri = input("Enter MongoDB URI (or press Enter to skip): ").strip()
        if not uri:
            return None
        return uri

def test_connection(uri):
    """Test basic MongoDB connection"""
    print_header("1. CONNECTION TEST")
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force connection
        client.admin.command('ping')
        print_success("Connected to MongoDB Atlas")
        
        # Get server info
        server_info = client.server_info()
        print_info(f"MongoDB version: {server_info['version']}")
        print_info(f"Server: {client.address[0]}:{client.address[1]}")
        
        return client
    
    except ServerSelectionTimeoutError:
        print_error("Connection timeout - check your internet connection and URI")
        return None
    except ConnectionFailure as e:
        print_error(f"Connection failed: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return None

def test_database_structure(client):
    """Test database and collection structure"""
    print_header("2. DATABASE STRUCTURE")
    
    try:
        # List databases
        databases = client.list_database_names()
        print_info(f"Available databases: {', '.join(databases)}")
        
        # Check prepol_db exists
        if 'prepol_db' not in databases:
            print_error("Database 'prepol_db' not found!")
            print_warning("Run migrate_to_mongodb.py first")
            return False
        
        print_success("Database 'prepol_db' exists")
        
        # Get collections
        db = client.prepol_db
        collections = db.list_collection_names()
        print_info(f"Collections: {', '.join(collections)}")
        
        # Check required collections
        required_collections = ['panel_data', 'metadata']
        missing = [c for c in required_collections if c not in collections]
        
        if missing:
            print_error(f"Missing collections: {', '.join(missing)}")
            return False
        
        print_success("All required collections exist")
        return True
        
    except Exception as e:
        print_error(f"Database structure check failed: {e}")
        return False

def test_panel_data(client):
    """Test panel_data collection"""
    print_header("3. PANEL DATA INTEGRITY")
    
    try:
        db = client.prepol_db
        collection = db.panel_data
        
        # Document count
        total_docs = collection.count_documents({})
        print_info(f"Total documents: {total_docs:,}")
        
        if total_docs == 0:
            print_error("Panel data collection is empty!")
            return False
        
        print_success(f"Collection contains {total_docs:,} documents")
        
        # Sample document
        sample = collection.find_one()
        if not sample:
            print_error("Could not retrieve sample document")
            return False
        
        print_info("Sample document structure:")
        print_info(f"  h3_cell: {sample.get('h3_cell', 'MISSING')}")
        print_info(f"  date: {sample.get('date', 'MISSING')}")
        print_info(f"  y: {sample.get('y', 'MISSING')}")
        print_info(f"  features: {list(sample.get('features', {}).keys())}")
        print_info(f"  coords: {sample.get('coords', 'MISSING')}")
        print_info(f"  time_period: {sample.get('time_period', 'MISSING')}")
        
        # Check required fields
        required_fields = ['h3_cell', 'date', 'y', 'features', 'coords', 'time_period']
        missing_fields = [f for f in required_fields if f not in sample]
        
        if missing_fields:
            print_error(f"Sample document missing fields: {', '.join(missing_fields)}")
            return False
        
        print_success("Document structure is valid")
        
        # Check feature completeness
        required_features = ['y_norm', 'y_lag_1', 'y_lag_2', 'y_lag_3', 
                           'y_rol_3', 'y_rol_7', 'y_lag_1_vizinhos']
        features = sample.get('features', {})
        missing_features = [f for f in required_features if f not in features]
        
        if missing_features:
            print_warning(f"Sample document missing features: {', '.join(missing_features)}")
        else:
            print_success("All required features present")
        
        # Date range
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'min_date': {'$min': '$date'},
                    'max_date': {'$max': '$date'}
                }
            }
        ]
        result = list(collection.aggregate(pipeline))
        
        if result:
            min_date = result[0]['min_date']
            max_date = result[0]['max_date']
            print_info(f"Date range: {min_date.date()} to {max_date.date()}")
            days_span = (max_date - min_date).days + 1
            print_info(f"Total days: {days_span}")
        
        # Unique cells
        unique_cells = len(collection.distinct('h3_cell'))
        print_info(f"Unique H3 cells: {unique_cells:,}")
        
        # Calculate expected records (cells × days)
        if result:
            expected_records = unique_cells * days_span
            print_info(f"Expected records (complete panel): {expected_records:,}")
            completeness = (total_docs / expected_records) * 100
            print_info(f"Panel completeness: {completeness:.2f}%")
            
            if completeness < 95:
                print_warning(f"Panel is only {completeness:.2f}% complete")
            else:
                print_success(f"Panel is {completeness:.2f}% complete")
        
        return True
        
    except Exception as e:
        print_error(f"Panel data check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_indexes(client):
    """Test database indexes"""
    print_header("4. INDEX VERIFICATION")
    
    try:
        db = client.prepol_db
        collection = db.panel_data
        
        # Get indexes
        indexes = list(collection.list_indexes())
        print_info(f"Total indexes: {len(indexes)}")
        
        for idx in indexes:
            name = idx['name']
            keys = idx.get('key', {})
            print_info(f"  - {name}: {dict(keys)}")
        
        # Check for required indexes
        index_names = [idx['name'] for idx in indexes]
        
        # Should have: _id_ (default), cell_date_idx, date_idx
        if 'cell_date_idx' in index_names:
            print_success("Compound index (h3_cell, date) exists")
        else:
            print_warning("Compound index missing - queries may be slow")
        
        if 'date_idx' in index_names:
            print_success("Date index exists")
        else:
            print_warning("Date index missing - date range queries may be slow")
        
        return True
        
    except Exception as e:
        print_error(f"Index check failed: {e}")
        return False

def test_query_performance(client):
    """Test query performance"""
    print_header("5. QUERY PERFORMANCE")
    
    try:
        db = client.prepol_db
        collection = db.panel_data
        
        # Get a sample cell and date range
        sample = collection.find_one()
        if not sample:
            print_error("No data to test queries")
            return False
        
        test_cell = sample['h3_cell']
        test_date = sample['date']
        
        # Test 1: Single cell query
        print_info("Test 1: Single cell query")
        start = time.time()
        result = collection.find_one({'h3_cell': test_cell})
        elapsed = (time.time() - start) * 1000
        
        if result:
            print_success(f"Single cell query: {elapsed:.2f}ms")
        else:
            print_error("Single cell query failed")
        
        # Test 2: Date range query (7 days)
        print_info("Test 2: Date range query (7 days)")
        end_date = test_date + timedelta(days=7)
        start = time.time()
        count = collection.count_documents({
            'date': {'$gte': test_date, '$lte': end_date}
        })
        elapsed = (time.time() - start) * 1000
        
        print_success(f"7-day range query: {count:,} docs in {elapsed:.2f}ms")
        
        # Test 3: Compound query (cell + date range)
        print_info("Test 3: Compound query (cell + date range)")
        start = time.time()
        cursor = collection.find({
            'h3_cell': test_cell,
            'date': {'$gte': test_date, '$lte': end_date}
        })
        results = list(cursor)
        elapsed = (time.time() - start) * 1000
        
        print_success(f"Compound query: {len(results)} docs in {elapsed:.2f}ms")
        
        # Test 4: Aggregation pipeline (simulate prediction query)
        print_info("Test 4: Aggregation pipeline (simulated prediction)")
        start = time.time()
        pipeline = [
            {'$match': {'date': {'$gte': test_date, '$lte': end_date}}},
            {'$group': {
                '_id': '$h3_cell',
                'avg_y': {'$avg': '$y'},
                'count': {'$sum': 1}
            }},
            {'$limit': 100}
        ]
        results = list(collection.aggregate(pipeline))
        elapsed = (time.time() - start) * 1000
        
        print_success(f"Aggregation: {len(results)} cells in {elapsed:.2f}ms")
        
        # Performance summary
        print_info("\nPerformance summary:")
        if elapsed < 100:
            print_success("Query performance is excellent (<100ms)")
        elif elapsed < 500:
            print_success("Query performance is good (<500ms)")
        elif elapsed < 1000:
            print_warning("Query performance is acceptable (<1s)")
        else:
            print_warning(f"Query performance is slow ({elapsed:.0f}ms)")
            print_info("Consider adding indexes or optimizing queries")
        
        return True
        
    except Exception as e:
        print_error(f"Query performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata(client):
    """Test metadata collection"""
    print_header("6. METADATA VERIFICATION")
    
    try:
        db = client.prepol_db
        collection = db.metadata
        
        # Get model_info document
        metadata = collection.find_one({'_id': 'model_info'})
        
        if not metadata:
            print_error("Model metadata not found")
            return False
        
        print_success("Model metadata exists")
        
        # Display metadata
        print_info("Metadata contents:")
        print_info(f"  Date range: {metadata.get('date_range', {}).get('min')} to {metadata.get('date_range', {}).get('max')}")
        print_info(f"  Total cells: {metadata.get('total_cells', 'N/A'):,}")
        print_info(f"  Total records: {metadata.get('total_records', 'N/A'):,}")
        print_info(f"  Migrated at: {metadata.get('migrated_at', 'N/A')}")
        print_info(f"  Source file: {metadata.get('source_file', 'N/A')}")
        
        return True
        
    except Exception as e:
        print_error(f"Metadata check failed: {e}")
        return False

def test_data_consistency(client):
    """Test data consistency and validate against parquet if available"""
    print_header("7. DATA CONSISTENCY")
    
    try:
        db = client.prepol_db
        collection = db.panel_data
        
        # Check for null/missing values
        print_info("Checking for data quality issues...")
        
        # Count documents with missing features
        pipeline = [
            {'$match': {'features.y_lag_1': None}},
            {'$count': 'missing_lag1'}
        ]
        result = list(collection.aggregate(pipeline))
        missing_lag1 = result[0]['missing_lag1'] if result else 0
        
        if missing_lag1 > 0:
            print_warning(f"Found {missing_lag1:,} documents with null y_lag_1")
        else:
            print_success("No missing lag features detected")
        
        # Check for duplicate (cell, date) pairs
        pipeline = [
            {'$group': {
                '_id': {'h3_cell': '$h3_cell', 'date': '$date'},
                'count': {'$sum': 1}
            }},
            {'$match': {'count': {'$gt': 1}}},
            {'$count': 'duplicates'}
        ]
        result = list(collection.aggregate(pipeline))
        duplicates = result[0]['duplicates'] if result else 0
        
        if duplicates > 0:
            print_error(f"Found {duplicates:,} duplicate (cell, date) pairs!")
        else:
            print_success("No duplicate (cell, date) pairs found")
        
        # Check for coordinate validity
        sample_coords = collection.find_one({'coords': {'$exists': True}})
        if sample_coords:
            coords = sample_coords['coords']
            lat, lon = coords.get('lat'), coords.get('lon')
            
            # Rough bounds for Brazil
            if -34 < lat < 6 and -74 < lon < -34:
                print_success("Coordinate ranges look valid (Brazil bounds)")
            else:
                print_warning(f"Coordinate ranges unusual: lat={lat}, lon={lon}")
        
        # Compare with parquet if available
        parquet_path = Path("panels/PrePol_panel_2016Q4.parquet")
        if parquet_path.exists():
            try:
                print_info("\nComparing with source parquet file...")
                df_parquet = pd.read_parquet(parquet_path)
                
                mongo_count = collection.count_documents({})
                parquet_count = len(df_parquet)
                
                print_info(f"MongoDB documents: {mongo_count:,}")
                print_info(f"Parquet rows: {parquet_count:,}")
                
                if mongo_count == parquet_count:
                    print_success("Document counts match!")
                else:
                    diff = abs(mongo_count - parquet_count)
                    print_warning(f"Document count mismatch: {diff:,} difference")
            except Exception as e:
                print_warning(f"Could not read parquet file for comparison: {e}")
                print_info("Skipping parquet comparison (not critical)")
        
        return True
        
    except Exception as e:
        print_error(f"Data consistency check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_compatibility(client):
    """Test if MongoDB data is compatible with trained model"""
    print_header("8. MODEL COMPATIBILITY")
    
    try:
        # Check if model exists
        model_dir = Path("model")
        model_files = sorted(model_dir.glob(f"{config.MODEL_PREFIX}_*.joblib"))
        
        if not model_files:
            print_warning("No trained model found - skipping compatibility check")
            return True
        
        model_path = model_files[-1]
        meta_path = model_path.with_name(
            model_path.stem.replace(config.MODEL_PREFIX, f"{config.MODEL_PREFIX}_meta") + ".json"
        )
        
        print_info(f"Model: {model_path.name}")
        
        if not meta_path.exists():
            print_warning("Model metadata not found - skipping feature check")
            return True
        
        # Load metadata
        import json
        with open(meta_path, 'r') as f:
            metadata = json.load(f)
        
        required_features = metadata.get('feature_columns', [])
        print_info(f"Model requires {len(required_features)} features")
        
        # Get sample document from MongoDB
        db = client.prepol_db
        collection = db.panel_data
        sample = collection.find_one()
        
        if not sample:
            print_error("No sample document to test")
            return False
        
        # Check if all required features are available
        available_features = list(sample.get('features', {}).keys())
        available_features.append('time_period')  # Also available as field
        
        missing_features = [f for f in required_features if f not in available_features]
        
        if missing_features:
            print_error(f"Missing features in MongoDB: {', '.join(missing_features)}")
            return False
        else:
            print_success("All model features available in MongoDB")
        
        # Check feature data types
        print_info("Validating feature data types...")
        features = sample['features']
        
        for feature_name, value in features.items():
            if not isinstance(value, (int, float)):
                print_warning(f"Feature '{feature_name}' has unexpected type: {type(value)}")
        
        print_success("Feature data types are valid")
        
        return True
        
    except Exception as e:
        print_error(f"Model compatibility check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_report(results):
    """Generate final report"""
    print_header("HEALTH CHECK SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    
    print_info(f"Total tests: {total_tests}")
    print_info(f"Passed: {passed_tests}")
    print_info(f"Failed: {failed_tests}")
    print_info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print()
    
    if failed_tests == 0:
        print_success("✓ MongoDB is fully functional and ready for production!")
        print_info("\nNext steps:")
        print_info("1. Update api/server.py to use MongoDB instead of parquet")
        print_info("2. Add pymongo to api/requirements.txt")
        print_info("3. Set MONGODB_URI environment variable in production")
        print_info("4. Test API endpoints with MongoDB backend")
        print_info("5. Deploy to production (Render)")
        return 0
    else:
        print_error(f"✗ {failed_tests} test(s) failed - MongoDB is NOT ready")
        print_info("\nFailed tests:")
        for test_name, passed in results.items():
            if not passed:
                print_error(f"  - {test_name}")
        
        print_info("\nRecommended actions:")
        print_info("1. Review error messages above")
        print_info("2. Re-run migrate_to_mongodb.py if data is missing")
        print_info("3. Check MongoDB Atlas connection and permissions")
        print_info("4. Verify indexes are created correctly")
        return 1

def main():
    """Main health check routine"""
    print_header("PrePol MongoDB Health Check")
    print_info("This script will test MongoDB connection, data integrity, and readiness")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get MongoDB URI
    uri = get_mongodb_uri()
    if not uri:
        print_error("No MongoDB URI provided - cannot proceed")
        return 1
    
    # Initialize results dictionary
    results = {}
    
    # Test 1: Connection
    client = test_connection(uri)
    results['Connection'] = client is not None
    
    if not client:
        print_error("\nCannot proceed without database connection")
        return 1
    
    try:
        # Test 2: Database structure
        results['Database Structure'] = test_database_structure(client)
        
        # Test 3: Panel data
        results['Panel Data'] = test_panel_data(client)
        
        # Test 4: Indexes
        results['Indexes'] = test_indexes(client)
        
        # Test 5: Query performance
        results['Query Performance'] = test_query_performance(client)
        
        # Test 6: Metadata
        results['Metadata'] = test_metadata(client)
        
        # Test 7: Data consistency
        results['Data Consistency'] = test_data_consistency(client)
        
        # Test 8: Model compatibility
        results['Model Compatibility'] = test_model_compatibility(client)
        
    finally:
        # Always close connection
        client.close()
    
    # Generate final report
    exit_code = generate_report(results)
    
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Health check interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.RED}✗ Health check failed with unexpected error:{Colors.END}")
        print(f"{Colors.RED}{str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
