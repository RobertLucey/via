import os
import boto3

import requests

from via import logger
from via.settings import (
    DOWNLOAD_JOURNEYS_URL,
    S3_REGION
)
from via.constants import REMOTE_DATA_DIR


def main():
    s3 = boto3.client('s3', region_name=S3_REGION)

    if not os.path.exists(REMOTE_DATA_DIR):
        os.makedirs(REMOTE_DATA_DIR, exist_ok=True)

    for fn in requests.get(DOWNLOAD_JOURNEYS_URL).json():

        local_fp = os.path.join(REMOTE_DATA_DIR, fn)
        if not os.path.exists(local_fp):
            logger.info(f'Downloading to {local_fp}')
            s3.download_file(
                'bike-road-quality',
                fn,
                local_fp
            )


if __name__ == '__main__':
    main()
