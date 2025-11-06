# RUMBO.AI - Driver ML Pipeline

Complete ML pipeline for driver behavior analysis, clustering, and scoring using Scania Fleet Management API data.

## 📋 Overview

This pipeline consists of 4 main stages:

1. **Data Extraction** - Fetch driver evaluation data from Scania API
2. **Feature Processing** - Calculate safety, efficiency, and compliance features
3. **Clustering** - Apply K-Means to segment drivers into behavioral groups
4. **Score Generation** - Generate final JSON with driver scores for API

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set Scania API token
export SCANIA_API_TOKEN='your_bearer_token_here'
```

### Run Complete Pipeline

```bash
# Run full pipeline (auto-dates: last 30 days)
python src/run_pipeline.py

# Specify date range
python src/run_pipeline.py \
  --start-date 202510210000 \
  --end-date 202510310000

# Skip extraction (use existing raw data)
python src/run_pipeline.py --skip-extraction
```

### Outputs

After successful execution, you'll find:

```
data/
  ├── raw_driver_trips.json       # Raw Scania API response
  ├── trips_processed.csv         # Trip-level features
  ├── drivers_features.csv        # Driver-level aggregated features
  ├── drivers_clustered.csv       # Drivers with cluster labels
  └── driver_scores.json          # ⭐ Final output for API

models/
  └── driver_clustering_model.pkl # Trained K-Means model

outputs/
  ├── clustering_report.txt       # Detailed clustering analysis
  ├── optimal_k_analysis.png      # Elbow method visualization
  ├── clusters_pca.png            # PCA cluster visualization
  └── cluster_distribution.png    # Driver distribution chart
```

---

## 📦 Individual Scripts

### 1. Extract Scania Data

Connects to Scania Fleet Management API and fetches Driver Evaluation Report.

**Usage:**

```bash
python src/extract_scania_data.py \
  --start-date 202510210000 \
  --end-date 202510310000 \
  --output data/raw_driver_trips.json
```

**Parameters:**
- `--start-date`: Start date in format `YYYYMMDDHHMM` (default: 30 days ago)
- `--end-date`: End date in format `YYYYMMDDHHMM` (default: now)
- `--drivers`: (optional) Specific driver IDs to fetch
- `--output`: Output file path

**Environment Variables:**
- `SCANIA_API_TOKEN`: Required Bearer token for authentication

**Output:**
- `data/raw_driver_trips.json` - Raw API response with all trip data
- `data/extraction_metadata.json` - Extraction summary
- `data/scania_extraction.log` - Detailed logs

---

### 2. Process Features

Processes raw Scania data and calculates driver features and composite scores.

**Usage:**

```bash
python src/process_features.py \
  --input data/raw_driver_trips.json \
  --output data/drivers_features.csv
```

**Parameters:**
- `--input`: Input raw JSON file (default: `data/raw_driver_trips.json`)
- `--output`: Output CSV file (default: `data/drivers_features.csv`)

**Features Calculated:**

**Safety:**
- `harsh_braking_per_100km_avg`
- `harsh_acceleration_per_100km_avg`
- `speeding_percentage_avg`
- `brake_score_avg`

**Efficiency:**
- `fuel_per_100km_avg`
- `idle_time_percentage_avg`
- `cruise_control_usage_pct_avg`
- `anticipation_score_avg`

**Compliance:**
- `total_distance_km`
- `total_trips`
- `avg_speed_kmh`

**Composite Scores:**
- `safety_score` = weighted combination of safety features
- `efficiency_score` = weighted combination of efficiency features
- `compliance_score` = weighted combination of compliance features
- `driver_score_base` = 0.4×safety + 0.35×efficiency + 0.25×compliance

**Output:**
- `data/trips_processed.csv` - Trip-level features
- `data/drivers_features.csv` - Driver-level aggregated features
- `data/processing_report.txt` - Processing summary

---

### 3. Train Clustering

Trains K-Means clustering model to segment drivers into behavioral groups.

**Usage:**

```bash
# Auto-detect optimal K (recommended)
python src/train_driver_clustering.py \
  --input data/drivers_features.csv \
  --output data/drivers_clustered.csv

# Specify K manually
python src/train_driver_clustering.py \
  --input data/drivers_features.csv \
  --output data/drivers_clustered.csv \
  --k 3
```

**Parameters:**
- `--input`: Input driver features CSV
- `--output`: Output clustered drivers CSV
- `--k`: Number of clusters (optional, auto-detects if not specified)

**Clustering Features:**
- `harsh_braking_per_100km_avg`
- `fuel_per_100km_avg`
- `idle_time_percentage_avg`
- `scania_driver_support_score_avg`
- `speeding_percentage_avg`

**Expected Clusters:**

**Cluster 0 - Conservadores:**
- High safety scores (85-95)
- Low harsh braking (<0.2/100km)
- Optimal fuel efficiency

**Cluster 1 - Equilibrados:**
- Medium safety scores (70-85)
- Moderate harsh braking (0.2-0.5/100km)
- Good fuel efficiency

**Cluster 2 - Agresivos:**
- Lower safety scores (60-70)
- High harsh braking (>0.5/100km)
- Improvable fuel efficiency

**Output:**
- `data/drivers_clustered.csv` - Drivers with cluster labels
- `models/driver_clustering_model.pkl` - Trained model (for inference)
- `outputs/clustering_report.txt` - Detailed cluster analysis
- `outputs/optimal_k_analysis.png` - Elbow method chart
- `outputs/clusters_pca.png` - PCA visualization
- `outputs/cluster_distribution.png` - Driver distribution

---

### 4. Generate Driver Scores JSON

Generates final `driver_scores.json` with km-balanced scores ready for API consumption.

**Usage:**

```bash
python src/generate_driver_scores_json.py \
  --input data/drivers_clustered.csv \
  --output data/driver_scores.json
```

**Parameters:**
- `--input`: Input clustered drivers CSV
- `--output`: Output JSON file path

**Score Adjustment:**

Applies kilometer balancing to promote equitable workload distribution:

```
km_balance = mean_fleet_km - driver_km
driver_score_adjusted = driver_score_base + (0.15 × km_balance_scaled)
```

**JSON Structure:**

```json
{
  "generated_at": "2025-11-06T00:00:00",
  "version": "1.0",
  "data_source": "Scania Driver Evaluation Report v2",
  "drivers": [
    {
      "driver_id": "abc123",
      "driver_name": "Ana Silva",
      "cluster": 0,
      "cluster_name": "Conservador",
      "safety_score": 95.0,
      "efficiency_score": 92.0,
      "compliance_score": 94.0,
      "overall_score": 94.0,
      "total_trips": 24,
      "km_accumulated": 18000.0,
      "harsh_braking_avg": 0.05,
      "fuel_consumption_avg": 24.8,
      "co2_per_km": 0.665,
      ...
    }
  ],
  "fleet_statistics": {
    "total_drivers": 38,
    "avg_overall_score": 78.5,
    "cluster_distribution": {
      "Conservador": 16,
      "Equilibrado": 18,
      "Agresivo": 4
    },
    ...
  }
}
```

**Output:**
- `data/driver_scores.json` - ⭐ **Final output for API**
- `data/driver_scores_report.txt` - Human-readable summary

---

## 🔧 Configuration

### Clustering Features

To modify which features are used for clustering, edit `CLUSTERING_FEATURES` in `train_driver_clustering.py`:

```python
CLUSTERING_FEATURES = [
    'harsh_braking_per_100km_avg',
    'fuel_per_100km_avg',
    'idle_time_percentage_avg',
    'scania_driver_support_score_avg',
    'speeding_percentage_avg'
]
```

### Score Weights

To adjust composite score weights, modify the formulas in `process_features.py`:

```python
# Safety score components
safety_score = (
    0.40 * harsh_braking_norm +
    0.30 * speeding_norm +
    0.20 * brake_score_norm +
    0.10 * harsh_accel_norm
)

# Overall driver score
driver_score_base = (
    0.40 * safety_score +
    0.35 * efficiency_score +
    0.25 * compliance_score
)
```

### Kilometer Balancing

To adjust the km balance adjustment factor, modify `ALPHA` in `generate_driver_scores_json.py`:

```python
ALPHA = 0.15  # Weight for kilometer balancing adjustment
```

---

## 📊 Understanding the Output

### Cluster Interpretation

Use the clustering report (`outputs/clustering_report.txt`) to understand:
- How many drivers in each cluster
- Average characteristics per cluster
- Silhouette Score (quality metric, target: >0.25)

### Driver Scores

Each driver receives 4 scores:

1. **Safety Score (0-100)**: Lower harsh braking, speeding, aggressive acceleration
2. **Efficiency Score (0-100)**: Lower fuel consumption, idle time; higher cruise control usage
3. **Compliance Score (0-100)**: Experience (km driven), consistency (trip count)
4. **Overall Score (0-100)**: Weighted combination + km balance adjustment

### Fleet Statistics

`driver_scores.json` includes fleet-wide metrics:
- Average scores by category
- Cluster distribution
- Performance distribution (excellent/good/average/needs improvement)
- CO2 metrics
- Top performer identification

---

## 🐛 Troubleshooting

### API Connection Issues

```bash
# Check if token is set
echo $SCANIA_API_TOKEN

# Test API connection
python src/extract_scania_data.py --help
```

### Missing Data

If extraction returns no trips:
- Verify date range (no data on weekends/holidays)
- Check driver activity in Scania portal
- Ensure vehicles have telemetry enabled

### Clustering Issues

If Silhouette Score is low (<0.2):
- Try different K values manually: `--k 2` or `--k 4`
- Check if you have enough drivers (minimum 20)
- Review feature distributions in `drivers_features.csv`

### File Not Found

Ensure you run scripts in order:
1. `extract_scania_data.py` → creates `raw_driver_trips.json`
2. `process_features.py` → creates `drivers_features.csv`
3. `train_driver_clustering.py` → creates `drivers_clustered.csv`
4. `generate_driver_scores_json.py` → creates `driver_scores.json`

Or simply use `run_pipeline.py` to run all steps automatically.

---

## 📈 Next Steps

### For Hackathon

1. ✅ Run pipeline with Scania data (last 30 days)
2. ✅ Review `driver_scores.json`
3. Deploy to API backend (NestJS)
4. Build frontend (React + Vite) to display:
   - Driver rankings
   - Cluster distribution
   - Route recommendation interface

### Post-Hackathon Evolution

See `RUMBO.md` section "🚀 EVOLUCIÓN POST-HACKATHON" for:
- Supervised learning implementation
- Outcome tracking (ETA, incidents, fuel)
- Continuous model retraining
- Predictive analytics

---

## 📚 Additional Resources

- **RUMBO.md** - Complete system architecture and ML roadmap
- **notebooks/** - Jupyter notebooks for exploratory analysis
- **evaluation_driver.json** - Scania API field reference

---

## 💬 Support

For issues or questions:
1. Check logs in `data/*.log`
2. Review processing reports in `data/*_report.txt`
3. Examine visualizations in `outputs/*.png`

---

**Built for Hackathon HG 2025**
**Team: RUMBO.AI**
