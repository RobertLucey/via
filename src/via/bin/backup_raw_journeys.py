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

    from via.db import db

    with open(args.backup_file, "w") as fh:
        fh.write(
            json.dumps(
                [rm_obj_id(journey_data) for journey_data in db.raw_journeys.find()]
            )
        )


if __name__ == "__main__":
    main()
