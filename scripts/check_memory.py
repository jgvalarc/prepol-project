"""
Quick script to check memory usage of loading model and panel data
"""
import sys
import psutil
import pandas as pd
import joblib
from pathlib import Path

def get_memory_mb():
    """Get current process memory in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

print("="*60)
print("Memory Usage Analysis")
print("="*60)

# Baseline
baseline = get_memory_mb()
print(f"\nBaseline (Python + imports): {baseline:.1f} MB")

# Load model
model_path = Path("model/rf_crime_model_20251119_1852.joblib")
print(f"\nLoading model from {model_path.name}...")
rf_model = joblib.load(model_path)
after_model = get_memory_mb()
print(f"After model load: {after_model:.1f} MB (delta: +{after_model - baseline:.1f} MB)")

# Load panel
panel_path = Path("panels/PrePol_panel_2016Q4.parquet")
print(f"\nLoading panel from {panel_path.name}...")
df_panel = pd.read_parquet(panel_path)
after_panel = get_memory_mb()
print(f"After panel load: {after_panel:.1f} MB (delta: +{after_panel - after_model:.1f} MB)")

print(f"\n{'='*60}")
print(f"TOTAL MEMORY USAGE: {after_panel:.1f} MB")
print(f"Render Free Tier Limit: 512 MB")
print(f"Memory Available: {512 - after_panel:.1f} MB")

if after_panel > 512:
    print(f"\n⚠️  WARNING: Exceeds Render free tier by {after_panel - 512:.1f} MB")
else:
    print(f"\n✓ Within Render free tier limit")

print(f"\nPanel data shape: {df_panel.shape}")
print(f"Panel memory (DataFrame.memory_usage): {df_panel.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
print("="*60)
