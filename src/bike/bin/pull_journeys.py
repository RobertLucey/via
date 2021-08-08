import os
import boto3

from bike.constants import REMOTE_DATA_DIR

s3 = boto3.client('s3', region_name='eu-west-1')

paginator = s3.get_paginator('list_objects_v2')

if not os.path.exists(REMOTE_DATA_DIR):
    os.makedirs(REMOTE_DATA_DIR, exist_ok=True)

for page in paginator.paginate(Bucket='bike-road-quality'):
    for file_object in page['Contents']:
        local_fp = os.path.join(REMOTE_DATA_DIR, file_object['Key'])
        if not os.path.exists(local_fp):
            s3.download_file(
                'bike-road-quality',
                file_object['Key'],
                local_fp
            )
