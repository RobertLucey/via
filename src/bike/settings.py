import os
import pkg_resources
from packaging import version

MIN_ACC_SCORE = float(os.getenv('MIN_ACC_SCORE', '0.001'))
MIN_PER_JOURNEY_USAGE = float(os.getenv('MIN_PER_JOURNEY_USAGE', '1'))
MIN_METRES_PER_SECOND = float(os.getenv('MIN_METRES_PER_SECOND', '0'))
MAX_METRES_PER_SECOND = float(os.getenv('MAX_METRES_PER_SECOND', '10000'))

MIN_JOURNEY_VERSION = version.parse(os.getenv('MIN_JOURNEY_VERSION', '0.0.0'))
MAX_JOURNEY_VERSION = version.parse(os.getenv('MAX_JOURNEY_VERSION', '999.999.999'))

# FIXME: this but less bad
VERSION = pkg_resources.require('bike')[0].version
