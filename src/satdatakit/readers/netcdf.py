"""NetCDF reader.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import xarray as xr

from satdatakit.core import SatelliteDataset

def read_netcdf(path: Union[str, Path], bands: Optional[List[str]] = None,
                variables: Optional[List[str]] = None,
                x_dim: str = "x", y_dim: str = "y", time_dim: str = "time",
                **kwargs: Any) -> SatelliteDataset:
    path = Path(path)
    if bands is not None and variables is None:
        variables = bands
    try:
        ds = xr.open_dataset(path, **kwargs)
    except Exception as e:
        raise RuntimeError(f"Cannot open NetCDF: {path} - {e}") from e
    if variables is None:
        variables = _detect_spatial_variables(ds, x_dim, y_dim)
        if not variables:
            raise ValueError(f"No spatial variables found in {path}")
    data_list = []
    band_names = []
    for var in variables:
        if var not in ds.data_vars:
            warnings.warn(f"Variable '{var}' not found. Skipping.", UserWarning)
            continue
        da = ds[var]
        if x_dim not in da.dims or y_dim not in da.dims:
            warnings.warn(f"Variable '{var}' missing spatial dims. Skipping.", UserWarning)
            continue
        if time_dim in da.dims:
            da = da.isel({time_dim: 0})
        if "band" not in da.dims:
            da = da.expand_dims(band=[var])
        data_list.append(da)
        band_names.append(var)
    if not data_list:
        raise ValueError(f"No valid variables could be read from {path}")
    if len(data_list) == 1:
        data_array = data_list[0]
    else:
        data_array = xr.concat(data_list, dim="band")
    if x_dim != "x":
        data_array = data_array.rename({x_dim: "x"})
    if y_dim != "y":
        data_array = data_array.rename({y_dim: "y"})
    crs = None
    for attr in ["crs", "spatial_ref", "esri_pe_string", "grid_mapping"]:
        if attr in ds.attrs:
            crs = str(ds.attrs[attr])
            break
    if crs is None:
        crs = _extract_cf_crs(ds)
    dt = None
    if time_dim in ds.coords:
        try:
            import pandas as pd
            dt_val = ds.coords[time_dim].values
            if hasattr(dt_val, "__len__") and len(dt_val) > 0:
                dt = pd.to_datetime(dt_val[0]).to_pydatetime()
            else:
                dt = pd.to_datetime(dt_val).to_pydatetime()
        except Exception:
            pass
    sensor = ds.attrs.get("sensor")
    platform = ds.attrs.get("platform")
    cloud_cover = None
    for key in ["cloud_cover", "CloudCover"]:
        if key in ds.attrs:
            try:
                cloud_cover = float(ds.attrs[key])
                break
            except (ValueError, TypeError):
                continue
    bounds = None
    resolution = None
    if "x" in data_array.coords and "y" in data_array.coords:
        x_vals = data_array.coords["x"].values
        y_vals = data_array.coords["y"].values
        bounds = (float(x_vals.min()), float(y_vals.min()), float(x_vals.max()), float(y_vals.max()))
        if len(x_vals) > 1 and len(y_vals) > 1:
            resolution = (abs(float(x_vals[1] - x_vals[0])), abs(float(y_vals[1] - y_vals[0])))
    return SatelliteDataset(
        data=data_array, bands=band_names, crs=crs, resolution=resolution,
        bounds=bounds, datetime=dt, sensor=sensor, platform=platform,
        cloud_cover=cloud_cover, metadata=dict(ds.attrs), source_format="netcdf",
        source_path=path)

def _detect_spatial_variables(ds: xr.Dataset, x_dim: str, y_dim: str) -> List[str]:
    spatial_vars = []
    for name, var in ds.data_vars.items():
        if x_dim in var.dims and y_dim in var.dims:
            spatial_vars.append(name)
    return spatial_vars

def _extract_cf_crs(ds: xr.Dataset) -> Optional[str]:
    for var_name, var in ds.data_vars.items():
        if "grid_mapping_name" in var.attrs:
            return var.attrs.get("crs_wkt", var.attrs.get("esri_pe_string"))
    if "Conventions" in ds.attrs and "CF" in str(ds.attrs["Conventions"]):
        for key in ["crs", "spatial_ref"]:
            if key in ds.attrs:
                return str(ds.attrs[key])
    return None
