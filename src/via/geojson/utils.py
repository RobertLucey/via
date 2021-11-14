import datetime
import os
import urllib
from packaging.version import Version
import dateutil.parser

import boto3
from botocore import UNSIGNED
from botocore.client import Config

import shapely
from networkx.readwrite import json_graph

from via.settings import (
    S3_REGION,
    PREPARED_GEOJSON_BUCKET
)
from via.constants import (
    GEOJSON_DIR,
    USELESS_GEOJSON_PROPERTIES
)


def parse_start_date(earliest_date):
    if earliest_date is None:
        return '2021-01-01'

    if isinstance(earliest_date, str):
        earliest_date = dateutil.parser.parse(earliest_date)
        print('now: %s' % (earliest_date))

    if isinstance(earliest_date, datetime.date):
        earliest_date = datetime.datetime.combine(
            earliest_date,
            datetime.datetime.min.time()
        )

    if isinstance(earliest_date, datetime.datetime):
        earliest_date = datetime.datetime.combine(
            earliest_date.date(),
            datetime.datetime.min.time()
        )

        if earliest_date < datetime.datetime(2021, 1, 1):
            earliest_date = datetime.datetime(2021, 1, 1)

        print('aaa: %s' % (earliest_date))

    return str(earliest_date.date())


def parse_end_date(latest_date):
    if latest_date is None:
        return '2023-12-31'

    if isinstance(latest_date, str):
        latest_date = dateutil.parser.parse(latest_date)

    if isinstance(latest_date, datetime.date):
        latest_date = datetime.datetime.combine(
            latest_date,
            datetime.datetime.min.time()
        )

    if isinstance(latest_date, datetime.datetime):
        latest_date = datetime.datetime.combine(
            latest_date.date(),
            datetime.datetime.min.time()
        )

        if latest_date > datetime.datetime(2023, 12, 31):
            latest_date = datetime.datetime(2023, 12, 31)

    return str(latest_date.date())


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


def geojson_from_graph(graph, must_include_props=None):
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
        for useless_property in USELESS_GEOJSON_PROPERTIES:
            if useless_property in feature.get('properties', {}).keys():
                del feature['properties'][useless_property]
        geojson_features['features'].append(feature)

    if must_include_props is not None:
        geojson_features['features'] = [
            f for f in geojson_features['features'] if len(set(f['properties'].keys()).intersection(set(must_include_props))) == len(must_include_props)
        ]

    return geojson_features


def download_prepared_geojson():
    os.makedirs(
        GEOJSON_DIR,
        exist_ok=True
    )

    s3 = boto3.client(
        's3',
        region_name=S3_REGION,
        config=Config(signature_version=UNSIGNED)
    )

    paginator = s3.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=PREPARED_GEOJSON_BUCKET):
        for key in result.get('Contents', []):
            s3.download_file(
                PREPARED_GEOJSON_BUCKET,
                key['Key'],
                os.path.join(GEOJSON_DIR, key['Key'])
            )
            os.utime(
                os.path.join(
                    GEOJSON_DIR,
                    key['Key']
                ),
                (
                    key['LastModified'].timestamp(),
                    key['LastModified'].timestamp()
                )
            )


def get_point(properties=None, gps=None):
    return {
        'type': 'Feature',
        'properties': properties if isinstance(properties, dict) else {},
        'geometry': {
            'type': 'Point',
            'coordinates': [gps.lng, gps.lat]
        }
    }
