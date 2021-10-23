import bottle

from via import logger

from via.models.collisions.utils import get_collisions

COLLISIONS = get_collisions()

@bottle.route('/collisions/get_geojson')
def get_geojson():
    logger.info('Getting collision GeoJSON')

    # TODO: filters

    filters = {'county': 'dublin'}

    dublin_collisions = COLLISIONS.filter(**filters)
    return dublin_collisions.geojson
