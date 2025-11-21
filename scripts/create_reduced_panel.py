"""
Create a reduced panel dataset for Render deployment
Only keeps 2016 data (last year) to fit within 512MB RAM limit
"""
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import prepol.config as config

print("="*60)
print("Creating Reduced Panel Data for Deployment")
print("="*60)

# Load full panel
panel_path = Path("panels/PrePol_panel_export.parquet")
print(f"\nLoading full panel from {panel_path}...")
df_full = pd.read_parquet(panel_path)

print(f"Full dataset:")
print(f"  Shape: {df_full.shape}")
print(f"  Date range: {df_full['timestamp'].min()} to {df_full['timestamp'].max()}")
print(f"  Memory: {df_full.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

# Filter to only 2016 data (last year - most relevant for demo)
print(f"\nFiltering to 2016 only...")
df_2016 = df_full[df_full['timestamp'].dt.year == 2016].copy()

print(f"\nReduced dataset (2016 only):")
print(f"  Shape: {df_2016.shape}")
print(f"  Date range: {df_2016['timestamp'].min()} to {df_2016['timestamp'].max()}")
print(f"  Memory: {df_2016.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
print(f"  Reduction: {(1 - df_2016.shape[0]/df_full.shape[0])*100:.1f}% fewer rows")

# Save reduced version
output_path = Path("panels/PrePol_panel_2016.parquet")
print(f"\nSaving to {output_path}...")
df_2016.to_parquet(output_path, index=False, compression='snappy')

print(f"✓ Saved reduced panel")
print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

print("\n" + "="*60)
print("✓ Reduced panel created successfully!")
print("="*60)
print("\nNext steps:")
print("1. Update api/server.py to load 'PrePol_panel_2016.parquet'")
print("2. Commit and push the new file")
print("3. Remove old PrePol_panel_export.parquet from git")
