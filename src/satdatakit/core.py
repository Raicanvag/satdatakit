"""Core data model: SatelliteDataset.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import box


@dataclass
class SatelliteDataset:
    """Universal container for Earth Observation data."""

    data: xr.DataArray
    bands: List[str]
    crs: Optional[str] = None
    resolution: Optional[Tuple[float, float]] = None
    bounds: Optional[Tuple[float, float, float, float]] = None
    datetime: Optional[Union[datetime, List[datetime]]] = None
    sensor: Optional[str] = None
    platform: Optional[str] = None
    cloud_cover: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_format: Optional[str] = None
    source_path: Optional[Path] = None

    def __post_init__(self) -> None:
        self._validate_data()
        self._normalize_bands()

    def _validate_data(self) -> None:
        dims = list(self.data.dims)
        if "band" not in dims:
            raise ValueError(f"DataArray must have 'band' dimension. Got: {dims}")
        if "y" not in dims or "x" not in dims:
            raise ValueError(f"DataArray must have 'y' and 'x' dimensions. Got: {dims}")
        n_bands = self.data.sizes["band"]
        if n_bands != len(self.bands):
            warnings.warn(f"Band count mismatch: {n_bands} vs {len(self.bands)}", UserWarning)
            self.bands = [f"band_{i}" for i in range(n_bands)]

    def _normalize_bands(self) -> None:
        self.bands = [str(b) for b in self.bands]
        seen = set()
        for i, name in enumerate(self.bands):
            if name in seen:
                self.bands[i] = f"{name}_{i}"
            seen.add(self.bands[i])

    @property
    def shape(self) -> Tuple[int, ...]:
        return tuple(self.data.sizes[d] for d in self.data.dims)

    @property
    def n_bands(self) -> int:
        return self.data.sizes["band"]

    @property
    def width(self) -> int:
        return self.data.sizes["x"]

    @property
    def height(self) -> int:
        return self.data.sizes["y"]

    @property
    def dtype(self):
        """Return data type."""
        return self.data.dtype

    def __getitem__(self, key: Union[str, int]) -> xr.DataArray:
        if isinstance(key, str):
            if key not in self.bands:
                raise KeyError(f"Band '{key}' not found. Available: {self.bands}")
            idx = self.bands.index(key)
        elif isinstance(key, int):
            idx = key
        else:
            raise TypeError(f"Key must be str or int, got {type(key)}")
        return self.data.isel(band=idx)

    def get_bands(self, names: List[str]) -> "SatelliteDataset":
        indices = [self.bands.index(n) for n in names if n in self.bands]
        new_data = self.data.isel(band=indices)
        return SatelliteDataset(
            data=new_data, bands=[self.bands[i] for i in indices],
            crs=self.crs, resolution=self.resolution, bounds=self.bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def to_numpy(self) -> np.ndarray:
        return self.data.values

    def to_xarray(self) -> xr.DataArray:
        return self.data

    def to_dataset(self) -> xr.Dataset:
        datasets = {b: self.data.isel(band=i).drop_vars("band")
                    for i, b in enumerate(self.bands)}
        ds = xr.Dataset(datasets)
        if self.crs:
            ds.attrs["crs"] = self.crs
        return ds

    def add_band(self, name: str, data: Union[np.ndarray, xr.DataArray]) -> "SatelliteDataset":
        if name in self.bands:
            raise ValueError(f"Band '{name}' already exists.")
        if isinstance(data, np.ndarray):
            data = xr.DataArray(data, dims=["y", "x"])
        data = data.expand_dims(band=[name])
        new_data = xr.concat([self.data, data], dim="band")
        return SatelliteDataset(
            data=new_data, bands=self.bands + [name], crs=self.crs,
            resolution=self.resolution, bounds=self.bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def remove_band(self, name: str) -> "SatelliteDataset":
        if name not in self.bands:
            raise KeyError(f"Band '{name}' not found.")
        idx = self.bands.index(name)
        new_data = self.data.drop_isel(band=idx)
        return SatelliteDataset(
            data=new_data, bands=[b for b in self.bands if b != name],
            crs=self.crs, resolution=self.resolution, bounds=self.bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def rename_bands(self, mapping: Dict[str, str]) -> "SatelliteDataset":
        new_bands = [mapping.get(b, b) for b in self.bands]
        new_data = self.data.copy()
        new_data = new_data.assign_coords(band=new_bands)
        return SatelliteDataset(
            data=new_data, bands=new_bands, crs=self.crs,
            resolution=self.resolution, bounds=self.bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def reproject(self, dst_crs: Union[str, int], **kwargs) -> "SatelliteDataset":
        import rioxarray
        if self.crs is None:
            raise ValueError("Source CRS is not set. Cannot reproject.")
        if self.data.rio.crs is None:
            self.data = self.data.rio.write_crs(self.crs)
        reprojected = self.data.rio.reproject(dst_crs, **kwargs)
        new_bounds = reprojected.rio.bounds()
        return SatelliteDataset(
            data=reprojected, bands=self.bands.copy(), crs=str(dst_crs),
            resolution=self.resolution, bounds=new_bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def resample(self, resolution: Union[float, Tuple[float, float]], **kwargs) -> "SatelliteDataset":
        if self.crs is None:
            raise ValueError("CRS must be set to resample.")
        return self.reproject(dst_crs=self.crs, resolution=resolution, **kwargs)

    def clip(self, geometry, crs=None, drop=True, **kwargs) -> "SatelliteDataset":
        import rioxarray
        if self.data.rio.crs is None and self.crs is not None:
            self.data = self.data.rio.write_crs(self.crs)
        clipped = self.data.rio.clip([geometry], crs=crs, drop=drop, all_touched=True, **kwargs)
        new_bounds = clipped.rio.bounds()
        return SatelliteDataset(
            data=clipped, bands=self.bands.copy(), crs=self.crs,
            resolution=self.resolution, bounds=new_bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def mask(self, mask_array: np.ndarray, fill_value: float = np.nan) -> "SatelliteDataset":
        if mask_array.shape != self.data.shape[-2:]:
            raise ValueError(f"Mask shape {mask_array.shape} does not match data spatial shape {self.data.shape[-2:]}")
        masked_data = self.data.where(mask_array, fill_value)
        return SatelliteDataset(
            data=masked_data, bands=self.bands.copy(), crs=self.crs,
            resolution=self.resolution, bounds=self.bounds,
            datetime=self.datetime, sensor=self.sensor, platform=self.platform,
            cloud_cover=self.cloud_cover, metadata=self.metadata.copy(),
            source_format=self.source_format, source_path=self.source_path)

    def to_geotiff(self, path: Union[str, Path], **kwargs) -> None:
        import rioxarray
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.data
        if data.rio.crs is None and self.crs is not None:
            data = data.rio.write_crs(self.crs)
        data.rio.to_raster(path, **kwargs)

    def to_netcdf(self, path: Union[str, Path], **kwargs) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataset().to_netcdf(path, **kwargs)

    def __repr__(self) -> str:
        return f"SatelliteDataset(shape={self.shape}, bands={self.bands}, crs={self.crs!r})"

    def info(self) -> str:
        lines = [
            "=" * 50,
            "SatelliteDataset Information",
            "=" * 50,
            f"Shape:        {self.shape}",
            f"Bands:        {self.n_bands} ({self.bands})",
            f"Width:        {self.width} px",
            f"Height:       {self.height} px",
            f"CRS:          {self.crs}",
            f"Resolution:   {self.resolution}",
            f"Bounds:       {self.bounds}",
            f"Sensor:       {self.sensor}",
            f"Platform:     {self.platform}",
            f"Datetime:     {self.datetime}",
            f"Cloud cover:  {self.cloud_cover}%",
            f"Dtype:        {self.dtype}",
            "=" * 50,
        ]
        return "\n".join(lines)
