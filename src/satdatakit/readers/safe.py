"""Sentinel SAFE format reader.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

import warnings
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import xarray as xr

from satdatakit.core import SatelliteDataset
from satdatakit.readers.geotiff import read_geotiff

def read_safe(path: Union[str, Path], bands: Optional[List[str]] = None,
              resolution: Optional[str] = None, **kwargs: Any) -> SatelliteDataset:
    path = Path(path)
    if path.suffix == ".zip":
        return _read_safe_zip(path, bands, resolution, **kwargs)
    else:
        return _read_safe_dir(path, bands, resolution, **kwargs)

def _read_safe_dir(path: Path, bands: Optional[List[str]],
                   resolution: Optional[str], **kwargs) -> SatelliteDataset:
    manifest = path / "manifest.safe"
    if not manifest.exists():
        raise FileNotFoundError(f"manifest.safe not found in {path}")
    metadata = _parse_safe_metadata(path)
    granule_dir = path / "GRANULE"
    if not granule_dir.exists():
        raise ValueError(f"GRANULE directory not found in {path}")
    img_data_dirs = list(granule_dir.rglob("IMG_DATA"))
    if not img_data_dirs:
        raise ValueError(f"IMG_DATA not found in {path}")
    img_data = img_data_dirs[0]
    if resolution:
        res_dir = img_data / f"R{resolution}"
        if res_dir.exists():
            img_data = res_dir
    jp2_files = sorted(img_data.glob("*.jp2"))
    if not jp2_files:
        raise ValueError(f"No JP2 files found in {img_data}")
    band_files = {}
    for jp2 in jp2_files:
        parts = jp2.stem.split("_")
        for part in parts:
            if part.startswith("B") and part[1:].isdigit():
                band_files[part] = jp2
                break
    if bands is None:
        bands = sorted(band_files.keys())
    selected_files = []
    selected_bands = []
    for band in bands:
        if band in band_files:
            selected_files.append(band_files[band])
            selected_bands.append(band)
        else:
            warnings.warn(f"Band {band} not found. Available: {list(band_files.keys())}", UserWarning)
    if not selected_files:
        raise ValueError(f"No valid bands found. Available: {list(band_files.keys())}")
    data_arrays = []
    for f in selected_files:
        ds = read_geotiff(f)
        data_arrays.append(ds.data)
    merged = xr.concat(data_arrays, dim="band")
    merged = merged.assign_coords(band=selected_bands)
    first = read_geotiff(selected_files[0])
    return SatelliteDataset(
        data=merged, bands=selected_bands, crs=first.crs,
        resolution=first.resolution, bounds=first.bounds,
        datetime=metadata.get("datetime"), sensor=metadata.get("sensor"),
        platform=metadata.get("platform"), cloud_cover=metadata.get("cloud_cover"),
        metadata=metadata, source_format="safe", source_path=path)

def _read_safe_zip(path: Path, bands: Optional[List[str]],
                   resolution: Optional[str], **kwargs) -> SatelliteDataset:
    import tempfile
    import shutil
    temp_dir = Path(tempfile.mkdtemp(prefix="satdatakit_safe_"))
    try:
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(temp_dir)
        safe_dirs = list(temp_dir.glob("*.SAFE"))
        if not safe_dirs:
            raise ValueError("No .SAFE directory found in zip")
        return _read_safe_dir(safe_dirs[0], bands, resolution, **kwargs)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def _parse_safe_metadata(path: Path) -> dict:
    metadata = {}
    mtd_files = list(path.rglob("MTD_*.xml"))
    if not mtd_files:
        return metadata
    try:
        tree = ET.parse(mtd_files[0])
        root = tree.getroot()
        for elem in root.iter():
            if elem.tag.endswith("SENSING_TIME") or elem.tag.endswith("ProductStartTime"):
                try:
                    metadata["datetime"] = datetime.fromisoformat(elem.text.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            if elem.tag.endswith("SPACECRAFT_NAME"):
                metadata["platform"] = elem.text
            if elem.tag.endswith("DATATAKE_TYPE"):
                metadata["sensor"] = elem.text
            if elem.tag.endswith("Cloud_Coverage_Assessment"):
                try:
                    metadata["cloud_cover"] = float(elem.text)
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    return metadata
