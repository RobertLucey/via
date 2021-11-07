from road_collisions.constants import COUNTY_MAP

from via import logger
from via.models.collisions.collision import Collisions


def get_collisions():
    return Collisions.load_all()


def generate_geojson(transport_type=None, years=False):
    """

    :kwarg transport_type:
    :kwarg years:
    """
    all_collisions = get_collisions()

    transport_types = set()
    if transport_type is None:
        transport_types = {None, 'bicycle', 'car', 'bus'}
    else:
        transport_types = {transport_type}

    for county in COUNTY_MAP.values():
        for vehicle_type in transport_types:

            # get more specific as time goes on for fewer networks to cache

            if years:
                years_list = [None] + sorted(list(range(2005, 2017)), reverse=True)
            else:
                years_list = [None]

            for year in years_list:

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
