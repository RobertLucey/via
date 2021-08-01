import os


BASE_PATH = '/opt/bike/' if os.getenv('TEST_ENV', 'False') == 'False' else '/tmp/bike'

DATA_DIR = os.path.join(BASE_PATH, 'data')
STAGED_DATA_DIR = os.path.join(DATA_DIR, 'staged')
SENT_DATA_DIR = os.path.join(DATA_DIR, 'sent')

LOG_LOCATION = '/var/log/bike/bike.log' if os.getenv('TEST_ENV', 'False') == 'False' else '/tmp/log/bike/bike.log'

DEFAULT_EDGE_COLOUR = '#E1E1E1'

POLY_POINT_BUFFER = 0.002
