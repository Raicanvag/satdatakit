"""Tests for Pipeline API.

Author: Rafael Cañete Vazquez
"""
import numpy as np
import pytest
import xarray as xr
from satdatakit.core import SatelliteDataset
from satdatakit.pipeline import Pipeline


class TestPipeline:
    @pytest.fixture
    def sample_dataset(self):
        data = xr.DataArray(
            np.random.rand(3, 100, 100).astype(np.float32),
            dims=["band", "y", "x"],
            coords={"band": ["B02", "B03", "B04"], "y": np.arange(100), "x": np.arange(100)},
        )
        return SatelliteDataset(data=data, bands=["B02", "B03", "B04"], crs="EPSG:4326")

    def test_empty_pipeline(self):
        p = Pipeline()
        assert p._dataset is None

    def test_select_bands(self, sample_dataset):
        p = Pipeline(sample_dataset).select_bands(["B02", "B04"])
        assert p.dataset.n_bands == 2

    def test_no_data_error(self):
        p = Pipeline()
        with pytest.raises(RuntimeError, match="No data"):
            p.select_bands(["red"])
