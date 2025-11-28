# PrePol MongoDB Scripts

⚠️  **SECURITY WARNING:** Always set `MONGODB_URI` environment variable. Never commit credentials to version control.

This directory contains MongoDB operation scripts for the PrePol predictive policing system.

## 🚨 Critical Security Notice

**BEFORE USING THESE SCRIPTS:**
```powershell
# Set MongoDB credentials via environment variable (REQUIRED)
$env:MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/prepol_db"
```

Scripts will display a warning if using hardcoded credentials. This is **INSECURE** for production use.

## 📊 Current Database State

### Production Collections:
- **`forecast_data`** - Pre-computed weekly crime forecasts (PRODUCTION)
  - Auto-incremented forecast numbers (PrepolForecast_01, PrepolForecast_02, ...)
  - Sparse format: one row per H3 cell per week
  - Includes crime_type for layer filtering
  - Required indexes: `(h3_cell, forecast_week, forecast_year)` UNIQUE

- **`panel_data`** - Historical panel data (DEPRECATED for forecasts)
  - Legacy collection from old architecture
  - Use for historical analysis only

### Forecast Panel Structure:
```
panels/
├── PrepolForecast_02/
│   ├── PrepolForecast_02.parquet
│   └── PrepolForecast_02_metadata.json
├── PrepolForecast_03/
│   ├── PrepolForecast_03.parquet
│   └── PrepolForecast_03_metadata.json
└── ...
```

## 🛠️ Available Scripts

### Main Control Panel (Recommended)
- **`MongoControl.py`** - Interactive terminal interface for all operations
  - ✅ **FIXED:** Now defaults to `forecast_data` collection
  - ✅ **NEW:** Collection switcher (forecast_data/panel_data)
  - ✅ **NEW:** Integrity verification tool
  - ✅ **NEW:** Enhanced statistics and validation

### Import/Export Tools
- **`import_forecast_to_mongodb.py`** - Import forecast panels to MongoDB
  - ✅ **FIXED:** Default collection changed to `forecast_data`
  - ✅ **NEW:** Document validation before insert
  - ✅ **NEW:** Duplicate detection and prevention
  - ✅ **NEW:** Unique index creation
  - ⚠️  **BREAKING CHANGE:** Default collection is now `forecast_data` (was `forecast_panels`)

### Diagnostic Tools
- `test_mongo_connection.py` - Simple connection test
- `check_mongodb_health.py` - Comprehensive database health check

### Legacy Scripts
- `migrate_to_mongodb.py` - Migrate old parquet data (DEPRECATED)
- `drop_databases.py` - Drop databases (⚠️  USE WITH EXTREME CAUTION)

## 📖 Usage Examples

### 1. Interactive Control Panel (Recommended)
```powershell
# Set credentials first!
$env:MONGODB_URI = "your_mongodb_uri_here"

# Run control panel
python scripts/mongodb/MongoControl.py

# Available operations:
#  1. Connect to MongoDB
#  2. Disconnect
#  3-4. List databases/collections  
#  5. Switch collection (forecast_data ↔ panel_data)
#  6-8. Count/view/stats for current collection
#  9. Run custom queries
#  10-11. Insert/delete test documents
#  12. Import forecast data
#  13. Verify forecast integrity (NEW!)
#  14. Exit
```

### 2. Import Forecast Data

```powershell
cd scripts/mongodb

# List available forecasts in panels/ directory
python import_forecast_to_mongodb.py --list

# Import specific forecast to production collection
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_03

# Import all forecasts (NEW: validates and prevents duplicates)
python import_forecast_to_mongodb.py

# Overwrite existing forecast data (use cautiously)
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_03 --drop-existing

# Import to custom collection (for testing)
python import_forecast_to_mongodb.py --collection test_forecasts

# Validate only (test without importing)
python import_forecast_to_mongodb.py --forecast-name PrepolForecast_03 --validate-only
```

### 3. Verify Database Integrity

```powershell
# Via Control Panel (option 13)
python MongoControl.py
# Then select: 13. Verify Forecast Data Integrity

# Checks performed:
# - Required fields present
# - No duplicate forecasts
# - Valid probability ranges (0-1)
# - No negative predictions
# - Valid coordinates
# - Index health
# - Summary statistics
```

### 4. Query Forecast Data

```powershell
# Via Control Panel
python MongoControl.py
# 1. Connect
# 5. Switch to forecast_data (if not default)
# 9. Run custom query

# Example queries:
# High-risk cells: {"crime_probability": {"$gt": 0.5}}
# Specific week: {"forecast_week": 3, "forecast_year": 2025}
# Specific crime type: {"crime_type": "Furto"}
# All forecasts: all
```

## 🔐 Security Best Practices

### DO:
✅ Use environment variables for credentials  
✅ Rotate credentials if exposed  
✅ Review audit logs regularly  
✅ Test in development before production  
✅ Backup database before destructive operations  

### DON'T:
❌ Commit credentials to version control  
❌ Pass credentials via command-line arguments  
❌ Share credentials in chat/email  
❌ Use same credentials for dev/prod  
❌ Run scripts with production credentials on untrusted machines  

## 🐛 Known Issues & Fixes

### Issue 1: Hardcoded Credentials (CRITICAL)
**Status:** ⚠️  SECURITY RISK  
**Fix:** Set `MONGODB_URI` environment variable before running any script  
**Affected:** All scripts  

### Issue 2: Wrong Default Collection (FIXED)
**Status:** ✅ FIXED in latest version  
**Previous:** Scripts defaulted to `panel_data` or `forecast_panels`  
**Current:** Scripts default to `forecast_data` (production collection)  

### Issue 3: No Duplicate Prevention (FIXED)
**Status:** ✅ FIXED in latest version  
**Fix:** Unique index on `(h3_cell, forecast_week, forecast_year)`  
**Impact:** Same forecast can no longer be imported twice  

### Issue 4: Missing Validation (FIXED)
**Status:** ✅ FIXED in latest version  
**Fix:** Document validation before MongoDB insert  
**Validates:** Required fields, data types, value ranges, coordinates  

## 📋 Pre-Import Checklist

Before importing forecast data to production:

- [ ] Environment variable `MONGODB_URI` is set
- [ ] Forecast panel exists in `panels/PrepolForecast_XX/`
- [ ] Parquet file and metadata.json both present
- [ ] Metadata shows correct week/year
- [ ] Parquet includes `crime_type` column (for layer filtering)
- [ ] Unique index exists on forecast_data collection
- [ ] Backup of existing data (if using --drop-existing)
- [ ] Tested import in development environment first

## 🆘 Troubleshooting

### "Connection failed" Error
```powershell
# Check environment variable is set
$env:MONGODB_URI

# Verify credentials are correct
# Test with: python test_mongo_connection.py
```

### "Duplicate key error" During Import
```powershell
# This is EXPECTED if forecast already exists
# Options:
# 1. Use --drop-existing to overwrite
# 2. Import will skip duplicates (new behavior)
# 3. Delete existing forecast via MongoControl first
```

### "Collection not found" Error
```powershell
# Switch to correct collection in MongoControl (option 5)
# Or specify collection: --collection forecast_data
```

### Forecast Not Appearing in Frontend
```powershell
# 1. Verify import succeeded (check MongoControl option 6)
# 2. Ensure imported to 'forecast_data' collection (not panel_data)
# 3. Check server.py has USE_MONGODB_FORECAST = True
# 4. Verify forecast has crime_type column for layer filtering
```

## 📚 Related Documentation

- **AUDIT_REPORT.md** - Security and integrity audit findings
- **../../.github/copilot-instructions.md** - MongoDB patterns for AI agents
- **../../DEPLOYMENT.md** - Production deployment guide
- **../../README.md** - Project overview

## 🔄 Migration from Old Architecture

If you have forecasts in `forecast_panels` collection:

```powershell
# 1. Export from old collection
# Via MongoControl: Switch to forecast_panels, view sample

# 2. Re-import to forecast_data
python import_forecast_to_mongodb.py --collection forecast_data

# 3. Update server.py to use forecast_data
# (Already done in latest version)

# 4. Test frontend still works

# 5. Archive/delete old forecast_panels collection
```

## 📞 Support

For issues or questions:
1. Check AUDIT_REPORT.md for known issues
2. Review troubleshooting section above
3. Check MongoDB Atlas logs
4. Verify forecast panel structure matches specification