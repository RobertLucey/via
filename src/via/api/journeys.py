import bottle

from via import logger

from via.pull_journeys import pull_journeys
from via.geojson import (
    generate,
    retrieve
)


@bottle.route('/journeys/update_journeys')
def pull_journeys_api():
    logger.info('Update journeys triggered')
    pull_journeys()
    logger.info('Journeys successfully pulled')
    return {
        'status': 200
    }


@bottle.route('/journeys/generate_geojson')
def generate_geojson_api():
    logger.info('Generate geojson triggered')
    generate.generate_geojson()
    logger.info('Journeys successfully parsed to geojson')
    return {
        'status': 200
    }


@bottle.route('/journeys/get_geojson')
def get_geojson():
    logger.info('Pulling cached journeys')

    earliest_time = bottle.request.query.earliest_time
    latest_time = bottle.request.query.latest_time
    journey_type = bottle.request.query.journey_type

    try:
        data = retrieve.get_geojson(
            journey_type,
            earliest_time=earliest_time,
            latest_time=latest_time,
            place=None,  # TODO
            version=None,  # TODO
            version_op=None,  # TODO
        )
    except FileNotFoundError:
        # TODO: generate and serve back
        return {
            'status': 404
        }
    else:
        return {
            'data': data,
            'status': 200
        }
