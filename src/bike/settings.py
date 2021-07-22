import pkg_resources


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


# FIXME: this but less bad
pkg_resources.require('bike')[0].version
