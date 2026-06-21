"""Unified I/O for satellite data formats.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, List, Optional, Union

from satdatakit.core import SatelliteDataset
from satdatakit.readers import READERS

FORMAT_EXTENSIONS = {
    "geotiff": [".tif", ".tiff", ".gtiff", ".geotiff"],
    "netcdf": [".nc", ".nc4", ".netcdf", ".cdf"],
    "hdf": [".hdf", ".hdf4", ".hdf5", ".h5", ".he5"],
    "safe": [".safe"],
}

def _detect_format(path: Union[str, Path]) -> str:
    path = Path(path)
    ext = path.suffix.lower()
    for fmt, exts in FORMAT_EXTENSIONS.items():
        if ext in exts:
            return fmt
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        if header[:8] == b"\x89HDF\r\n\x1a\n":
            return "hdf"
        if header[:4] == b"CDF\x01" or header[:4] == b"CDF\x02":
            return "netcdf"
    except Exception:
        pass
    raise ValueError(f"Cannot detect format for: {path}")

def read(path: Union[str, Path], format: Optional[str] = None, 
         bands: Optional[List[str]] = None, **kwargs: Any) -> SatelliteDataset:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if format is None:
        format = _detect_format(path)
    format = format.lower()
    if format not in READERS:
        raise ValueError(f"Unsupported format: {format!r}")
    try:
        reader = READERS[format]
        return reader(path, bands=bands, **kwargs)
    except Exception as e:
        raise RuntimeError(f"Failed to read {format} file: {path}\nError: {e}") from e

def read_collection(paths: List[Union[str, Path]], format: Optional[str] = None,
                    bands: Optional[List[str]] = None, concat_dim: str = "time",
                    **kwargs: Any) -> SatelliteDataset:
    if not paths:
        raise ValueError("paths cannot be empty")
    datasets: List[SatelliteDataset] = []
    for p in paths:
        try:
            ds = read(p, format=format, bands=bands, **kwargs)
            datasets.append(ds)
        except Exception as e:
            warnings.warn(f"Skipping {p}: {e}", UserWarning)
            continue
    if not datasets:
        raise RuntimeError("No files could be read successfully.")
    first = datasets[0]
    for i, ds in enumerate(datasets[1:], 1):
        if ds.bands != first.bands:
            raise ValueError(f"Band mismatch: {first.bands} vs {ds.bands}")
        if ds.crs != first.crs:
            raise ValueError(f"CRS mismatch: {first.crs} vs {ds.crs}")
    import xarray as xr
    data_arrays = [ds.data for ds in datasets]
    stacked = xr.concat(data_arrays, dim=concat_dim)
    datetimes = [ds.datetime for ds in datasets if ds.datetime is not None]
    if datetimes and len(datetimes) == len(datasets):
        stacked = stacked.assign_coords({concat_dim: datetimes})
    return SatelliteDataset(
        data=stacked, bands=first.bands.copy(), crs=first.crs,
        resolution=first.resolution, bounds=first.bounds,
        datetime=datetimes if len(datetimes) == len(datasets) else None,
        sensor=first.sensor, platform=first.platform,
        metadata=first.metadata.copy(), source_format=first.source_format)
