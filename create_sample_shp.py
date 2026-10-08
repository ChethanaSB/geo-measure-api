import geopandas as gpd
from pathlib import Path
import zipfile
import shutil
import os
from shapely.geometry import Polygon

sample_shp_dir = Path('sample_data/sample_shp')
sample_zip = Path('sample_data/sample.zip')

if sample_shp_dir.exists():
    shutil.rmtree(sample_shp_dir)
sample_shp_dir.mkdir(parents=True, exist_ok=True)

# Create a simple polygon GeoDataFrame
poly = Polygon([
    (-122.366278, 37.818844),
    (-122.365248, 37.819267),
    (-122.365640, 37.819861),
    (-122.366669, 37.819429),
    (-122.366278, 37.818844)
])
gdf = gpd.GeoDataFrame({'name': ['Test Polygon']}, geometry=[poly], crs="EPSG:4326")

# Save as shapefile
gdf.to_file(sample_shp_dir / 'sample.shp', engine='pyogrio')

# Zip it up
with zipfile.ZipFile(sample_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(sample_shp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, sample_shp_dir)
            zipf.write(file_path, arcname)

print('Sample shapefile zip created successfully.')
