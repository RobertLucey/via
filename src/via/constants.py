import os

METRES_PER_DEGREE = 110574.38855780

BASE_DIR = '/opt/via/' if os.getenv('TEST_ENV', 'False') == 'False' else '/tmp/via'

DATA_DIR = os.path.join(BASE_DIR, 'data')
GENERATED_DIR = os.path.join(BASE_DIR, 'generated')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

REMOTE_DATA_DIR = os.path.join(DATA_DIR, 'raw')

EDGE_CACHE_NAME = 'edge_cache'
NETWORK_CACHE_NAME = 'network_cache'
BOUNDING_GRAPH_GDFS_NAME = 'bounding_graph_gdfs_cache'

EDGE_CACHE_DIR = os.path.join(CACHE_DIR, EDGE_CACHE_NAME)
NETWORK_CACHE_DIR = os.path.join(CACHE_DIR, NETWORK_CACHE_NAME)
BOUNDING_GRAPH_GDFS_CACHE = os.path.join(CACHE_DIR, BOUNDING_GRAPH_GDFS_NAME)

GEOJSON_DIR = os.path.join(GENERATED_DIR, 'geojson')

LOG_LOCATION = '/var/log/via/via.log' if os.getenv('TEST_ENV', 'False') == 'False' else '/tmp/log/via/via.log'

DEFAULT_EDGE_COLOUR = '#E1E1E1'

POLY_POINT_BUFFER = 0.002

HIGHWAYS_TO_EXCLUDE = {
    'footway',
    'steps',
    'corridor',
    'sidewalk',
    'crossing',
    'driveway'
}

USELESS_GEOJSON_PROPERTIES = {
    'oneway',
    'length',
    'osmid',
    'source',
    'target',
    'key',
    'maxspeed',
    'lanes',
    'ref',
    'access'
}
