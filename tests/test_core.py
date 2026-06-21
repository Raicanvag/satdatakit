"""Tests for SatelliteDataset core class.

Author: Rafael Cañete Vazquez
"""
import numpy as np
import pytest
import xarray as xr

from satdatakit.core import SatelliteDataset


class TestSatelliteDataset:
    @pytest.fixture
    def sample_dataset(self):
        data = xr.DataArray(
            np.random.rand(3, 100, 100).astype(np.float32),
            dims=["band", "y", "x"],
            coords={"band": ["red", "green", "blue"], "y": np.arange(100), "x": np.arange(100)},
        )
        return SatelliteDataset(
            data=data, bands=["red", "green", "blue"], crs="EPSG:4326",
            resolution=(10.0, 10.0), bounds=(0.0, 0.0, 1000.0, 1000.0),
            sensor="sentinel-2", platform="sentinel-2a", source_format="geotiff")

    def test_init(self, sample_dataset):
        assert sample_dataset.n_bands == 3
        assert sample_dataset.bands == ["red", "green", "blue"]
        assert sample_dataset.crs == "EPSG:4326"

    def test_getitem(self, sample_dataset):
        red = sample_dataset["red"]
        assert red.shape == (100, 100)

    def test_add_band(self, sample_dataset):
        new_data = np.random.rand(100, 100).astype(np.float32)
        updated = sample_dataset.add_band("nir", new_data)
        assert updated.n_bands == 4
        assert "nir" in updated.bands

    def test_remove_band(self, sample_dataset):
        updated = sample_dataset.remove_band("green")
        assert updated.n_bands == 2
        assert "green" not in updated.bands
