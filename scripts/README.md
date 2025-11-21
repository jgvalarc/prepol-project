# Test Scripts

This directory contains utility scripts for testing various components of the PrePol system.

## Available Scripts

### check_memory.py
**Purpose**: Check memory usage of panel data loading  
**Usage**: 
```powershell
python testscripts/check_memory.py
```
**What it does**: Reports memory usage when loading the panel parquet file

### create_reduced_panel.py
**Purpose**: Create reduced panel datasets for deployment  
**Usage**:
```powershell
python testscripts/create_reduced_panel.py
```
**What it does**: Generates Q4 2016 subset (Oct-Dec) from full panel for Render deployment

### test_mongo_connection.py
**Purpose**: Simple MongoDB connection test  
**Usage**:
```powershell
python testscripts/test_mongo_connection.py
```
**What it does**: Tests basic connectivity to MongoDB Atlas

**Note**: For comprehensive MongoDB testing, use `check_mongodb_health.py` in the project root instead.

## MongoDB Testing

For complete MongoDB health checks, use the main health check script:

```powershell
# Set MongoDB URI
$env:MONGODB_URI = "your-mongodb-uri"

# Run comprehensive health check (recommended)
python check_mongodb_health.py

# Or run simple connection test
python testscripts/test_mongo_connection.py
```

See `MONGODB_HEALTH_CHECK.md` for detailed documentation.
