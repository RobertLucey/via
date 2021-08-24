import os
import pkg_resources

MIN_ACC_SCORE = float(os.getenv('MIN_ACC_SCORE', '0.001'))
MIN_PER_JOURNEY_USAGE = float(os.getenv('MIN_PER_JOURNEY_USAGE', '1'))
MIN_METRES_PER_SECOND = float(os.getenv('MIN_METRES_PER_SECOND', '0'))
MAX_METRES_PER_SECOND = float(os.getenv('MAX_METRES_PER_SECOND', '10000'))

# FIXME: this but less bad
VERSION = pkg_resources.require('bike')[0].version
