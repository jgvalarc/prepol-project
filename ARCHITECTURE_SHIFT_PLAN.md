# PrePol Architecture Shift: Pre-Computed Predictions with Crime Type Support

**Date**: November 24, 2025  
**Status**: Planning Phase  
**Objective**: Transform PrePol from on-demand prediction generation to pre-computed panel upload system with crime type granularity

---

## Executive Summary

PrePol is shifting from a **dynamic prediction service** (user requests date range → backend computes predictions) to a **pre-computed insights platform** (offline machine generates predictions → upload to MongoDB → frontend displays static data).

**Key Changes:**
- ✅ Add crime type support (top 5 types)
- ✅ Pre-compute 7-day forward predictions offline
- ✅ Upload predictions to MongoDB free tier (<100MB)
- ✅ Remove prediction computation from 512MB Render backend
- ✅ Enable faster, more powerful predictions without memory constraints

---

## Current vs New Architecture

### Current Architecture (On-Demand)
```
User selects date range → Frontend requests predictions
    ↓
Backend (512MB Render):
  - Loads full panel data (~150MB)
  - Loads RF model (~150MB)
  - Generates predictions in real-time
  - Converts to GeoJSON
    ↓
Frontend displays results (5-10 second delay)
```

**Constraints:**
- ❌ Render 512MB RAM limits date range and granularity
- ❌ Cannot handle crime type breakdown (would require 5× memory)
- ❌ Slow response times (5-10 seconds)
- ❌ Heavy compute load on backend

### New Architecture (Pre-Computed)
```
OFFLINE (Local Machine - Weekly):
  - Train models (one per crime type)
  - Generate 7-day predictions for all cells × crime types
  - Export to parquet (~4MB)
  - Upload to MongoDB predictions collection
    ↓
ONLINE (Render Backend - Always Available):
  - GET /api/predictions?crime_type=ROUBO&target_date=2025-11-25
  - Query MongoDB (pre-computed)
  - Return GeoJSON (<500ms)
    ↓
FRONTEND (Vercel):
  - Dropdowns: target_date (7 days), crime_type (top 5)
  - Display pre-computed predictions
  - Fast, responsive UX
```

**Benefits:**
- ✅ Backend memory: 300MB → 50MB (83% reduction)
- ✅ Response time: 5-10s → <500ms (10-20× faster)
- ✅ Enables crime type granularity (5 types)
- ✅ Predictions generated on powerful local machine (no Render limits)
- ✅ Predictable costs (no dynamic computation)

**Trade-offs:**
- ⚠️ Predictions become static (updated weekly/daily)
- ⚠️ No arbitrary date range selection
- ⚠️ Requires manual prediction generation workflow

---

## Crime Type Support Design

### Top 5 Crime Types (MongoDB Free Tier Constraint)

**Problem**: 32 unique crime types in RDO data × 12K cells × 7 days = 2.7M documents (exceeds 512MB free tier)

**Solution**: Focus on **top 5 crime types** + "OUTROS" aggregate category

```python
TOP_CRIME_TYPES = [
    'ROUBO',              # Robbery (highest frequency)
    'FURTO',              # Theft
    'LESAO_CORPORAL',     # Bodily injury
    'AMEACA',             # Threat
    'OUTROS'              # Aggregate of remaining 27 types
]
```

**Coverage**: Top 5 types cover ~80-90% of all crimes in dataset

**Storage Impact**:
- 12,000 cells × 7 days × 5 types = **420,000 predictions**
- Avg document size: ~100 bytes
- **Total storage**: ~87 MB (data + indexes)
- **MongoDB free tier usage**: 17% of 512MB ✅

### Hour Interval Decision

**Excluded from MVP**: Hour interval breakdown (00-04h, 04-08h, etc.)

**Reasoning**:
- 6 intervals × 5 crime types = 30 combinations
- Would increase storage to ~520 MB (exceeds free tier by 8MB)
- Can be added later with paid MongoDB tier

---

## Data Pipeline Changes

### 1. H3Discretization Updates

**Current**: Aggregates `(h3_cell, date)` → total crime count

**New**: Preserve crime type dimension `(h3_cell, date, crime_type)`

```python
# Before (current aggregation)
df_h3 = df_events.groupby(['h3_cell', 'timestamp']).size().reset_index(name='y')
# Result: 14.5M rows (12K cells × 1,200 days)

# After (with crime types)
df_h3 = df_events.groupby([
    'h3_cell', 
    'timestamp', 
    'RUBRICA'  # Crime type
]).size().reset_index(name='y')
# Result: 72.5M rows (12K cells × 1,200 days × 5 types)

# Map to top 5 + OUTROS
df_h3['crime_type'] = df_h3['RUBRICA'].apply(
    lambda x: x if x in TOP_CRIME_TYPES[:4] else 'OUTROS'
)
```

**Critical**: Must maintain complete grid including **zero-crime observations**

### 2. Complete Grid Creation (Including Zeros)

**Why Zeros Matter**: Training only on `y > 0` creates severe prediction bias

```python
# Create complete spatio-temporal grid
unique_cells = df_h3['h3_cell'].unique()  # ~12,000 cells
all_dates = pd.date_range('2013-01-01', '2016-12-31', freq='D')
crime_types = TOP_CRIME_TYPES

# Cartesian product: ALL combinations
complete_grid = pd.MultiIndex.from_product(
    [unique_cells, all_dates, crime_types],
    names=['h3_cell', 'date', 'crime_type']
).to_frame(index=False)
# Result: 12K × 1,461 × 5 = 87.7M rows

# Merge with actual crimes
df_crimes = df_events.groupby(['h3_cell', 'date', 'crime_type']).size()
df_panel = complete_grid.merge(df_crimes, how='left')
df_panel['y'] = df_panel['y'].fillna(0).astype(int)  # Explicit zeros

# ✅ Complete panel with zero-crime observations preserved
```

**Validation**: Zero-crime observations represent ~85-90% of data (realistic for crime data)

### 3. Storage Optimization Strategy

**Challenge**: 87.7M rows × 100 bytes = 8.8 GB raw data

**Solution**: Parquet compression + sparse storage

```python
# Approach 1: Parquet compression (RECOMMENDED)
df_panel.to_parquet(
    'panel_complete.parquet',
    compression='snappy',
    engine='pyarrow'
)
# Result: 8.8 GB → ~2.5 GB (71% compression)

# Approach 2: Per-crime-type storage (for memory-efficient training)
for crime_type in TOP_CRIME_TYPES:
    df_type = df_panel[df_panel['crime_type'] == crime_type]
    df_type.to_parquet(f'panel_{crime_type}.parquet')
    # Result: 5 files × 500 MB = 2.5 GB total
```

---

## Model Training Strategy

### Option A: Single Multi-Output Model
- One RandomForest with 5 outputs (one per crime type)
- Training time: ~15.5 minutes
- Memory: 10 GB peak
- ❌ Not recommended: Complex, harder to update individual types

### Option B: Sequential Training (5 Separate Models)
- Train one model per crime type sequentially
- Training time: ~19 minutes
- Memory: 10 GB peak (one type at a time)
- ⚠️ Slower but safer for memory

### Option C: Optimized Lightweight Models (RECOMMENDED)
- 5 separate models with reduced complexity
- Training time: **~4.7 minutes per type** = 23.5 minutes total (parallel 2×: ~12 minutes)
- Memory: 10 GB peak (safe for 16GB machine)

```python
# Per crime type model configuration
RandomForestRegressor(
    n_estimators=50,      # Reduced from 100
    max_depth=12,         # Reduced from 15
    min_samples_split=10,
    min_samples_leaf=5,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1             # Use all 12 cores
)
```

**Performance Trade-off**:
- R² drops from 0.91 → 0.85-0.88 (still highly accurate)
- Models remain lightweight: 150 MB each × 5 = 750 MB total
- Faster training enables frequent updates

### Memory-Efficient Training Pattern

```python
# Train one crime type at a time to manage memory
for crime_type in TOP_CRIME_TYPES:
    print(f"Training {crime_type}...")
    
    # Load only this crime type (reduces memory by 5×)
    df_type = pd.read_parquet(
        'panel_complete.parquet',
        filters=[('crime_type', '=', crime_type)]
    )  # ~1.5 GB in RAM
    
    # Train model
    model = RandomForestRegressor(n_estimators=50, max_depth=12, n_jobs=-1)
    model.fit(df_type[feature_cols], df_type['y'])
    
    # Save and clear memory
    joblib.dump(model, f'rf_model_{crime_type}.joblib')
    del df_type, model
    gc.collect()

# Peak RAM: ~3 GB (well within 16 GB available)
```

---

## Time Estimates (Based on Benchmark)

**Machine Specs**: AMD Ryzen 6C/12T @ 3.6GHz, 16GB RAM, HDD

| Phase | Duration | Notes |
|-------|----------|-------|
| Data Loading & Preprocessing | 10 min | Load 72M rows, sparse storage |
| Model Training (5 models, optimized) | 4.7 min | Sequential, lightweight |
| Model Evaluation | 1.5 min | Test 5 models |
| Save Models | 0.5 min | 750 MB total |
| Generate 7-Day Predictions | 1.7 min | 420K predictions |
| Export to Parquet | 0.15 min | ~4 MB file |
| **TOTAL (First-Time)** | **~19 min** | End-to-end pipeline |

**Weekly Prediction Refresh** (using cached models):
- Load 5 models: 15 seconds
- Generate predictions: 100 seconds
- Export: 9 seconds
- **Total: ~2 minutes**

**Monthly Re-training**:
- Incremental data prep: 5 minutes
- Re-train 5 models: 4.7 minutes
- **Total: ~11.5 minutes**

---

## MongoDB Schema Design (Free Tier Optimized)

### Collection: `prepol_db.predictions`

```javascript
{
  _id: ObjectId("..."),
  h3_cell: "89a6c462c3fffff",           // H3 cell identifier
  prediction_date: ISODate("2025-11-24"), // When prediction was generated
  target_date: ISODate("2025-11-25"),     // Date being predicted (1-7 days out)
  crime_type: "ROUBO",                    // One of top 5 types
  
  // Prediction outputs
  predicted_count: 0.85,                  // Expected crime count
  crime_probability: 0.57,                // P(≥1 crime) = 1 - e^(-λ)
  risk_level: "Medium",                   // Low/Medium/High category
  
  // Metadata
  coords: {lat: -8.05, lon: -34.9},      // H3 centroid coordinates
  model_version: "v1.0_20251124"          // Model tracking
}
```

**Indexes**:
```javascript
// Query optimization
db.predictions.createIndex({target_date: 1, crime_type: 1}, {name: 'query_idx'})
db.predictions.createIndex({h3_cell: 1, target_date: 1}, {name: 'cell_date_idx'})

// TTL for automatic cleanup (7 days after prediction_date)
db.predictions.createIndex({prediction_date: 1}, {expireAfterSeconds: 604800, name: 'ttl_idx'})
```

**Storage Breakdown**:
- Documents: 420,000 × ~100 bytes = 42 MB
- Indexes: ~45 MB
- **Total: ~87 MB** (17% of 512MB free tier)

---

## Backend API Changes

### Remove from `api/server.py`:
- ❌ `POST /api/predict` endpoint (no more on-demand predictions)
- ❌ Model loading (`rf_model`, `joblib.load()`)
- ❌ Panel data loading for prediction
- ❌ Feature preparation logic
- ❌ Prediction computation

### Keep:
- ✅ `GET /api/health` (update to check predictions collection)
- ✅ `GET /api/metadata` (add prediction metadata)

### Add New Endpoint:

```python
@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """Serve pre-computed predictions with filtering.
    
    Query parameters:
    - target_date: Date to get predictions for (default: tomorrow)
    - crime_type: Filter by crime type (default: all types)
    - min_probability: Minimum probability threshold (default: 0.05)
    """
    target_date = request.args.get('target_date', 
                                   (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    crime_type = request.args.get('crime_type', None)
    min_prob = float(request.args.get('min_probability', 0.05))
    
    # Build MongoDB query
    query = {'target_date': datetime.strptime(target_date, '%Y-%m-%d')}
    if crime_type and crime_type != 'ALL':
        query['crime_type'] = crime_type
    
    # Query MongoDB (fast, pre-computed)
    predictions = list(mongo_collection.find(query))
    predictions = [p for p in predictions if p['crime_probability'] >= min_prob]
    
    # Convert to GeoJSON
    geojson = convert_to_geojson(predictions)
    summary = calculate_summary(predictions)
    
    return jsonify({'geojson': geojson, 'summary': summary})
```

**Performance**: <500ms response (vs 5-10s before)

---

## Frontend Changes

### Remove from `CrimeMap.jsx`:
- ❌ Date range pickers (start_date, end_date)
- ❌ POST request to `/api/predict`
- ❌ "Generate Predictions" button

### Add:
- ✅ Target date dropdown (7 available days)
- ✅ Crime type selector (top 5 types + "ALL")
- ✅ GET request to `/api/predictions`

```jsx
function CrimeMap() {
  const [targetDate, setTargetDate] = useState(tomorrow);
  const [crimeType, setCrimeType] = useState('ALL');
  const [availableDates, setAvailableDates] = useState([]);
  const [crimeTypes, setCrimeTypes] = useState([]);
  
  // Fetch metadata on mount
  useEffect(() => {
    fetch(`${API_URL}/api/metadata`)
      .then(res => res.json())
      .then(data => {
        setAvailableDates(data.target_dates);
        setCrimeTypes(['ALL', ...data.crime_types]);
      });
  }, []);
  
  // Fetch predictions when filters change
  useEffect(() => {
    const params = new URLSearchParams({
      target_date: targetDate,
      crime_type: crimeType,
      min_probability: '0.05'
    });
    
    fetch(`${API_URL}/api/predictions?${params}`)
      .then(res => res.json())
      .then(data => setPredictionData(data));
  }, [targetDate, crimeType]);
  
  return (
    <Box>
      <FormControl>
        <Select value={targetDate} onChange={e => setTargetDate(e.target.value)}>
          {availableDates.map(date => <MenuItem key={date} value={date}>{date}</MenuItem>)}
        </Select>
      </FormControl>
      
      <FormControl>
        <Select value={crimeType} onChange={e => setCrimeType(e.target.value)}>
          {crimeTypes.map(type => <MenuItem key={type} value={type}>{type}</MenuItem>)}
        </Select>
      </FormControl>
      
      <MapContainer>{/* Display predictions */}</MapContainer>
    </Box>
  );
}
```

---

## Prediction Upload Script

**File**: `scripts/upload_predictions_freetier.py`

```python
from pymongo import MongoClient, ASCENDING
import pandas as pd
from pathlib import Path

def upload_predictions():
    # Load predictions
    df = pd.read_parquet('predictions_export/predictions_7day_latest.parquet')
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    db = client.prepol_db
    collection = db.predictions
    
    # Clear old predictions
    collection.delete_many({'prediction_date': {'$lt': cutoff_date}})
    
    # Convert to documents
    documents = df.to_dict('records')
    
    # Bulk insert (batches of 10K)
    for i in range(0, len(documents), 10000):
        batch = documents[i:i+10000]
        collection.insert_many(batch, ordered=False)
    
    # Create indexes
    collection.create_index([('target_date', ASCENDING), ('crime_type', ASCENDING)])
    collection.create_index([('h3_cell', ASCENDING), ('target_date', ASCENDING)])
    collection.create_index([('prediction_date', ASCENDING)], expireAfterSeconds=604800)
    
    # Store metadata
    db.metadata.replace_one(
        {'_id': 'predictions_info'},
        {
            '_id': 'predictions_info',
            'prediction_date': df['prediction_date'].iloc[0],
            'target_dates': sorted(df['target_date'].unique()),
            'crime_types': sorted(df['crime_type'].unique()),
            'total_predictions': len(df),
            'model_version': MODEL_VERSION
        },
        upsert=True
    )
    
    print(f"✓ Uploaded {len(documents):,} predictions")
    print(f"  Storage: {get_collection_size_mb(collection):.2f} MB")
```

---

## New Workflow

### Weekly Production Cycle

```
Monday 8:00 AM (Local Machine):
├─ 8:00: Generate 7-day predictions (~2 min)
├─ 8:02: Export to parquet (~4 MB file)
├─ 8:02: Upload to MongoDB (~5 min network time)
└─ 8:07: Predictions live on frontend

User Experience:
├─ Visits prepol.vercel.app
├─ Sees predictions for next 7 days (Mon-Sun)
├─ Filters by crime type (ROUBO, FURTO, etc.)
└─ Fast, responsive map (<500ms load)
```

### Monthly Model Update

```
First Monday of Month (If new data available):
├─ Load new RDO data
├─ Re-run H3Discretization (~5 min)
├─ Re-train 5 models (~12 min)
├─ Generate predictions (~2 min)
├─ Upload to MongoDB (~5 min)
└─ Total: ~24 minutes (can run overnight)
```

---

## Implementation Checklist

### Phase 1: Data Pipeline Updates
- [ ] Update `H3Discretization.ipynb` to preserve crime types
- [ ] Add complete grid creation (including zeros)
- [ ] Implement sparse storage with parquet compression
- [ ] Add crime type mapping (top 5 + OUTROS)
- [ ] Validate panel completeness (85-90% zeros expected)

### Phase 2: Model Training Updates
- [ ] Create `scripts/analyze_crime_types.py` (determine top 5)
- [ ] Update `ModelTraining.ipynb` for per-crime-type training
- [ ] Implement memory-efficient sequential training
- [ ] Test optimized hyperparameters (n_estimators=50, max_depth=12)
- [ ] Save 5 separate models with metadata

### Phase 3: Prediction Generation
- [ ] Create `notebooks/GeneratePredictions_FreeTier.ipynb`
- [ ] Implement 7-day forward prediction logic
- [ ] Add probability calculation (Poisson distribution)
- [ ] Add risk level categorization
- [ ] Export to parquet format

### Phase 4: MongoDB Setup
- [ ] Create `predictions` collection with schema
- [ ] Add compound indexes for query optimization
- [ ] Add TTL index for automatic cleanup
- [ ] Create metadata collection for prediction info
- [ ] Test query performance (<100ms target)

### Phase 5: Upload Script
- [ ] Create `scripts/upload_predictions_freetier.py`
- [ ] Implement bulk insert with batching
- [ ] Add validation checks (document count, storage size)
- [ ] Add metadata tracking
- [ ] Test with sample predictions

### Phase 6: Backend API Refactor
- [ ] Remove POST `/api/predict` endpoint
- [ ] Add GET `/api/predictions` endpoint
- [ ] Update `/api/metadata` for prediction info
- [ ] Update `/api/health` to check predictions collection
- [ ] Remove model loading logic
- [ ] Test API performance (<500ms)

### Phase 7: Frontend Updates
- [ ] Remove date range pickers from `CrimeMap.jsx`
- [ ] Add target date dropdown (7 days)
- [ ] Add crime type selector (top 5 + ALL)
- [ ] Update prediction fetching to use GET endpoint
- [ ] Update map popups with crime type info
- [ ] Test UI/UX flow

### Phase 8: Deployment
- [ ] Deploy backend to Render (test prediction serving)
- [ ] Deploy frontend to Vercel (test filters)
- [ ] Run end-to-end smoke test
- [ ] Monitor performance metrics
- [ ] Document new workflow in DEPLOYMENT.md

### Phase 9: Documentation
- [ ] Update `README.md` with new architecture
- [ ] Update `DEPLOYMENT.md` with prediction upload process
- [ ] Update `.github/copilot-instructions.md`
- [ ] Create `docs/PREDICTION_PIPELINE.md`
- [ ] Add workflow diagrams

---

## Key Insights & Decisions

### 1. Training on Complete Data (Including Zeros)
**Decision**: Train on complete spatio-temporal grid with explicit zeros

**Rationale**:
- Zero crimes are **real observations**, not missing data
- Training only on `y > 0` creates severe prediction bias
- Model needs to learn "what no-crime looks like"
- Proper probability calibration requires zero observations

**Implementation**: Complete grid creation ensures ~85-90% zero values (realistic for crime data)

### 2. MongoDB Free Tier Optimization
**Challenge**: 32 crime types × 12K cells × 7 days = 2.7M docs (exceeds 512MB)

**Solution**: Top 5 crime types + "OUTROS" aggregate
- Covers 80-90% of crime events
- Results in 420K documents (~87 MB with indexes)
- Leaves room for growth within free tier

### 3. Training Strategy Selection
**Chosen**: Strategy C (Optimized Lightweight Models)

**Rationale**:
- Balances training time (~5 min/model) with accuracy (R² ~0.85-0.88)
- Memory-efficient: Sequential training with per-type loading
- Enables independent model updates (don't retrain all 5 for one type)
- Lightweight models (150 MB each) easier to version/deploy

### 4. Hour Interval Exclusion
**Decision**: Exclude hour interval breakdown from MVP

**Rationale**:
- 6 intervals × 5 types = 30 combinations (exceeds free tier)
- Can be added later with paid MongoDB tier ($9/month M2)
- Crime type alone provides significant value

---

## Future Enhancements

### Short-term (Next 3 months)
1. **Automated prediction refresh**: Cron job for weekly generation
2. **Model performance monitoring**: Track prediction accuracy vs actual crimes
3. **User feedback collection**: Crime type usage analytics
4. **Mobile-responsive UI**: Optimize for smaller screens

### Medium-term (Next 6 months)
1. **Hour interval support**: Upgrade to MongoDB M2 tier
2. **Historical prediction tracking**: Store past predictions for analysis
3. **A/B testing framework**: Test new models before deployment
4. **Real-time data ingestion**: Auto-update when new RDO data available

### Long-term (Next 12 months)
1. **Multi-city support**: Expand beyond Recife
2. **Ensemble models**: Combine multiple algorithms
3. **External features**: Weather, events, demographics
4. **API rate limiting**: Protect against abuse
5. **Premium tier**: Advanced analytics for law enforcement

---

## Success Metrics

### Technical Performance
- ✅ API response time: <500ms (target: 200ms)
- ✅ Backend memory usage: <100MB (target: 50MB)
- ✅ MongoDB storage: <100MB (target: 87MB)
- ✅ Prediction refresh time: <2 minutes
- ✅ Model training time: <20 minutes

### Prediction Quality
- ✅ Per-crime-type R²: >0.85
- ✅ Overall accuracy: >85%
- ✅ False positive rate: <20%
- ✅ Coverage: Top 5 types cover >80% of crimes

### User Experience
- ✅ Map load time: <2 seconds
- ✅ Filter change response: <500ms
- ✅ Available crime types: 5 categories
- ✅ Prediction window: 7 days forward

---

## Risk Assessment & Mitigation

### Risk 1: MongoDB Storage Limits
**Probability**: Low  
**Impact**: High  
**Mitigation**: 
- Current design uses 17% of free tier
- Can reduce to top 3 crime types if needed (50% storage reduction)
- Upgrade to M2 tier ($9/month) if necessary

### Risk 2: Stale Predictions
**Probability**: Medium  
**Impact**: Medium  
**Mitigation**:
- TTL index auto-deletes after 7 days
- "Last Updated" timestamp visible in UI
- Weekly refresh cadence documented
- Alerts if upload fails

### Risk 3: Model Performance Degradation
**Probability**: Medium  
**Impact**: High  
**Mitigation**:
- Quarterly retraining with new data
- Monitor actual vs predicted crime rates
- A/B test new models before deployment
- Version tracking for rollback capability

### Risk 4: Upload Failures
**Probability**: Low  
**Impact**: Medium  
**Mitigation**:
- Retry logic in upload script
- Validation checks before/after upload
- Keep backup of previous predictions
- Alert on upload failure

---

## Conclusion

This architecture shift transforms PrePol into a **scalable, performant predictive policing platform** that:

1. **Removes memory constraints** by moving computation offline
2. **Adds crime type granularity** (5 categories) for actionable insights
3. **Improves user experience** with <500ms response times
4. **Fits MongoDB free tier** (87 MB of 512 MB)
5. **Maintains prediction validity** through complete training data
6. **Enables weekly updates** in ~2 minutes

The system is now positioned for growth while maintaining operational efficiency within free-tier constraints.

**Next Step**: Begin implementation with Phase 1 (Data Pipeline Updates)
