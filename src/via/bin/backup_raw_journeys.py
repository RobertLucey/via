import argparse
import json


def rm_obj_id(journey_data):
    del journey_data["_id"]
    return journey_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "backup_file",
        help="Path to the backup json file",
    )
    args = parser.parse_args()

    if not args.backup_file.endswith(".json"):
        raise ValueError("backup file must be a .json file")

    from via.utils import get_mongo_interface
    from via.settings import MONGO_RAW_JOURNEYS_COLLECTION

    mongo_interface = get_mongo_interface()
    with open(args.backup_file, "w") as fh:
        fh.write(
            json.dumps(
                [
                    rm_obj_id(journey_data)
                    for journey_data in getattr(
                        mongo_interface, MONGO_RAW_JOURNEYS_COLLECTION
                    ).find()
                ]
            )
        )


if __name__ == "__main__":
    main()
