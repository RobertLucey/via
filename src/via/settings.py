import os
import pkg_resources
from packaging import version

# TODO: data from DOWNLOAD_JOURNEYS_URL should give back the s3 region
DOWNLOAD_JOURNEYS_URL = os.getenv('DOWNLOAD_JOURNEYS', 'https://l7vv5djf9h.execute-api.eu-west-1.amazonaws.com/default/getUUIDs')
S3_REGION = os.getenv('S3_REGION', 'eu-west-1')

MIN_ACC_SCORE = float(os.getenv('MIN_ACC_SCORE', '0.001'))
MIN_PER_JOURNEY_USAGE = float(os.getenv('MIN_PER_JOURNEY_USAGE', '1'))
MIN_METRES_PER_SECOND = float(os.getenv('MIN_METRES_PER_SECOND', '2'))
MAX_METRES_PER_SECOND = float(os.getenv('MAX_METRES_PER_SECOND', '10000'))

MIN_JOURNEY_VERSION = version.parse(os.getenv('MIN_JOURNEY_VERSION', '0.0.0'))
MAX_JOURNEY_VERSION = version.parse(os.getenv('MAX_JOURNEY_VERSION', '999.999.999'))

# How often to skip gps points, smooths things out a bit more
# 1 includes all, 3 includes every 3rd etc
# Intervals are generally 2 seconds
GPS_INCLUDE_RATIO = int(os.getenv('GPS_INCLUDE_RATIO', '2'))

VIZ_INITIAL_LAT = float(os.getenv('VIZ_INITIAL_LAT', 53.35))
VIZ_INITIAL_LNG = float(os.getenv('VIZ_INITIAL_LNG', -6.26))
VIZ_INITIAL_ZOOM = int(os.getenv('VIZ_INITIAL_ZOOM', 12))

NEAREST_EDGE_METHOD = os.getenv('NEAREST_EDGE_METHOD', 'angle_nearest')
CLOSE_ANGLE_TO_ROAD = float(os.getenv('CLOSE_ANGLE_TO_ROAD', 15))

DEFAULT_OVERPASS_API = os.getenv('DEFAULT_OVERPASS_API', 'https://overpass-api.de/api')
CUSTOM_OVERPASS_API = os.getenv('CUSTOM_OVERPASS_API', 'http://54.73.95.15/api')

VERSION = pkg_resources.require('via-api')[0].version
