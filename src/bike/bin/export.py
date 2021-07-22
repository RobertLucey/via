from bike.utils import iter_journeys
from bike import logger


def main():
    logger.info('Begin export')

    for journey in iter_journeys(staged=True):
        journey.send()

    logger.info('Finished export')

if __name__ == '__main__':
    main()
