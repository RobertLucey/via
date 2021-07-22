from bike.utils import iter_journeys


def main():

    for journey in iter_journeys(staged=True):
        journey.send()


if __name__ == '__main__':
    main()
