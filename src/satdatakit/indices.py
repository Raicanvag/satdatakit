"""Spectral indices computation.

Author: Rafael Cañete Vazquez
License: MIT
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import xarray as xr

from satdatakit.core import SatelliteDataset

INDEX_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "NDVI": {
        "name": "Normalized Difference Vegetation Index",
        "formula": "(nir - red) / (nir + red)",
        "bands": {"red": ["red", "B04"], "nir": ["nir", "B08"]},
        "range": (-1, 1),
    },
    "NDWI": {
        "name": "Normalized Difference Water Index",
        "formula": "(green - nir) / (green + nir)",
        "bands": {"green": ["green", "B03"], "nir": ["nir", "B08"]},
        "range": (-1, 1),
    },
    "EVI": {
        "name": "Enhanced Vegetation Index",
        "formula": "2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)",
        "bands": {"red": ["red", "B04"], "nir": ["nir", "B08"], "blue": ["blue", "B02"]},
        "range": (-1, 1),
    },
    "SAVI": {
        "name": "Soil Adjusted Vegetation Index",
        "formula": "(1 + L) * (nir - red) / (nir + red + L)",
        "bands": {"red": ["red", "B04"], "nir": ["nir", "B08"]},
        "params": {"L": 0.5},
        "range": (-1, 1),
    },
}

def _resolve_band_name(dataset: SatelliteDataset, candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in dataset.bands:
            return candidate
    return None

def compute_index(dataset: SatelliteDataset, index: str,
                  band_mapping: Optional[Dict[str, str]] = None,
                  params: Optional[Dict[str, float]] = None,
                  add_to_dataset: bool = True, clip_range: bool = True
                  ) -> Union[SatelliteDataset, xr.DataArray]:
    index = index.upper()
    if index not in INDEX_DEFINITIONS:
        raise ValueError(f"Index '{index}' not supported.")
    definition = INDEX_DEFINITIONS[index]
    resolved_bands = {}
    for canonical_name, candidates in definition["bands"].items():
        if band_mapping and canonical_name in band_mapping:
            actual_name = band_mapping[canonical_name]
        else:
            actual_name = _resolve_band_name(dataset, candidates)
        if actual_name is None:
            raise KeyError(f"Cannot resolve band for '{canonical_name}'.")
        resolved_bands[canonical_name] = actual_name
    band_data = {name: dataset[actual] for name, actual in resolved_bands.items()}
    formula_params = definition.get("params", {}).copy()
    if params:
        formula_params.update(params)
    result = _compute_formula(index, band_data, formula_params)
    if clip_range:
        valid_min, valid_max = definition.get("range", (-float("inf"), float("inf")))
        result = result.clip(min=valid_min, max=valid_max)
    result = result.where(np.isfinite(result))
    if add_to_dataset:
        return dataset.add_band(index, result)
    return result

def _compute_formula(index: str, bands: Dict[str, xr.DataArray], params: Dict[str, float]) -> xr.DataArray:
    if index == "NDVI":
        return (bands["nir"] - bands["red"]) / (bands["nir"] + bands["red"])
    elif index == "NDWI":
        return (bands["green"] - bands["nir"]) / (bands["green"] + bands["nir"])
    elif index == "EVI":
        return 2.5 * (bands["nir"] - bands["red"]) / (bands["nir"] + 6 * bands["red"] - 7.5 * bands["blue"] + 1)
    elif index == "SAVI":
        L = params.get("L", 0.5)
        return (1 + L) * (bands["nir"] - bands["red"]) / (bands["nir"] + bands["red"] + L)
    else:
        raise ValueError(f"Formula not implemented for index: {index}")

def list_indices() -> List[str]:
    return list(INDEX_DEFINITIONS.keys())

def index_info(index: str) -> Dict[str, Any]:
    index = index.upper()
    if index not in INDEX_DEFINITIONS:
        raise ValueError(f"Index '{index}' not found.")
    return INDEX_DEFINITIONS[index].copy()
