import os
import urllib

from road_collisions.constants import COUNTY_MAP

from via import logger
from via.utils import (
    read_json,
    write_json
)
from via.models.collisions.collision import Collisions
from via.geojson.utils import get_point
from via.constants import GEOJSON_DIR


def get_collisions() -> Collisions:
    return Collisions.load_all()


def clean_filters(filters: dict) -> dict:
    return {
        k: v for k, v in filters.items() if v is not None and v != 'all'
    }


def get_filters(transport_type=None, years=False, county=None):
    """

    :kwargs transport_type:
    :kwargs years:
    :kwargs county:
    :return: Tuple of (transport_types, counties, years)
    :rtype: tuple
    """
    transport_types = set()
    if transport_type is None:
        transport_types = {None, 'bicycle', 'car', 'bus'}
    else:
        transport_types = {transport_type}

    counties = list(COUNTY_MAP.values())
    if county is not None:
        counties = [county]

    if years:
        years_list = [None] + sorted(list(range(2005, 2017)), reverse=True)
    else:
        years_list = [None]

    return transport_types, counties, years_list


def retrieve_geojson(
    transport_type=None,
    years=False,
    county=None,
    mode='edge'
):
    """
    :kwarg transport_type:
    :kwarg years:
    :kwarg county:
    :kwarg mode:
        - edge: get geojson data as road data
        - point: get geojson data as points on map
    """
    transport_types, counties, years_list = get_filters(
        transport_type=transport_type,
        years=years,
        county=county
    )

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for county in counties:
        for vehicle_type in transport_types:
            for year in years_list:

                filters = clean_filters({
                    'county': county.lower(),
                    'year': year,
                    'vehicle_type': vehicle_type
                })

                if mode == 'point':
                    filters['mode'] = mode
                elif mode == 'edge':
                    pass
                else:
                    raise NotImplementedError()

                filename = 'collision_' + urllib.parse.urlencode(filters) + '.geojson'
                data = read_json(os.path.join(GEOJSON_DIR, filename))
                geojson['features'].extend(data['features'])

    if geojson['features'] == []:
        # FIXME: bit yucky
        raise FileNotFoundError()

    return geojson


def generate_geojson(
    transport_type=None,
    years=False,
    county=None,
    mode='edge'
):
    """

    :kwarg transport_type:
    :kwarg years:
    :kwarg mode:
        - edge: get geojson data as road data
        - point: get geojson data as points on map
    """
    all_collisions = get_collisions()

    transport_types, counties, years_list = get_filters(
        transport_type=transport_type,
        years=years,
        county=county
    )

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    for county in counties:
        for vehicle_type in transport_types:
            for year in years_list:

                filters = clean_filters({
                    'county': county.lower(),
                    'year': year,
                    'vehicle_type': vehicle_type
                })

                logger.debug('Process collisions geojson: %s', filters)
                collisions = all_collisions.filter(
                    **filters
                )

                if mode == 'point':
                    for collision in collisions:
                        geojson['features'].append(
                            get_point(
                                properties=None,
                                gps=collision.gps
                            )
                        )
                elif mode == 'edge':
                    individual_geojson = collisions.geojson
                    geojson['features'].extend(individual_geojson['features'])
                else:
                    raise NotImplementedError()

                filters['mode'] = mode
                filename = 'collision_' + urllib.parse.urlencode(filters) + '.geojson'
                write_json(os.path.join(GEOJSON_DIR, filename), geojson)

    return geojson
