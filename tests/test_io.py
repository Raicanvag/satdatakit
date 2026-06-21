"""Tests for unified I/O.

Author: Rafael Cañete Vazquez
"""
from pathlib import Path
import numpy as np
import pytest
import rasterio
from satdatakit.core import SatelliteDataset
from satdatakit.io import _detect_format, read


class TestFormatDetection:
    def test_detect_geotiff(self):
        assert _detect_format("test.tif") == "geotiff"

    def test_detect_netcdf(self):
        assert _detect_format("test.nc") == "netcdf"

    def test_detect_unknown(self):
        with pytest.raises(ValueError):
            _detect_format("test.unknown")


class TestReadGeoTIFF:
    @pytest.fixture
    def geotiff_path(self, tmp_path):
        path = tmp_path / "test.tif"
        data = np.random.rand(3, 100, 100).astype(np.float32)
        with rasterio.open(
            path, "w", driver="GTiff", height=100, width=100, count=3,
            dtype="float32", crs="EPSG:4326",
            transform=rasterio.Affine.identity() * rasterio.Affine.scale(0.01, -0.01),
        ) as dst:
            dst.write(data)
        return path

    def test_read_geotiff(self, geotiff_path):
        ds = read(geotiff_path)
        assert isinstance(ds, SatelliteDataset)
        assert ds.n_bands == 3
        assert ds.source_format == "geotiff"
