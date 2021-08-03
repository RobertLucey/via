import pkg_resources

DELETE_ON_SEND = True

SUSPENSION = True

# road mountain commuter electric touring walking / or put in whatever
TRANSPORT_TYPE = 'mountain'


# Only data after 5 minutes of the journey is counted
# Only data up to the last 5 minutes of the journey is counted
MINUTES_TO_CUT = 5


# Haven't decided if this is direct or indirect so check the code, don't
# want to commit to anything yet

# You must move this far from the origin for the data to count
# You must be at least this far away from the end for the data to count
EXCLUDE_METRES_BEGIN_AND_END = 100


# Exclude time from data sent across network
UPLOAD_EXCLUDE_TIME = False

UPLOAD_PARTIAL = False

# When saving upload split the mega journey into this many parts. Influenced by MIN_JOURNEYS_UPLOAD_PARTIALS
# TODO: change to chunks
PARTIAL_SPLIT_INTO = 20

# The min number of journeys needed to send partial journeys for the sake
# of mixing them all together to hide the true route of any one journey
MIN_JOURNEYS_UPLOAD_PARTIALS = 5

PARTIAL_RANDOMIZE_DATA_ORDER = True


UPLOAD_URL = 'https://localhost'


# FIXME: this but less bad
pkg_resources.require('bike')[0].version
