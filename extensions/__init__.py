"""SatDataKit extensions — optional add-ons for scalability.

Extensions load on demand and do not modify core code.
"""

__version__ = "0.1.0"


def list_extensions():
    """Return available extensions."""
    return ["dask", "stac", "zarr"]


def enable(extension: str):
    """Activate an extension by name."""
    if extension == "dask":
        from .dask_ext import enable_dask
        enable_dask()
    elif extension == "stac":
        from .stac_ext import enable_stac
        enable_stac()
    elif extension == "zarr":
        from .zarr_ext import enable_zarr
        enable_zarr()
    else:
        raise ValueError(f"Unknown extension: {extension}. Available: {list_extensions()}")