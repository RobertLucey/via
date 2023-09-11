from via.utils import get_journeys


def main():
    for journey in get_journeys():
        print(journey)


if __name__ == "__main__":
    main()
