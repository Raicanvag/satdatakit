# SatDataKit

**Unified satellite data analysis toolkit - one API for all Earth Observation formats.**

**Author:** Rafael Cañete Vazquez  
**License:** MIT

## Quick Start

```python
from satdatakit import read, compute_index, Pipeline

# Read any format
ds = read("sentinel2.tif")

# Compute indices
ds = compute_index(ds, "NDVI")

# Pipeline
result = (
    Pipeline()
    .read("data.tif")
    .reproject("EPSG:4326")
    .resample(30)
    .compute_index("NDVI")
    .to_geotiff("output.tif")
