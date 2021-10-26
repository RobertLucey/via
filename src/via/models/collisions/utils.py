from road_collisions.constants import COUNTY_MAP

from via import logger
from via.models.collisions.collision import Collisions


def get_collisions():
    return Collisions.load_all()


def generate_geojson():
    all_collisions = get_collisions()

    for vehicle_type in {None, 'bicycle', 'car', 'bus'}:

        # get more specific as time goes on for fewer networks to cache
        for year in [None] + sorted(list(range(2005, 2017)), reverse=True):
            for county in COUNTY_MAP.values():

                filters = {
                    'county': county.lower(),
                    'year': year,
                    'vehicle_type': vehicle_type
                }

                filters = {
                    k: v for k, v in filters.items() if v is not None and v != 'all'
                }

                logger.debug('Process collisions geojson: %s', filters)
                collisions = all_collisions.filter(
                    **filters
                )
                collisions.geojson
