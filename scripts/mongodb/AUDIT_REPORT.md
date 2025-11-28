# MongoDB Scripts Security & Integrity Audit Report

**Date:** November 27, 2025  
**Audited Files:** `MongoControl.py`, `import_forecast_to_mongodb.py`

## 🚨 Critical Issues Found

### 1. **SECURITY: Hardcoded Database Credentials**
- **Severity:** CRITICAL
- **Location:** Both files (line ~15)
- **Issue:** MongoDB connection string with credentials hardcoded in source code
- **Impact:** Credentials exposed in version control, logs, and error messages
- **Recommendation:** 
  - IMMEDIATELY set `MONGODB_URI` environment variable
  - Remove hardcoded credentials from codebase
  - Rotate exposed credentials
  - Add `.env` to `.gitignore`

### 2. **DATA INTEGRITY: Wrong Production Collection**
- **Severity:** HIGH
- **Location:** `MongoControl.py` (lines 120, 137, 149, 161)
- **Issue:** All operations target `panel_data` collection instead of `forecast_data`
- **Impact:** 
  - Production forecast data not accessible via control panel
  - Risk of modifying wrong collection
  - Confusion between historical and forecast data
- **Current State:** 
  - Production uses `forecast_data` collection
  - Control panel targets `panel_data` (deprecated)
- **Fix Required:** Add collection selector, default to `forecast_data`

### 3. **DATA INTEGRITY: No Duplicate Prevention**
- **Severity:** HIGH  
- **Location:** `import_forecast_to_mongodb.py` (line ~175)
- **Issue:** No unique index on `(h3_cell, forecast_week, forecast_year)`
- **Impact:** Same forecast can be imported multiple times, creating duplicates
- **Consequence:**
  - Database bloat
  - Incorrect statistics (counts doubled/tripled)
  - Frontend may show duplicate layers
- **Fix Required:** Create unique compound index before insert

### 4. **DATA INTEGRITY: Missing Input Validation**
- **Severity:** MEDIUM
- **Location:** `import_forecast_to_mongodb.py` `prepare_forecast_documents()`
- **Issue:** No validation of document fields before MongoDB insert
- **Impact:**
  - Invalid probabilities (< 0 or > 1) could be inserted
  - Negative crime predictions could enter database
  - Invalid coordinates could break map rendering
  - Type mismatches cause query failures
- **Fix Required:** Add validation function before insert

### 5. **OPERATIONAL: No Transaction Support**
- **Severity:** MEDIUM
- **Location:** `import_forecast_to_mongodb.py` (line ~215)
- **Issue:** Bulk insert with `ordered=False` allows partial failures
- **Impact:**
  - Failed imports leave database in inconsistent state
  - No rollback on errors
  - Difficult to recover from partial imports
- **Fix Required:** Use MongoDB transactions for atomic imports

### 6. **OPERATIONAL: Inadequate Error Reporting**
- **Severity:** LOW
- **Location:** Both files (exception handlers)
- **Issue:** Generic exception handling loses error context
- **Impact:** Difficult to debug import failures
- **Fix Required:** Detailed error logging with row numbers

### 7. **USABILITY: Wrong Default Collection Name**
- **Severity:** MEDIUM
- **Location:** `import_forecast_to_mongodb.py` (line ~290)
- **Issue:** Default collection is `forecast_panels` but production uses `forecast_data`
- **Impact:** First-time users import to wrong collection
- **Fix Required:** Change default to `forecast_data`

## 📊 Current Database State

### Collections:
- **`forecast_data`** - Production collection (current architecture)
- **`panel_data`** - Historical panel data (deprecated for forecasts)

### Existing Forecast Panels:
- `PrepolForecast_02/` - Week 2 forecast with metadata
- `PrepolForecast_03/` - Week 3 forecast with metadata

### Schema Issues:
- No unique constraints on forecast documents
- No indexes on `crime_type` field (if exists)
- No validation rules enforced

## ✅ Recommended Fixes Priority

### IMMEDIATE (Deploy Today):
1. Add environment variable warning at script startup
2. Change MongoControl default collection to `forecast_data`
3. Add collection selector to MongoControl menu
4. Create unique index on `(h3_cell, forecast_week, forecast_year)`

### HIGH PRIORITY (This Week):
5. Add document validation function
6. Implement duplicate detection before import
7. Add integrity verification command to MongoControl
8. Fix default collection name in import script

### MEDIUM PRIORITY (Next Sprint):
9. Implement transaction support for imports
10. Add detailed error logging
11. Create database backup before destructive operations
12. Add `--validate-only` flag to test imports without writing

## 🔧 Implementation Plan

### Phase 1: Security & Collection Fixes (1-2 hours)
```python
# 1. Add to MongoControl.__init__():
self.current_collection = 'forecast_data'  # Not panel_data

# 2. Add collection switcher method
def switch_collection(self):
    # Allow user to toggle between forecast_data/panel_data

# 3. Update all methods to use self.current_collection
```

### Phase 2: Duplicate Prevention (1 hour)
```python
# Add to import_forecast_to_mongodb.py:
def create_unique_index(collection):
    collection.create_index(
        [('h3_cell', 1), ('forecast_week', 1), ('forecast_year', 1)],
        unique=True
    )
```

### Phase 3: Validation (2 hours)
```python
def validate_document(doc):
    # Check required fields
    # Validate ranges (probability 0-1, no negative predictions)
    # Check coordinates (-90 to 90 lat, -180 to 180 lon)
    # Validate week (1-53), year (2000-2100)
```

### Phase 4: Integrity Tool (1 hour)
```python
# Add to MongoControl:
def verify_forecast_integrity(self):
    # Count duplicates
    # Check for missing required fields
    # Validate value ranges
    # Report statistics
```

## 📝 Code Review Checklist

- [ ] Remove hardcoded credentials
- [ ] Add environment variable validation
- [ ] Fix default collection names
- [ ] Add unique indexes
- [ ] Implement document validation
- [ ] Add duplicate detection
- [ ] Improve error messages
- [ ] Add integrity verification tool
- [ ] Test import with existing data
- [ ] Update README with security notes

## 🎯 Testing Plan

1. **Security Test:**
   - Verify script fails gracefully without MONGODB_URI
   - Check credentials not logged in errors

2. **Integrity Test:**
   - Import same forecast twice (should fail or skip duplicates)
   - Try importing invalid probability values (should reject)
   - Verify unique index prevents duplicates

3. **Operational Test:**
   - Import forecast to forecast_data collection
   - Verify data accessible via MongoControl
   - Run integrity check command
   - Test collection switching

## 📚 Documentation Updates Needed

1. README.md - Add security warnings
2. README.md - Update default collection names
3. README.md - Document integrity verification tool
4. README.md - Add troubleshooting section
5. .github/copilot-instructions.md - Update MongoDB patterns

## ⚖️ Risk Assessment

| Issue | Current Risk | After Fix | Mitigation Time |
|-------|-------------|-----------|-----------------|
| Exposed credentials | HIGH | LOW | 5 minutes |
| Wrong collection access | HIGH | LOW | 30 minutes |
| Duplicate forecasts | HIGH | LOW | 1 hour |
| Invalid data insertion | MEDIUM | LOW | 2 hours |
| Partial import failures | MEDIUM | LOW | 2 hours |

**Overall Risk Level:** HIGH → LOW after fixes applied

## 📞 Next Steps

1. Review this audit with team
2. Prioritize fixes (Phases 1-2 critical)
3. Implement fixes following plan above
4. Test thoroughly in development
5. Deploy to production
6. Update documentation
7. Schedule follow-up audit in 1 month
