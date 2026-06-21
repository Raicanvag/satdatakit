"""Tests for spectral indices.

Author: Rafael Cañete Vazquez
"""
import numpy as np
import pytest
import xarray as xr
from satdatakit.core import SatelliteDataset
from satdatakit.indices import compute_index, list_indices


class TestSpectralIndices:
    @pytest.fixture
    def sample_dataset(self):
        data = xr.DataArray(
            np.stack([
                np.full((100, 100), 0.1, dtype=np.float32),
                np.full((100, 100), 0.2, dtype=np.float32),
                np.full((100, 100), 0.3, dtype=np.float32),
                np.full((100, 100), 0.6, dtype=np.float32),
            ]),
            dims=["band", "y", "x"],
            coords={"band": ["B02", "B03", "B04", "B08"], "y": np.arange(100), "x": np.arange(100)},
        )
        return SatelliteDataset(data=data, bands=["B02", "B03", "B04", "B08"], crs="EPSG:4326")

    def test_list_indices(self):
        indices = list_indices()
        assert "NDVI" in indices

    def test_compute_ndvi(self, sample_dataset):
        result = compute_index(sample_dataset, "NDVI")
        assert isinstance(result, SatelliteDataset)
        assert "NDVI" in result.bands
