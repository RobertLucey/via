from via.constants import GEOJSON_DIR
from via import logger
from via.viz.dummy_data import full_journey

import bottle
import json
import os


@bottle.route('/hello')
def hello():
    return "Hello!!"


@bottle.route('/')
@bottle.route('/hello/<name>')
def greet(name='Stranger'):
    return bottle.template('Hello {{name}}, how are you??', name=name)


@bottle.route('/static/:filename#.*#')
def send_static(filename):
    return bottle.static_file(filename, root='static/')


@bottle.route('/pull_journeys')
def pull_journeys():
    print("Pulling journeys")

    earliest_time = bottle.request.query.earliest_time
    latest_time = bottle.request.query.latest_time
    journey_type = bottle.request.query.journey_type
    limit = bottle.request.query.limit

    geojson_file = os.path.join(
        GEOJSON_DIR,
        f'{journey_type}.geojson'
    )

    try:
        with open(geojson_file) as fh:
            geojson_data = json.load(fh)
        status = 200
    except Exception as e:
        logger.warning(f'GeoJSON not found at {geojson_file}')
        logger.warning(f'Exception: {e}')
        geojson_data = full_journey

        # Interestingly there's no status code for "Return OK with caveats"
        status = 203

    return {
        'req': {
            'earliest_time': earliest_time,
            'latest_time': latest_time,
            'journey_type': journey_type,
            'limit': limit
        },
        'resp': {
            'geojson': geojson_data
        },
        'status': status
    }


@bottle.route('/')
def send_index():
    return send_static('index.html')


bottle.debug(True)
bottle.run(host="localhost", port=8080, debug=True, reloader=True)
