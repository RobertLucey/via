import os

METRES_PER_DEGREE = 110574.38855780

LOG_LOCATION = (
    "/var/log/via/via.log"
    if os.getenv("TEST_ENV", "False") == "False"
    else "/tmp/log/via/via.log"
)

USELESS_GEOJSON_PROPERTIES = {
    "highway",
    "reversed",
    "oneway",
    "length",
    "osmid",
    "source",
    "target",
    "key",
    "maxspeed",
    "lanes",
    "ref",
    "access",
}

VALID_JOURNEY_MIN_DISTANCE = 250  # How far the journey must be
VALID_JOURNEY_MIN_POINTS = 10  # How many gps points required in a journey
VALID_JOURNEY_MIN_DURATION = 60  # Only if time is included

EMPTY_GEOJSON = {"type": "FeatureCollection", "features": []}
