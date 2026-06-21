"""Dask extension for SatDataKit — parallel processing.

Usage:
    from satdatakit.extensions.dask_ext import enable_dask
    enable_dask()
    
    ds = read("file.tif")
    ds = ds.to_dask(chunks={"x": 1024, "y": 1024})
    ds = compute_index(ds, "NDVI")  # lazy + parallel
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Union

from satdatakit.core import SatelliteDataset


def enable_dask():
    """Activate Dask backend. Monkey-patches SatelliteDataset safely."""
    try:
        import dask.array as da
        import xarray as xr
        from dask.distributed import Client
    except ImportError:
        raise ImportError(
            "Dask not installed. Run: pip install satdatakit[dask]"
        ) from None

    # --- Monkey patch: SatelliteDataset.to_dask ---
    def to_dask(self: SatelliteDataset, chunks: Optional[dict] = None) -> SatelliteDataset:
        """Convert data to Dask lazy arrays."""
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

    # --- Global function: read_dask ---
    def read_dask(
        paths: List[Union[str, Path]],
        bands: Optional[List[str]] = None,
        chunks: Optional[dict] = None,
        concat_dim: str = "time",
        **kwargs: Any,
    ) -> SatelliteDataset:
        """Read multiple files as lazy Dask dataset."""
        if chunks is None:
            chunks = {"x": 1024, "y": 1024}

        datasets = []
        for p in paths:
            ds = xr.open_dataarray(p, chunks=chunks, **kwargs)
            if "band" not in ds.dims:
                ds = ds.expand_dims(band=[Path(p).stem])
            datasets.append(ds)

        stacked = xr.concat(datasets, dim=concat_dim)
        band_names = [Path(p).stem for p in paths]

        return SatelliteDataset(
            data=stacked,
            bands=band_names,
            source_format="dask",
        )

    import satdatakit
    satdatakit.read_dask = read_dask

    print("✅ Dask extension enabled:")
    print("   - ds.to_dask(chunks={...})")
    print("   - ds.compute()")
    print("   - satdatakit.read_dask([...])")


def disable_dask():
    """Remove Dask patches."""
    if hasattr(SatelliteDataset, "to_dask"):
        delattr(SatelliteDataset, "to_dask")
    if hasattr(SatelliteDataset, "compute"):
        delattr(SatelliteDataset, "compute")
    import satdatakit
    if hasattr(satdatakit, "read_dask"):
        delattr(satdatakit, "read_dask")
    print("✅ Dask extension disabled")