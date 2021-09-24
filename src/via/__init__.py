import requests

from via.logging import logger

import osmnx as ox

# overpass api clone for this so we can disable rate limiting and not feel bad
CUSTOM_OVERPASS_API = 'http://54.73.95.15/api'
DEFAULT_OVERPASS_API = 'https://overpass-api.de/api'

try:
    CUSTOM_AVAILABLE = 'www.openstreetmap.org' in requests.get(CUSTOM_OVERPASS_API).text
except:
    CUSTOM_AVAILABLE = False

if CUSTOM_AVAILABLE:
    overpass_endpoint = CUSTOM_OVERPASS_API
    overpass_rate_limit = False
else:
    overpass_endpoint = DEFAULT_OVERPASS_API
    overpass_rate_limit = True

ox.config(
    overpass_endpoint=overpass_endpoint,
    overpass_rate_limit=overpass_rate_limit
)
