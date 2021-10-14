import os
import shutil
import glob

import boto3
import requests

from via import logger
from via.settings import (
    DOWNLOAD_JOURNEYS_URL,
    S3_REGION
)
from via.constants import REMOTE_DATA_DIR
from via.models.journey import Journey


def pull_journeys(cache_graphs=True):
    """

    :kwargs cache_graphs: cache the graphs of pulled journeys so we don't
        need to do it again later when we need them
    """
    s3 = boto3.client('s3', region_name=S3_REGION)

    if not os.path.exists(REMOTE_DATA_DIR):
        os.makedirs(REMOTE_DATA_DIR, exist_ok=True)

    journey_ids = []
    for filename in glob.iglob(REMOTE_DATA_DIR + '/**/*', recursive=True):
        journey_ids.append(os.path.splitext(os.path.basename(filename))[0])

    journey_filenames = requests.get(DOWNLOAD_JOURNEYS_URL).json()
    journey_files_to_download = []

    for filename in journey_filenames:
        journey_id = os.path.splitext(os.path.basename(filename))[0]
        if journey_id in journey_ids:
            continue
        journey_files_to_download.append(filename)

    logger.info(f'Downloading {len(journey_files_to_download)} files')

    for filename in journey_files_to_download:

        journey_id = os.path.splitext(filename)[0]

        tmp_filepath = f'/tmp/{journey_id}.json'

        s3.download_file(
            'bike-road-quality',
            filename,
            tmp_filepath
        )

        journey = Journey.from_file(tmp_filepath)

        if cache_graphs:
            logger.info(f'Caching graphs for {journey_id}')
            journey.bounding_graph

        local_filepath = os.path.join(
            REMOTE_DATA_DIR,
            journey.transport_type.lower(),
            filename
        )
        logger.info(f'Putting to {local_filepath}')

        os.makedirs(
            os.path.dirname(local_filepath),
            exist_ok=True
        )

        shutil.move(
            tmp_filepath,
            local_filepath
        )
