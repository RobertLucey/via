import os
import boto3

import requests

from bike.constants import REMOTE_DATA_DIR


def main():
    s3 = boto3.client('s3', region_name='eu-west-1')

    if not os.path.exists(REMOTE_DATA_DIR):
        os.makedirs(REMOTE_DATA_DIR, exist_ok=True)

    for fn in requests.get('https://l7vv5djf9h.execute-api.eu-west-1.amazonaws.com/default/getUUIDs').json():

        local_fp = os.path.join(REMOTE_DATA_DIR, fn)
        if not os.path.exists(local_fp):
            s3.download_file(
                'bike-road-quality',
                fn,
                local_fp
            )


if __name__ == '__main__':
    main()
