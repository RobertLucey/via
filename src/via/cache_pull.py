import os
import zipfile
import shutil
from packaging import version

import boto3
from botocore import UNSIGNED
from botocore.client import Config

from via import logger
from via.settings import (
    S3_REGION,
    PREPARED_CACHE_BUCKET,
    VERSION
)
from via.constants import (
    BASE_PATH,
    CACHE_DIR
)


def download_cache():
    os.makedirs(
        CACHE_DIR,
        exist_ok=True
    )

    s3 = boto3.client(
        's3',
        region_name=S3_REGION,
        config=Config(signature_version=UNSIGNED)
    )

    available_versions = []

    paginator = s3.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=PREPARED_CACHE_BUCKET):
        for obj in result.get('Contents', []):
            key = obj['Key']
            try:
                available_versions.append(
                    (
                        version.parse(os.path.splitext(key)[0]),
                        key
                    )
                )
            except:
                pass

    sorted_versions = sorted(
        available_versions,
        key=lambda x: x[1],
        reverse=True
    )
    valid_versions = [
        v for v in sorted_versions if v[0] <= version.parse(VERSION)
    ]

    pull_version = valid_versions[0]

    if pull_version[0] != version.parse(VERSION):
        logger.warn(
            'Pulling an older cache which may not be compatible. Current %s Pulling %s',
            VERSION,
            pull_version[0]
        )

    s3.download_file(
        PREPARED_CACHE_BUCKET,
        pull_version[1],
        os.path.join(BASE_PATH, f'cache_{pull_version[1]}')
    )


def extract_cache():
    cache_files = [
        f for f in os.listdir(BASE_PATH) if all([
            f.startswith('cache_'),
            f.endswith('.zip')
        ])
    ]

    latest_cache_file = sorted(
        cache_files,
        key=lambda x: version.parse(os.path.splitext(x.split('_')[-1])[0]),
        reverse=True
    )[0]

    shutil.rmtree(CACHE_DIR, ignore_errors=True)

    latest_cache_filepath = os.path.join(BASE_PATH, latest_cache_file)
    with zipfile.ZipFile(latest_cache_filepath, 'r') as zip_ref:
        zip_ref.extractall(BASE_PATH)


def is_cache_already_pulled():
    return all([
        os.path.exists(os.path.join(CACHE_DIR, 'edge_cache')),
        os.path.exists(os.path.join(CACHE_DIR, 'network_cache')),
        os.path.exists(os.path.join(CACHE_DIR, 'bounding_graph_gdfs_cache')),
        # TODO: check size of dir or something
    ])
