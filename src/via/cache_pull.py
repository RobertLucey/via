import os
import re
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
    BASE_DIR,
    CACHE_DIR,
    EDGE_CACHE_DIR,
    NETWORK_CACHE_DIR,
    BOUNDING_GRAPH_GDFS_CACHE
)


def download_cache():
    logger.info('Downloading cache')
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
        logger.warning(
            'Pulling the most recent (older) cache which may not be compatible. Current %s Pulling %s',
            VERSION,
            pull_version[0]
        )

    s3.download_file(
        PREPARED_CACHE_BUCKET,
        pull_version[1],
        os.path.join(BASE_DIR, f'cache_{pull_version[1]}')
    )


def extract_cache():
    logger.info('Extracting cache')
    cache_files = [
        f for f in os.listdir(BASE_DIR) if all([
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

    latest_cache_filepath = os.path.join(BASE_DIR, latest_cache_file)
    with zipfile.ZipFile(latest_cache_filepath, 'r') as zip_ref:
        zip_ref.extractall(BASE_DIR)

    # make sure that the version numbers of whatever cache we downloaded
    # are changed to the current version so that the caches can be picked up
    for root, dirs, files in os.walk(CACHE_DIR):
        for dir_name in dirs:
            original = os.path.join(root, dir_name)
            new_dir = re.sub(r'/\d+\.\d+\.\d+/?', f'/{VERSION}/', original)
            shutil.move(original, new_dir)


def is_cache_already_pulled() -> bool:
    """
    Determine if there is already a valid cache to use

    Could be smarter about this and see if the cache is somewhat full
    """

    already_pulled = all([
        os.path.exists(os.path.join(EDGE_CACHE_DIR, VERSION)),
        os.path.exists(os.path.join(NETWORK_CACHE_DIR, VERSION)),
        os.path.exists(os.path.join(BOUNDING_GRAPH_GDFS_CACHE, VERSION)),
    ])
    if already_pulled:
        logger.info('Assuming the cache is up to date')
    else:
        logger.warning('Cache is not up to date')
    return already_pulled
