import datetime
import urllib
from packaging.version import Version

import shapely
from networkx.readwrite import json_graph


def parse_start_date(earliest_date):
    if earliest_date is None:
        return '2021-01'

    if earliest_date < datetime.datetime(2021, 1, 1):
        return '2021-01'

    return earliest_date


def parse_end_date(latest_date):
    if latest_date is None:
        return '2023-12'

    if latest_date > datetime.datetime(2023, 12, 31):
        return '2023-12'

    return latest_date


def generate_basename(
    name=None,
    version=None,
    version_op=None,
    earliest_time=None,
    latest_time=None,
    place=None
):
    data = {
        'transport_type': name,
        'version': version,
        'version_op': version_op,
        'earliest_time': parse_start_date(earliest_time),
        'latest_time': parse_end_date(latest_time),
        'place': place
    }
    if data['version'] in {None, False, '0.0.0', Version('0.0.0')}:
        del data['version']
        del data['version_op']
    if data['place'] is None:
        del data['place']
    return urllib.parse.urlencode(data)


def geojson_from_graph(graph):
    json_links = json_graph.node_link_data(
        graph
    )['links']

    geojson_features = {
        'type': 'FeatureCollection',
        'features': []
    }

    for link in json_links:
        if 'geometry' not in link:
            continue

        feature = {
            'type': 'Feature',
            'properties': {}
        }

        for k in link:
            if k == 'geometry':
                feature['geometry'] = shapely.geometry.mapping(
                    link['geometry']
                )
            else:
                feature['properties'][k] = link[k]
        useless_properties = {
            'oneway',
            'length',
            'osmid',
            'highway',
            'source',
            'target',
            'key',
            'maxspeed',
            'lanes',
            'ref'
        }
        for useless_property in useless_properties:
            try:
                del feature['properties'][useless_property]
            except:
                pass
        geojson_features['features'].append(feature)

    return geojson_features
