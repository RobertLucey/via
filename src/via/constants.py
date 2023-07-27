import os

METRES_PER_DEGREE = 110574.38855780

LOG_LOCATION = (
    "/var/log/via/via.log"
    if os.getenv("TEST_ENV", "False") == "False"
    else "/tmp/log/via/via.log"
)

POLY_POINT_BUFFER = 0.002

HIGHWAYS_TO_EXCLUDE = {
    "footway",
    "steps",
    "corridor",
    "sidewalk",
    "crossing",
    "driveway",
}

USELESS_GEOJSON_PROPERTIES = {
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


COUNTY_REGION_MAP = {
    "carlow": "leinster",
    "dublin": "leinster",
    "kildare": "leinster",
    "kilkenny": "leinster",
    "laois": "leinster",
    "longford": "leinster",
    "louth": "leinster",
    "meath": "leinster",
    "offaly": "leinster",
    "westmeath": "leinster",
    "wexford": "leinster",
    "wicklow": "leinster",
}

VALID_JOURNEY_MIN_DISTANCE = 250  # How far the journey must be
VALID_JOURNEY_MIN_POINTS = 10  # How many gps points required in a journey
VALID_JOURNEY_MIN_DURATION = 60  # Only if time is included
