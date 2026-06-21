"""Dask extension for SatDataKit — parallel processing.

Usage:
    from satdatakit.extensions.dask_ext import enable_dask, read_dask
    enable_dask()
    
    ds = read_dask(["file.tif"], chunks={"x": 1024})
    ds = ds.to_dask(chunks={"x": 256})
    ds = compute_index(ds, "NDVI")
    ds = ds.compute()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import xarray as xr

from satdatakit.core import SatelliteDataset


def _check_dask():
    """Verify Dask is installed."""
    try:
        import dask.array as da
        from dask.distributed import Client
    except ImportError:
        raise ImportError(
            "Dask not installed. Run: pip install satdatakit[dask]"
        ) from None


def enable_dask():
    """Activate Dask backend. Monkey-patches SatelliteDataset safely."""
    _check_dask()

    # --- Monkey patch: SatelliteDataset.to_dask ---
    def to_dask(self: SatelliteDataset, chunks: Optional[dict] = None) -> SatelliteDataset:
        """Convert data to Dask lazy arrays."""
        import dask.array as da
        
        if chunks is None:
            chunks = {"x": 1024, "y": 1024}
        if not isinstance(self.data.data, da.Array):
            new_data = self.data.chunk(chunks)
            return SatelliteDataset(
                data=new_data,
                bands=self.bands.copy(),
                crs=self.crs,
                resolution=self.resolution,
                bounds=self.bounds,
                datetime=self.datetime,
                sensor=self.sensor,
                platform=self.platform,
                cloud_cover=self.cloud_cover,
                metadata=self.metadata.copy(),
                source_format=self.source_format,
                source_path=self.source_path,
            )
        return self

    SatelliteDataset.to_dask = to_dask

    # --- Monkey patch: SatelliteDataset.compute ---
    def compute(self: SatelliteDataset) -> SatelliteDataset:
        """Trigger Dask computation and return in-memory dataset."""
        import dask.array as da
        
        if isinstance(self.data.data, da.Array):
            new_data = self.data.compute()
            return SatelliteDataset(
                data=new_data,
                bands=self.bands.copy(),
                crs=self.crs,
                resolution=self.resolution,
                bounds=self.bounds,
                datetime=self.datetime,
                sensor=self.sensor,
                platform=self.platform,
                cloud_cover=self.cloud_cover,
                metadata=self.metadata.copy(),
                source_format=self.source_format,
                source_path=self.source_path,
            )
        return self

    SatelliteDataset.compute = compute

    print("✅ Dask extension enabled:")
    print("   - ds.to_dask(chunks={...})")
    print("   - ds.compute()")


def disable_dask():
    """Remove Dask patches."""
    if hasattr(SatelliteDataset, "to_dask"):
        delattr(SatelliteDataset, "to_dask")
    if hasattr(SatelliteDataset, "compute"):
        delattr(SatelliteDataset, "compute")
    print("✅ Dask extension disabled")


def read_dask(
    paths: List[Union[str, Path]],
    bands: Optional[List[str]] = None,
    chunks: Optional[dict] = None,
    concat_dim: str = "time",
    **kwargs: Any,
) -> SatelliteDataset:
    """
    Read multiple files as lazy Dask dataset.
    
    Usage:
        from satdatakit.extensions.dask_ext import read_dask
        ds = read_dask(["file1.tif", "file2.tif"], chunks={"x": 1024})
    """
    _check_dask()
    
    import dask.array as da
    import rioxarray

    if chunks is None:
        chunks = {"x": 1024, "y": 1024}

    datasets = []
    for p in paths:
        ds = rioxarray.open_rasterio(p, chunks=chunks)
        datasets.append(ds)

    if len(datasets) == 1:
        stacked = datasets[0]
    else:
        stacked = xr.concat(datasets, dim=concat_dim)

    # Extraer nombres de bandas correctamente
    band_names = []
    if "band" in stacked.coords:
        band_names = [str(b) for b in stacked.coords["band"].values]
    else:
        band_names = [f"band_{i}" for i in range(stacked.sizes["band"])]

    return SatelliteDataset(
        data=stacked,
        bands=band_names,
        crs=stacked.rio.crs.to_string() if hasattr(stacked, "rio") else None,
        resolution=None,
        bounds=None,
        datetime=None,
        sensor=None,
        platform=None,
        cloud_cover=None,
        metadata={},
        source_format="dask",
        source_path=Path(paths[0]) if paths else None,
    )