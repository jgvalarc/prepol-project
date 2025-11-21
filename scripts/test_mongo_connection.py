from pymongo import MongoClient

# Replace with your actual connection string
MONGODB_URI = "mongodb+srv://prepol-api:N1377Vi8pjs2fURT@prepol-cluster.ks5kzhh.mongodb.net/prepol_db?appName=prepol-cluster"

try:
    client = MongoClient(MONGODB_URI)
    # Test connection
    client.admin.command('ping')
    print("✓ Successfully connected to MongoDB Atlas!")
    
    # List databases
    print("\nDatabases:", client.list_database_names())
    
    client.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")