import os
import uuid
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


def main():
    s3 = boto3.client('s3', region_name=S3_REGION)

    if not os.path.exists(REMOTE_DATA_DIR):
        os.makedirs(REMOTE_DATA_DIR, exist_ok=True)

    journey_ids = []
    for filename in glob.iglob(REMOTE_DATA_DIR + '/**/*', recursive=True):
        journey_ids.append(os.path.splitext(os.path.basename(filename))[0])

    for fn in requests.get(DOWNLOAD_JOURNEYS_URL).json():

        journey_id = os.path.splitext(os.path.basename(fn))[0]

        if journey_id in journey_ids:
            continue

        tmp_fp = f'/tmp/{journey_id}.json'

        s3.download_file(
            'bike-road-quality',
            fn,
            tmp_fp
        )

        journey = Journey.from_file(tmp_fp)

        local_fp = os.path.join(
            REMOTE_DATA_DIR,
            journey.transport_type.lower(),
            fn
        )
        logger.info(f'Putting to {local_fp}')

        os.makedirs(
            os.path.dirname(local_fp),
            exist_ok=True
        )

        shutil.move(
            tmp_fp,
            local_fp
        )


if __name__ == '__main__':
    main()
