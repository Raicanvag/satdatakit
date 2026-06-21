"""STAC extension for SatDataKit — cloud catalog access.

Usage:
    from satdatakit.extensions.stac_ext import enable_stac
    enable_stac()
    
    ds = satdatakit.read_stac(
        catalog_url="https://earth-search.aws.element84.com/v1",
        collection="sentinel-2-l2a",
        bbox=(-100, 25, -99, 26),
        datetime_range="2024-01-01/2024-06-01"
    )
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union


def enable_stac():
    """Activate STAC backend."""
    try:
        import pystac
        import pystac_client
        import stackstac
    except ImportError:
        raise ImportError(
            "STAC dependencies not installed. Run: pip install satdatakit[stac]"
        ) from None

    from satdatakit.core import SatelliteDataset

    def read_stac(
        catalog_url: str,
        collection: str,
        bbox: Tuple[float, float, float, float],
        datetime_range: str,
        bands: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> SatelliteDataset:
        """Search and read from STAC catalog."""
        catalog = pystac_client.Client.open(catalog_url)
        search = catalog.search(
            collections=[collection],
            bbox=bbox,
            datetime=datetime_range,
        )
        items = list(search.get_items())
        
        if not items:
            raise ValueError("No items found for query")

        data = stackstac.stack(items, assets=bands, **kwargs)

        return SatelliteDataset(
            data=data,
            bands=bands or list(data.coords["band"].values),
            crs="EPSG:4326",
            source_format="stac",
        )

    import satdatakit
    satdatakit.read_stac = read_stac

    print("✅ STAC extension enabled:")
    print("   - satdatakit.read_stac(catalog_url=..., collection=...)")


def disable_stac():
    """Remove STAC patches."""
    import satdatakit
    if hasattr(satdatakit, "read_stac"):
        delattr(satdatakit, "read_stac")
    print("✅ STAC extension disabled")