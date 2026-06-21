<p align="center">
  <img src="satdatakit_banner.png" alt="SatDataKit Banner" width="100%">
</p>

<h1 align="center">SatDataKit</h1>

<p align="center">
  <strong>Unified satellite data analysis toolkit — one API for all Earth Observation formats.</strong>
</p>

<p align="center">
  <a href="https://github.com/raicanvag/satdatakit/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/EO-GeoTIFF%20%7C%20NetCDF%20%7C%20HDF%20%7C%20SAFE-orange.svg" alt="Formats">
</p>

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

#Installation

# Docker (recommended)
docker-compose up --build satdatakit

# Or Conda
conda env create -f environment.yml
conda activate satdatakit
pip install -e ".[dev]"

#Features
#Unified API: One read() for GeoTIFF, NetCDF, HDF, SAFE
#Spectral Indices: NDVI, NDWI, EVI, SAVI, and more
#Pipeline API: Fluent, chainable operations
#Time Series: Stack multiple scenes automatically