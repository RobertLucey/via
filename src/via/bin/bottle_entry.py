import argparse
import json
import os

import backoff
import bottle

from via import logger
from via import settings

from via.bin.pull_journeys import main as pull_journeys_main
from via.bin.generate_geojson import main as generate_geojson_main
from via.constants import GEOJSON_DIR
from via.viz.dummy_data import full_journey


@bottle.route('/static/resources/:filename#.*#')
def get_static_resource(filename):
    return bottle.static_file(filename, root='static/resources/')


@bottle.route('/static/templates/:filename#.*#')
def render_page(filename):
    return bottle.template(
        os.path.join('static', 'templates', filename),
        initial_coords=[settings.VIZ_INITIAL_LAT, settings.VIZ_INITIAL_LNG],
        initial_zoom=settings.VIZ_INITIAL_ZOOM
    )


@bottle.route('/favicon.ico')
def get_favicon():
    return get_static_resource('favicon.ico')


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3
)
def pull_journeys():
    pull_journeys_main()


@backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=3
)
def generate_geojson():
    generate_geojson_main()


@bottle.route('/update_journeys')
def update_journeys():
    """
    Call the bin methods to pull new data and generate geojson from them.

    TODO: Add throttling to not hit API limitations
    TODO: Move the helper methods from bin
    TODO: Accept GET params to only pull journeys of a particular type
    """
    logger.info("Update journeys triggered")

    try:
        pull_journeys()
    except Exception as e:
        logger.error(f"Exception pulling journeys: {e}")
        logger.critical("Returning without pulling journeys.")
        return {
            "message": "Pulling journeys failed",
            "status": 500
        }

    logger.info("Journeys successfully pulled")

    try:
        generate_geojson()
    except Exception as e:
        logger.error(f"Exception converting journeys to geojson: {e}")
        logger.critical("Returning without converting journeys.")
        return {
            "message": "Converting journeys failed",
            "status": 500
        }

    logger.info("Journeys successfully parsed to geojson")

    return {
        "status": 200
    }


@bottle.route('/get_journeys')
def get_journeys():
    """
    API call to just get cached journeys. Use update_journeys to get new data.
    """
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
    return render_page('index.tpl')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--port',
        dest='port',
        default=8080
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        dest='debug'
    )
    args = parser.parse_args()

    bottle.debug(args.debug)
    bottle.run(
        host="0.0.0.0",
        port=args.port,
        debug=args.debug,
        reloader=True
    )


if __name__ == '__main__':
    main()
