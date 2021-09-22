from via import logger

from via.bin.pull_journeys import main as pull_journeys_main
from via.bin.generate_geojson import main as generate_geojson_main
from via.constants import GEOJSON_DIR
from via.viz.dummy_data import full_journey

import bottle
import json
import os
import time


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


@bottle.route('/update_journeys')
def update_journeys():
    '''
    Call the bin methods to pull new data and generate geojson from them.
    TODO: Add throttling to not hit API limitations
    TODO: Move the helper methods from bin
    TODO: Accept GET params to only pull journeys of a particular type
    '''
    logger.info("Update journeys triggered")

    # This is real dirty and I'm not happy with it...
    # Should use a retry decorator in utils or similar if this has to be done.
    retry_count = 3

    for attempt_counter in range(retry_count):
        try:
            pull_journeys_main()
            break
        except Exception as e:
            logger.error(f"Exception pulling journeys: {e}")

            if attempt_counter == retry_count - 1:
                logger.critical("Returning without pulling journeys.")
                return {
                    "message": "Pulling journeys failed",
                    "status": 500
                }
            time.sleep(5)

    logger.info("Journeys successfully pulled")

    for attempt_counter in range(retry_count):
        try:
            generate_geojson_main()
            break
        except Exception as e:
            logger.error(f"Exception converting journeys to geojson: {e}")

            if attempt_counter == retry_count - 1:
                logger.critical("Returning without converting journeys.")

                return {
                    "message": "Converting journeys failed",
                    "status": 500
                }
            time.sleep(5)

    logger.info("Journeys successfully parsed to geojson")

    return {
        "status": 200
    }


@bottle.route('/get_journeys')
def get_journeys():
    '''
    API call to just get cached journeys. Use update_journeys to get new data.
    '''
    logger.info("Pulling cached journeys")

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
bottle.run(host="0.0.0.0", port=8080, debug=True, reloader=True)
