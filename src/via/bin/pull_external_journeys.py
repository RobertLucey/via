from urllib.parse import urlencode
from collections import OrderedDict

import requests

from via.db import db
from via.models.journey import Journey


URLS = [
    # "http://localhost:8000"
]


def main():
    for base_url in URLS:
        query_url = f"{base_url}/get_journey_uuids"

        print(query_url)

        journeys_uuids = requests.get(query_url).json()

        for journey_uuid in journeys_uuids:
            print(journey_uuid)

            query_string = urlencode(OrderedDict(journey_uuid=journey_uuid))
            url = f"{base_url}/get_raw_journey?{query_string}"

            journey_data = requests.get(url).json()

            # Validate the journey
            Journey(
                uuid=journey_data["uuid"],
                data=journey_data["data"],
                transport_type=journey_data["transport_type"],
                suspension=journey_data["suspension"],
                version=journey_data["version"],
            )

            result = db.raw_journeys.find_one(
                {"uuid": journey_data["uuid"]}
            )

            if not result:
                db.raw_journeys.insert_one(
                    journey_data
                )
            else:
                print(f'already exists: {journey_data["uuid"]}')


if __name__ == "__main__":
    main()
