import requests

from shapely.errors import ShapelyDeprecationWarning

import warnings

warnings.filterwarnings(
    "ignore",
    ".*Geometry is in a geographic CRS.*",
)
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

import osmnx

from via import settings
from via.log import logger


# overpass api clone for this so we can disable rate limiting and not feel bad

try:  # pragma: nocover
    if CUSTOM_OVERPASS_API:
        CUSTOM_AVAILABLE = (
            "www.openstreetmap.org"
            in requests.get(settings.CUSTOM_OVERPASS_API, timeout=1).text
        )
    else:
        CUSTOM_AVAILABLE = False
except:
    CUSTOM_AVAILABLE = False

if CUSTOM_AVAILABLE:  # pragma: nocover
    logger.info("Using custom overpass api")
    osmnx.settings.overpass_endpoint = settings.CUSTOM_OVERPASS_API
    osmnx.settings.overpass_rate_limit = False
else:
    osmnx.settings.overpass_endpoint = settings.DEFAULT_OVERPASS_API
    osmnx.settings.overpass_rate_limit = True
    logger.info("Using default overpass api")
