"""Readers subpackage.

Author: Rafael Cañete Vazquez
License: MIT
"""
from satdatakit.readers.geotiff import read_geotiff
from satdatakit.readers.netcdf import read_netcdf
from satdatakit.readers.hdf import read_hdf
from satdatakit.readers.safe import read_safe

READERS = {
    "geotiff": read_geotiff,
    "netcdf": read_netcdf,
    "hdf": read_hdf,
    "safe": read_safe,
}

__all__ = ["READERS", "read_geotiff", "read_netcdf", "read_hdf", "read_safe"]
