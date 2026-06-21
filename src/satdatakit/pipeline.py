"""Fluent pipeline API.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from satdatakit.core import SatelliteDataset
from satdatakit.indices import compute_index
from satdatakit.io import read


class Pipeline:
    """Fluent processing pipeline for satellite data."""

    def __init__(self, dataset: Optional[SatelliteDataset] = None):
        self._dataset = dataset
        self._operations: List[str] = []

    def read(self, path: Union[str, Path], **kwargs) -> "Pipeline":
        dataset = read(path, **kwargs)
        new_pipeline = Pipeline(dataset)
        new_pipeline._operations = self._operations + [f"read({path})"]
        return new_pipeline

    def reproject(self, dst_crs, **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = self._dataset.reproject(dst_crs, **kwargs)
        return Pipeline(dataset)

    def resample(self, resolution, **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = self._dataset.resample(resolution, **kwargs)
        return Pipeline(dataset)

    def clip(self, geometry, **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = self._dataset.clip(geometry, **kwargs)
        return Pipeline(dataset)

    def select_bands(self, bands: List[str]) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = self._dataset.get_bands(bands)
        return Pipeline(dataset)

    def compute_index(self, index: str, **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = compute_index(self._dataset, index, **kwargs)
        return Pipeline(dataset)

    def apply(self, func: Callable, *args, **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        dataset = func(self._dataset, *args, **kwargs)
        return Pipeline(dataset)

    def to_geotiff(self, path: Union[str, Path], **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        self._dataset.to_geotiff(path, **kwargs)
        return Pipeline(self._dataset)

    def to_netcdf(self, path: Union[str, Path], **kwargs) -> "Pipeline":
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        self._dataset.to_netcdf(path, **kwargs)
        return Pipeline(self._dataset)

    @property
    def dataset(self) -> SatelliteDataset:
        if self._dataset is None:
            raise RuntimeError("No data loaded.")
        return self._dataset

    @property
    def operations(self) -> List[str]:
        """List of operations performed."""
        return self._operations.copy()
        
    def __repr__(self) -> str:
        if self._dataset is None:
            return "Pipeline(empty)"
        return f"Pipeline({self._dataset.n_bands} bands)"


