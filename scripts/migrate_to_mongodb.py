"""
Migrate parquet panel data to MongoDB Atlas
Run once before deploying to Render
"""
from pymongo import MongoClient, ASCENDING
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import prepol.helpers as helpers

def migrate():
    print("="*60)
    print("PrePol Panel Data Migration to MongoDB")
    print("="*60)
    
    # Get MongoDB URI
    MONGODB_URI = input("Enter MongoDB URI: ").strip()
    if not MONGODB_URI:
        print("❌ No URI provided. Exiting.")
        return
    
    PARQUET_PATH = Path("panels/PrePol_panel_2016Q4.parquet")
    
    if not PARQUET_PATH.exists():
        print(f"❌ Panel file not found: {PARQUET_PATH}")
        return
    
    # Connect to MongoDB
    print("\n1. Connecting to MongoDB Atlas...")
    try:
        client = MongoClient(MONGODB_URI)
        db = client.prepol_db
        collection = db.panel_data
        
        # Test connection
        client.admin.command('ping')
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Load parquet
    print("\n2. Loading parquet file...")
    df = pd.read_parquet(PARQUET_PATH)
    print(f"✓ Loaded {len(df):,} records")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  H3 cells: {df['h3_cell'].nunique():,}")
    print(f"  Columns: {list(df.columns)}")
    
    # Convert to documents
    print("\n3. Converting to MongoDB documents...")
    
    # Pre-compute coordinates (avoid h3_to_geo in loop)
    print("  Computing coordinates for all cells...")
    unique_cells = df['h3_cell'].unique()
    coords_map = {}
    for i, cell in enumerate(unique_cells):
        lat, lon = helpers.h3_to_geo(cell)
        coords_map[cell] = {"lat": float(lat), "lon": float(lon)}
        if (i + 1) % 100 == 0:
            print(f"    Processed {i + 1}/{len(unique_cells)} cells...")
    
    print(f"✓ Computed coordinates for {len(coords_map):,} cells")
    
    # Convert rows to documents
    print("  Converting rows to documents...")
    documents = []
    for idx, row in df.iterrows():
        # Convert Period to ordinal if needed
        if hasattr(row['time_period'], 'ordinal'):
            time_period_ordinal = row['time_period'].ordinal
        else:
            # Fallback: convert to pandas Period
            time_period_ordinal = pd.Period(row['timestamp'], freq='D').ordinal
        
        doc = {
            "h3_cell": row['h3_cell'],
            "date": pd.to_datetime(row['timestamp']).to_pydatetime(),
            "y": int(row['y']),
            "features": {
                "y_norm": float(row['y_norm']) if pd.notna(row['y_norm']) else 0.0,
                "y_lag_1": float(row['y_lag_1']) if pd.notna(row['y_lag_1']) else 0.0,
                "y_lag_2": float(row['y_lag_2']) if pd.notna(row['y_lag_2']) else 0.0,
                "y_lag_3": float(row['y_lag_3']) if pd.notna(row['y_lag_3']) else 0.0,
                "y_rol_3": float(row['y_rol_3']) if pd.notna(row['y_rol_3']) else 0.0,
                "y_rol_7": float(row['y_rol_7']) if pd.notna(row['y_rol_7']) else 0.0,
                "y_lag_1_vizinhos": int(row['y_lag_1_vizinhos']) if pd.notna(row['y_lag_1_vizinhos']) else 0
            },
            "coords": coords_map[row['h3_cell']],
            "time_period": int(time_period_ordinal)
        }
        documents.append(doc)
        
        # Progress indicator
        if (idx + 1) % 50000 == 0:
            print(f"    Converted {idx + 1:,}/{len(df):,} records...")
    
    print(f"✓ Converted {len(documents):,} documents")
    
    # Insert into MongoDB
    print("\n4. Inserting into MongoDB...")
    print("  (This may take 2-5 minutes for 911K records)")
    
    # Drop existing collection if exists
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"  Found existing collection with {existing_count:,} documents")
        confirm = input("  Drop and recreate? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("  Aborting migration.")
            client.close()
            return
        print("  Dropping existing collection...")
        collection.drop()
    
    # Bulk insert (batches of 10K)
    batch_size = 10000
    total_inserted = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        try:
            result = collection.insert_many(batch, ordered=False)
            total_inserted += len(result.inserted_ids)
            print(f"  Inserted {total_inserted:,}/{len(documents):,} ({100*total_inserted/len(documents):.1f}%)")
        except Exception as e:
            print(f"  ⚠️  Error inserting batch {i//batch_size + 1}: {e}")
            continue
    
    print(f"✓ Inserted {total_inserted:,} documents")
    
    # Create indexes
    print("\n5. Creating indexes...")
    try:
        collection.create_index([("h3_cell", ASCENDING), ("date", ASCENDING)], 
                               name="cell_date_idx")
        print("  ✓ Created compound index: (h3_cell, date)")
    except Exception as e:
        print(f"  ⚠️  Index creation warning: {e}")
    
    try:
        collection.create_index([("date", ASCENDING)], name="date_idx")
        print("  ✓ Created index: date")
    except Exception as e:
        print(f"  ⚠️  Index creation warning: {e}")
    
    # Get index info
    indexes = collection.list_indexes()
    print("  Current indexes:")
    for idx in indexes:
        print(f"    - {idx['name']}: {idx.get('key', {})}")
    
    # Insert metadata
    print("\n6. Inserting metadata...")
    metadata_col = db.metadata
    metadata_col.delete_many({})  # Clear existing
    metadata_doc = {
        "_id": "model_info",
        "date_range": {
            "min": df['timestamp'].min().to_pydatetime(),
            "max": df['timestamp'].max().to_pydatetime()
        },
        "total_cells": int(df['h3_cell'].nunique()),
        "total_records": int(len(df)),
        "migrated_at": datetime.utcnow(),
        "source_file": str(PARQUET_PATH)
    }
    metadata_col.insert_one(metadata_doc)
    print("✓ Metadata inserted")
    
    # Verify
    print("\n7. Verification:")
    final_count = collection.count_documents({})
    print(f"  Documents in collection: {final_count:,}")
    print(f"  Expected: {len(documents):,}")
    
    if final_count == len(documents):
        print("  ✓ Document count matches!")
    else:
        print(f"  ⚠️  Mismatch: {len(documents) - final_count} documents missing")
    
    # Sample queries
    print("\n  Sample queries:")
    sample = collection.find_one({"h3_cell": df['h3_cell'].iloc[0]})
    if sample:
        print(f"    Single document:")
        print(f"      h3_cell: {sample['h3_cell']}")
        print(f"      date: {sample['date']}")
        print(f"      y: {sample['y']}")
        print(f"      features: {list(sample['features'].keys())}")
    
    # Date range query
    start_date = df['timestamp'].min().to_pydatetime()
    end_date = (df['timestamp'].min() + pd.Timedelta(days=7)).to_pydatetime()
    count_7d = collection.count_documents({
        "date": {"$gte": start_date, "$lte": end_date}
    })
    print(f"    7-day range query: {count_7d:,} documents")
    
    print("\n" + "="*60)
    print("✓ Migration complete!")
    print("="*60)
    print("\nCollection Statistics:")
    print(f"  Total documents: {final_count:,}")
    print(f"  Unique cells: {metadata_doc['total_cells']:,}")
    print(f"  Date range: {metadata_doc['date_range']['min'].date()} to {metadata_doc['date_range']['max'].date()}")
    print(f"  Storage size: {db.command('collstats', 'panel_data')['size'] / 1024 / 1024:.2f} MB")
    
    print("\n📋 Next steps:")
    print("1. Set MONGODB_URI environment variable in Render:")
    print(f"   {MONGODB_URI.replace(MONGODB_URI.split('@')[0].split('//')[1], '***:***')}")
    print("2. Add pymongo to api/requirements.txt")
    print("3. Update api/server.py to use MongoDB")
    print("4. Test locally before deploying")
    print("5. Deploy to Render")
    
    client.close()

if __name__ == "__main__":
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
