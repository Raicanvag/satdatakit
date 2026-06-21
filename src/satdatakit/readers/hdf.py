"""HDF4/HDF5 reader.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import xarray as xr

from satdatakit.core import SatelliteDataset


def read_hdf(
    path: Union[str, Path],
    bands: Optional[List[str]] = None,
    dataset_name: Optional[str] = None,
    **kwargs: Any,
) -> SatelliteDataset:
    """Read HDF4 or HDF5 file into SatelliteDataset."""
    path = Path(path)
    try:
        return _read_hdf5(path, bands, dataset_name, **kwargs)
    except Exception as h5_error:
        try:
            return _read_hdf4(path, bands, dataset_name, **kwargs)
        except Exception as h4_error:
            raise RuntimeError(
                f"Failed to read HDF5: {h5_error}\n"
                f"Failed to read HDF4: {h4_error}"
            )


def _read_hdf5(
    path: Path,
    bands: Optional[List[str]],
    dataset_name: Optional[str],
    **kwargs: Any,
) -> SatelliteDataset:
    """Read HDF5 file with automatic dataset discovery."""
    import h5py

    with h5py.File(path, "r") as f:
        # Buscar datasets con ndim >= 2 en toda la jerarquía
        candidates = []

        def find_datasets(name, obj):
            if isinstance(obj, h5py.Dataset) and obj.ndim >= 2:
                candidates.append(name)

        f.visititems(find_datasets)

        if dataset_name is None:
            if candidates:
                dataset_name = candidates[0]

        if dataset_name is None:
            raise ValueError(f"No 2D+ datasets found in file")

        # Navegar al dataset (puede estar anidado como "reflectance/data")
        parts = dataset_name.split("/")
        h5_dataset = f
        for part in parts:
            h5_dataset = h5_dataset[part]

        data = np.array(h5_dataset)
        if data.ndim == 2:
            data = data[np.newaxis, ...]
        elif data.ndim == 3:
            if data.shape[-1] < data.shape[0]:
                data = np.moveaxis(data, -1, 0)

        attrs = dict(h5_dataset.attrs)
        file_attrs = dict(f.attrs)

        n_bands = data.shape[0]
        band_names = []
        for i in range(n_bands):
            if bands and i < len(bands):
                band_names.append(bands[i])
            else:
                band_names.append(f"band_{i}")

        data_array = xr.DataArray(
            data,
            dims=["band", "y", "x"],
            coords={
                "band": band_names,
                "y": np.arange(data.shape[1]),
                "x": np.arange(data.shape[2]),
            },
            attrs=attrs,
        )

        metadata = {**file_attrs, **attrs}
        crs = None
        for key in ["crs", "CoordinateSystem", "Projection"]:
            if key in metadata:
                crs = str(metadata[key])
                break

        dt = None
        for key in ["DateTime", "acquisition_date", "Date"]:
            if key in metadata:
                try:
                    dt = datetime.strptime(str(metadata[key]), "%Y-%m-%d")
                    break
                except ValueError:
                    continue

        return SatelliteDataset(
            data=data_array,
            bands=band_names,
            crs=crs,
            resolution=None,
            bounds=None,
            datetime=dt,
            sensor=metadata.get("sensor"),
            platform=metadata.get("platform"),
            metadata=metadata,
            source_format="hdf5",
            source_path=path,
        )


def _read_hdf4(
    path: Path,
    bands: Optional[List[str]],
    dataset_name: Optional[str],
    **kwargs: Any,
) -> SatelliteDataset:
    """Read HDF4 file via rasterio."""
    import rasterio

    with rasterio.open(path) as src:
        subdatasets = src.subdatasets if hasattr(src, "subdatasets") else []
        if not subdatasets:
            raise ValueError("No subdatasets found in HDF4 file")
        subdataset_path = subdatasets[0]
        with rasterio.open(subdataset_path) as sub_src:
            data = sub_src.read()
            if data.ndim == 2:
                data = data[np.newaxis, ...]
            band_names = [f"band_{i}" for i in range(data.shape[0])]
            data_array = xr.DataArray(
                data,
                dims=["band", "y", "x"],
                coords={
                    "band": band_names,
                    "y": np.arange(data.shape[1]),
                    "x": np.arange(data.shape[2]),
                },
            )
            return SatelliteDataset(
                data=data_array,
                bands=band_names,
                crs=sub_src.crs.to_string() if sub_src.crs else None,
                resolution=(
                    (abs(sub_src.transform.a), abs(sub_src.transform.e))
                    if sub_src.transform
                    else None
                ),
                bounds=sub_src.bounds,
                metadata=dict(sub_src.tags()),
                source_format="hdf4",
                source_path=path,
            )
