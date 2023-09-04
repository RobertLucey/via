import argparse
import json
import requests

from via.db import db
from via import logger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    remove_id = lambda x: x if x.pop("_id") else x

    for journey_data in db.raw_journeys.find():
        response = requests.post(
            args.url + "/push_journey", json=remove_id(journey_data)
        )
        if response.status_code == 201:
            logger.info(f'Created: {journey_data["uuid"]}')
        elif response.status_code == 409:
            logger.debug(f'Already exists: {journey_data["uuid"]}')


if __name__ == "__main__":
    main()
