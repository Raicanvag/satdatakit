"""GeoTIFF reader.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import rasterio
import xarray as xr
from rasterio.errors import RasterioIOError

from satdatakit.core import SatelliteDataset

def read_geotiff(path: Union[str, Path], bands: Optional[List[str]] = None, **kwargs) -> SatelliteDataset:
    path = Path(path)
    try:
        with rasterio.open(path, **kwargs) as src:
            data = src.read()
            if data.ndim == 2:
                data = data[np.newaxis, ...]
            height, width = data.shape[-2:]
            transform = src.transform
            x_coords = np.arange(width) * transform.a + transform.c + transform.a / 2
            y_coords = np.arange(height) * transform.e + transform.f + transform.e / 2
            band_names = []
            for i in range(1, src.count + 1):
                tag = src.tags(i)
                name = tag.get("band_name", tag.get("BandName", f"band_{i-1}"))
                band_names.append(name)
            if bands is not None:
                indices = []
                filtered_names = []
                for b in bands:
                    if b in band_names:
                        indices.append(band_names.index(b))
                        filtered_names.append(b)
                    else:
                        warnings.warn(f"Band '{b}' not found. Skipping.", UserWarning)
                if not indices:
                    raise ValueError(f"None of the requested bands found: {bands}")
                data = data[indices]
                band_names = filtered_names
            data_array = xr.DataArray(
                data, dims=["band", "y", "x"],
                coords={"band": band_names, "y": y_coords, "x": x_coords})
            metadata = dict(src.tags())
            metadata.update({
                "driver": src.driver, "width": src.width, "height": src.height,
                "count": src.count, "dtype": str(src.dtypes[0])})
            dt = None
            for key in ["TIFFTAG_DATETIME", "acquisition_date", "date"]:
                if key in metadata:
                    try:
                        dt = datetime.strptime(metadata[key], "%Y:%m:%d %H:%M:%S")
                        break
                    except (ValueError, KeyError):
                        continue
            sensor = metadata.get("sensor")
            platform = metadata.get("platform")
            cloud_cover = None
            for key in ["cloud_cover", "CloudCover"]:
                if key in metadata:
                    try:
                        cloud_cover = float(metadata[key])
                        break
                    except (ValueError, TypeError):
                        continue
            return SatelliteDataset(
                data=data_array, bands=band_names,
                crs=src.crs.to_string() if src.crs else None,
                resolution=(abs(src.transform.a), abs(src.transform.e)),
                bounds=src.bounds, datetime=dt, sensor=sensor, platform=platform,
                cloud_cover=cloud_cover, metadata=metadata, source_format="geotiff",
                source_path=path)
    except RasterioIOError as e:
        raise RuntimeError(f"Cannot read GeoTIFF: {path} - {e}") from e
