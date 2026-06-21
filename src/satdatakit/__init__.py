"""SatDataKit - Unified satellite data analysis toolkit.

Author: Rafael Cañete Vazquez
License: MIT
"""
__version__ = "0.1.0"
__author__ = "Rafael Cañete Vazquez"

from satdatakit.core import SatelliteDataset
from satdatakit.io import read, read_collection
from satdatakit.indices import compute_index
from satdatakit.pipeline import Pipeline

__all__ = ["SatelliteDataset", "read", "read_collection", "compute_index", "Pipeline"]
