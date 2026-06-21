"""Zarr extension for SatDataKit — cloud-native format.

Usage:
    from satdatakit.extensions.zarr_ext import enable_zarr
    enable_zarr()
    
    ds = satdatakit.read_zarr("s3://bucket/dataset.zarr")
    ds.to_zarr("/local/output.zarr")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union


def enable_zarr():
    """Activate Zarr backend."""
    try:
        import zarr
    except ImportError:
        raise ImportError(
            "Zarr not installed. Run: pip install satdatakit[zarr]"
        ) from None

    from satdatakit.core import SatelliteDataset

    # --- Monkey patch: SatelliteDataset.to_zarr ---
    def to_zarr(self: SatelliteDataset, path: Union[str, Path], **kwargs: Any) -> None:
        """Export dataset to Zarr format."""
        ds = self.to_dataset()
        ds.to_zarr(path, **kwargs)

    SatelliteDataset.to_zarr = to_zarr

    # --- Global function: read_zarr ---
    def read_zarr(path: Union[str, Path], **kwargs: Any) -> SatelliteDataset:
        """Read Zarr store into SatelliteDataset."""
        import xarray as xr

        ds = xr.open_zarr(path, **kwargs)
        
        # Detectar variables espaciales
        spatial_vars = []
        for name, var in ds.data_vars.items():
            if any(d in var.dims for d in ["x", "y", "lon", "lat"]):
                spatial_vars.append(name)

        if not spatial_vars:
            raise ValueError("No spatial variables found in Zarr store")

        # Convertir a DataArray con dimensión band
        data_arrays = []
        for var in spatial_vars:
            da = ds[var]
            if "band" not in da.dims:
                da = da.expand_dims(band=[var])
            data_arrays.append(da)

        if len(data_arrays) == 1:
            data = data_arrays[0]
        else:
            data = xr.concat(data_arrays, dim="band")

        return SatelliteDataset(
            data=data,
            bands=spatial_vars,
            crs=ds.attrs.get("crs"),
            source_format="zarr",
            source_path=Path(path),
        )

    import satdatakit
    satdatakit.read_zarr = read_zarr

    print("✅ Zarr extension enabled:")
    print("   - satdatakit.read_zarr(path)")
    print("   - ds.to_zarr(path)")


def disable_zarr():
    """Remove Zarr patches."""
    from satdatakit.core import SatelliteDataset
    if hasattr(SatelliteDataset, "to_zarr"):
        delattr(SatelliteDataset, "to_zarr")
    import satdatakit
    if hasattr(satdatakit, "read_zarr"):
        delattr(satdatakit, "read_zarr")
    print("✅ Zarr extension disabled")