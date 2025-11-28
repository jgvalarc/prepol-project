#!/usr/bin/env python3
"""
MongoControl - Terminal Control Panel for MongoDB Operations
Direct interface for general MongoDB actions in PrePol project

SECURITY WARNING: Always set MONGODB_URI environment variable for production use.
"""
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import json
from datetime import datetime
from pathlib import Path

# Default MongoDB URI - SECURITY: Should be set via environment variable
DEFAULT_MONGODB_URI = "mongodb+srv://prepol-api:N1377Vi8pjs2fURT@prepol-cluster.ks5kzhh.mongodb.net/prepol_db?appName=prepol-cluster"

class MongoControl:
    def __init__(self):
        self.uri = os.environ.get('MONGODB_URI') or DEFAULT_MONGODB_URI
        self.client = None
        self.db = None
        self.current_collection = 'forecast_data'  # Default to production collection
        
        # Security warning if using hardcoded credentials
        if 'MONGODB_URI' not in os.environ:
            print("\n⚠️  SECURITY WARNING: Using hardcoded MongoDB credentials!")
            print("   Set environment variable: $env:MONGODB_URI = 'your_uri'")
            print()

    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client.prepol_db
            print("✅ Connected to MongoDB successfully")
            return True
        except ConnectionFailure as e:
            print(f"❌ Connection failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("🔌 Disconnected from MongoDB")

    def print_header(self):
        """Print the control panel header"""
        print("=" * 70)
        print("              MongoControl - MongoDB Operations")
        print("=" * 70)
        print("Direct terminal interface for MongoDB actions in PrePol")
        print()

    def print_menu(self):
        """Print the main menu"""
        collection_info = f" (Current: {self.current_collection})" if self.db else ""
        print(f"\nAvailable Operations:{collection_info}")
        print("1. Connect to MongoDB")
        print("2. Disconnect from MongoDB")
        print("3. List Databases")
        print("4. List Collections")
        print("5. Switch Collection (forecast_data/panel_data)")
        print("6. Count Documents in Current Collection")
        print("7. View Sample Documents")
        print("8. Get Collection Stats")
        print("9. Run Custom Query")
        print("10. Insert Test Document")
        print("11. Delete Test Documents")
        print("12. Import Forecast Data")
        print("13. Verify Forecast Integrity")
        print("14. Exit")
        print()

    def get_choice(self):
        """Get user choice"""
        while True:
            try:
                choice = input("Enter your choice (1-14): ").strip()
                if choice in [str(i) for i in range(1, 15)]:
                    return int(choice)
                else:
                    print("Invalid choice. Please enter 1-14.")
            except KeyboardInterrupt:
                print("\n\nExiting...")
                sys.exit(0)
            except:
                print("Invalid input. Please enter a number 1-14.")

    def list_databases(self):
        """List all databases"""
        if not self.client:
            print("❌ Not connected to MongoDB")
            return
        try:
            dbs = self.client.list_database_names()
            print(f"\n📊 Databases ({len(dbs)}):")
            for db in dbs:
                print(f"  - {db}")
        except Exception as e:
            print(f"❌ Error listing databases: {e}")

    def list_collections(self):
        """List collections in prepol_db"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            collections = self.db.list_collection_names()
            print(f"\n📋 Collections in prepol_db ({len(collections)}):")
            for coll in collections:
                marker = " ← CURRENT" if coll == self.current_collection else ""
                count = self.db[coll].count_documents({})
                print(f"  - {coll}: {count:,} documents{marker}")
        except Exception as e:
            print(f"❌ Error listing collections: {e}")

    def switch_collection(self):
        """Switch between collections"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        
        print("\n📂 Switch Collection:")
        print("  1. forecast_data (production forecasts)")
        print("  2. panel_data (historical panel data)")
        print("  3. Custom collection name")
        
        choice = input("Select collection (1-3): ").strip()
        
        if choice == '1':
            self.current_collection = 'forecast_data'
        elif choice == '2':
            self.current_collection = 'panel_data'
        elif choice == '3':
            custom_name = input("Enter collection name: ").strip()
            if custom_name:
                self.current_collection = custom_name
            else:
                print("❌ Invalid collection name")
                return
        else:
            print("❌ Invalid choice")
            return
        
        print(f"✅ Switched to collection: {self.current_collection}")

    def count_documents(self):
        """Count documents in current collection"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            collection = self.db[self.current_collection]
            count = collection.count_documents({})
            print(f"\n📈 Documents in {self.current_collection}: {count:,}")
            
            # Show breakdown if forecast_data
            if self.current_collection == 'forecast_data':
                forecast_count = collection.count_documents({'is_forecast': True})
                print(f"  - Forecast documents: {forecast_count:,}")
                
                # Group by week/year
                pipeline = [
                    {'$group': {
                        '_id': {'year': '$forecast_year', 'week': '$forecast_week'},
                        'count': {'$sum': 1}
                    }},
                    {'$sort': {'_id.year': 1, '_id.week': 1}}
                ]
                forecasts = list(collection.aggregate(pipeline))
                if forecasts:
                    print(f"  - Forecast periods: {len(forecasts)}")
                    for f in forecasts[:5]:
                        print(f"    • Week {f['_id']['week']} of {f['_id']['year']}: {f['count']:,} cells")
                    if len(forecasts) > 5:
                        print(f"    ... and {len(forecasts) - 5} more")
        except Exception as e:
            print(f"❌ Error counting documents: {e}")

    def view_sample_documents(self):
        """View sample documents from current collection"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            collection = self.db[self.current_collection]
            samples = list(collection.find().limit(3))
            print(f"\n📄 Sample documents from {self.current_collection}:")
            for i, doc in enumerate(samples, 1):
                doc_copy = dict(doc)
                doc_copy.pop('_id', None)
                print(f"\n--- Document {i} ---")
                print(json.dumps(doc_copy, indent=2, default=str))
        except Exception as e:
            print(f"❌ Error retrieving samples: {e}")

    def get_collection_stats(self):
        """Get statistics for current collection"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            stats = self.db.command("collStats", self.current_collection)
            print(f"\n📊 Collection Stats for {self.current_collection}:")
            print(f"  Size: {stats.get('size', 'N/A'):,} bytes ({stats.get('size', 0) / (1024**2):.2f} MB)")
            print(f"  Count: {stats.get('count', 'N/A'):,}")
            print(f"  Storage Size: {stats.get('storageSize', 'N/A'):,} bytes ({stats.get('storageSize', 0) / (1024**2):.2f} MB)")
            print(f"  Average Document Size: {stats.get('avgObjSize', 'N/A'):,} bytes")
            if 'indexSizes' in stats:
                print(f"  Indexes:")
                for idx_name, idx_size in stats['indexSizes'].items():
                    print(f"    - {idx_name}: {idx_size:,} bytes ({idx_size / 1024:.2f} KB)")
        except Exception as e:
            print(f"❌ Error getting stats: {e}")

    def run_custom_query(self):
        """Run a custom query"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            collection = self.db[self.current_collection]
            print(f"\n🔍 Custom Query on {self.current_collection}")
            print("Enter MongoDB query filter (JSON format, or 'all' for all documents):")
            query_input = input("Query: ").strip()
            
            if query_input.lower() == 'all':
                query = {}
            else:
                query = json.loads(query_input)
            
            limit = input("Limit results (default 5): ").strip()
            limit = int(limit) if limit.isdigit() else 5
            
            results = list(collection.find(query).limit(limit))
            total_matching = collection.count_documents(query)
            
            print(f"\n📋 Query Results ({len(results)} of {total_matching:,} matching documents):")
            for i, doc in enumerate(results, 1):
                doc_copy = dict(doc)
                doc_copy.pop('_id', None)
                print(f"\n--- Result {i} ---")
                print(json.dumps(doc_copy, indent=2, default=str))
                
        except json.JSONDecodeError:
            print("❌ Invalid JSON query format")
        except Exception as e:
            print(f"❌ Error running query: {e}")

    def insert_test_document(self):
        """Insert a test document"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        
        # Safety check for production collection
        if self.current_collection == 'forecast_data':
            confirm = input(f"⚠️  Insert test document into '{self.current_collection}'? (yes/no): ").lower().strip()
            if confirm != 'yes':
                print("❌ Operation cancelled")
                return
        
        try:
            collection = self.db[self.current_collection]
            
            # Create appropriate test document based on collection
            if self.current_collection == 'forecast_data':
                test_doc = {
                    "h3_cell": "test_cell_123",
                    "forecast_week": 99,
                    "forecast_year": 9999,
                    "period": datetime.now(),
                    "predicted_daily_avg": 0.001,
                    "predicted_total": 0.007,
                    "crime_probability": 0.001,
                    "n_days": 7,
                    "coords": {"lat": -8.05, "lon": -34.9},
                    "is_forecast": True,
                    "test_document": True
                }
            else:
                test_doc = {
                    "h3_cell": "test_cell_123",
                    "date": datetime.now(),
                    "y": 0,
                    "features": {"test": True},
                    "coords": {"lat": -8.05, "lon": -34.9},
                    "time_period": 999999,
                    "test_document": True
                }
            
            result = collection.insert_one(test_doc)
            print(f"✅ Test document inserted with ID: {result.inserted_id}")
            print(f"   Collection: {self.current_collection}")
        except Exception as e:
            print(f"❌ Error inserting document: {e}")

    def delete_test_documents(self):
        """Delete test documents"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        try:
            collection = self.db[self.current_collection]
            
            # Count first for confirmation
            count = collection.count_documents({"test_document": True})
            if count == 0:
                print(f"ℹ️  No test documents found in {self.current_collection}")
                return
            
            confirm = input(f"⚠️  Delete {count} test document(s) from '{self.current_collection}'? (yes/no): ").lower().strip()
            if confirm != 'yes':
                print("❌ Operation cancelled")
                return
            
            result = collection.delete_many({"test_document": True})
            print(f"🗑️  Deleted {result.deleted_count} test documents from {self.current_collection}")
        except Exception as e:
            print(f"❌ Error deleting documents: {e}")

    def import_forecast_data(self):
        """Import forecast data from panels directory"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return

        try:
            # Import the forecast import function
            sys.path.insert(0, str(Path(__file__).parent))
            from import_forecast_to_mongodb import find_forecast_panels, import_forecast_to_mongodb

            # Find available forecasts
            project_root = Path(__file__).parent.parent.parent
            panels_dir = project_root / "panels"

            forecast_dirs = find_forecast_panels(str(panels_dir))

            if not forecast_dirs:
                print(f"❌ No forecast panels found in {panels_dir}")
                return

            print(f"📁 Found {len(forecast_dirs)} forecast panels:")
            for i, forecast_dir in enumerate(forecast_dirs, 1):
                print(f"  {i}. {forecast_dir.name}")

            # Let user choose which forecast to import
            while True:
                try:
                    choice = input(f"\nEnter forecast number to import (1-{len(forecast_dirs)}), or 'all' for all: ").strip()
                    if choice.lower() == 'all':
                        selected_dirs = forecast_dirs
                        break
                    else:
                        idx = int(choice) - 1
                        if 0 <= idx < len(forecast_dirs):
                            selected_dirs = [forecast_dirs[idx]]
                            break
                        else:
                            print(f"Invalid choice. Please enter 1-{len(forecast_dirs)} or 'all'.")
                except ValueError:
                    print("Invalid input. Please enter a number or 'all'.")

            # Ask about target collection
            target_collection = input(f"Import to collection (default: {self.current_collection}): ").strip()
            if not target_collection:
                target_collection = self.current_collection
            
            # Ask about overwriting existing data
            drop_existing = input("Drop existing forecast data before importing? (yes/no): ").lower().strip() == 'yes'

            # Import selected forecasts
            success_count = 0
            for forecast_dir in selected_dirs:
                print(f"\n{'='*50}")
                print(f"Importing: {forecast_dir.name}")
                print('='*50)

                if import_forecast_to_mongodb(self.db, Path(forecast_dir), target_collection, drop_existing):
                    success_count += 1
                else:
                    print(f"❌ Failed to import {forecast_dir.name}")

            print(f"\n📊 Import Summary: {success_count}/{len(selected_dirs)} successful")

        except ImportError:
            print("❌ Could not import forecast import module. Make sure import_forecast.py exists.")
        except Exception as e:
            print(f"❌ Error importing forecast data: {e}")

    def verify_forecast_integrity(self):
        """Verify forecast data integrity"""
        if not self.db:
            print("❌ Not connected to MongoDB")
            return
        
        print("\n🔍 Verifying forecast data integrity...")
        
        try:
            collection = self.db[self.current_collection]
            
            # Check for required fields
            print("\n1. Checking required fields...")
            required_fields = ['h3_cell', 'forecast_week', 'forecast_year', 'predicted_total', 'crime_probability']
            
            for field in required_fields:
                missing = collection.count_documents({field: {'$exists': False}})
                if missing > 0:
                    print(f"   ⚠️  {missing:,} documents missing '{field}'")
                else:
                    print(f"   ✓ All documents have '{field}'")
            
            # Check for duplicates
            print("\n2. Checking for duplicate forecasts...")
            pipeline = [
                {'$group': {
                    '_id': {
                        'h3_cell': '$h3_cell',
                        'week': '$forecast_week',
                        'year': '$forecast_year'
                    },
                    'count': {'$sum': 1}
                }},
                {'$match': {'count': {'$gt': 1}}}
            ]
            duplicates = list(collection.aggregate(pipeline))
            if duplicates:
                print(f"   ⚠️  Found {len(duplicates)} duplicate cell/week/year combinations")
                for dup in duplicates[:5]:
                    print(f"      - Cell {dup['_id']['h3_cell'][:12]}..., Week {dup['_id']['week']}/{dup['_id']['year']}: {dup['count']} copies")
            else:
                print(f"   ✓ No duplicates found")
            
            # Check value ranges
            print("\n3. Checking value ranges...")
            
            # Probability should be 0-1
            invalid_prob = collection.count_documents({
                'crime_probability': {'$not': {'$gte': 0, '$lte': 1}}
            })
            if invalid_prob > 0:
                print(f"   ⚠️  {invalid_prob:,} documents with invalid probability (not 0-1)")
            else:
                print(f"   ✓ All probabilities in valid range [0, 1]")
            
            # Negative predictions
            negative_pred = collection.count_documents({'predicted_total': {'$lt': 0}})
            if negative_pred > 0:
                print(f"   ⚠️  {negative_pred:,} documents with negative predictions")
            else:
                print(f"   ✓ No negative predictions")
            
            # Check indexes
            print("\n4. Checking indexes...")
            indexes = list(collection.list_indexes())
            print(f"   Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"      - {idx['name']}")
            
            # Summary statistics
            print("\n5. Summary Statistics:")
            total_docs = collection.count_documents({})
            forecast_docs = collection.count_documents({'is_forecast': True})
            
            print(f"   Total documents: {total_docs:,}")
            print(f"   Forecast documents: {forecast_docs:,}")
            
            if total_docs > 0:
                pipeline = [
                    {'$group': {
                        '_id': None,
                        'avg_prob': {'$avg': '$crime_probability'},
                        'min_prob': {'$min': '$crime_probability'},
                        'max_prob': {'$max': '$crime_probability'},
                        'avg_pred': {'$avg': '$predicted_total'}
                    }}
                ]
                stats = list(collection.aggregate(pipeline))
                if stats:
                    s = stats[0]
                    print(f"   Probability: avg={s.get('avg_prob', 0):.4f}, min={s.get('min_prob', 0):.4f}, max={s.get('max_prob', 0):.4f}")
                    print(f"   Avg prediction: {s.get('avg_pred', 0):.4f} crimes/week")
            
            print("\n✅ Integrity check complete")
            
        except Exception as e:
            print(f"❌ Error during integrity check: {e}")

    def main_loop(self):
        """Main control loop"""
        self.print_header()

        while True:
            self.print_menu()
            choice = self.get_choice()

            if choice == 1:
                self.connect()
            elif choice == 2:
                self.disconnect()
            elif choice == 3:
                self.list_databases()
            elif choice == 4:
                self.list_collections()
            elif choice == 5:
                self.switch_collection()
            elif choice == 6:
                self.count_documents()
            elif choice == 7:
                self.view_sample_documents()
            elif choice == 8:
                self.get_collection_stats()
            elif choice == 9:
                self.run_custom_query()
            elif choice == 10:
                self.insert_test_document()
            elif choice == 11:
                self.delete_test_documents()
            elif choice == 12:
                self.import_forecast_data()
            elif choice == 13:
                self.verify_forecast_integrity()
            elif choice == 14:
                print("\n👋 Thank you for using MongoControl!")
                self.disconnect()
                break

            # Wait for user to continue
            input("\nPress Enter to continue...")

def main():
    """Main entry point"""
    try:
        control = MongoControl()
        control.main_loop()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting MongoControl...")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()