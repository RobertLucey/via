import os
import logging
from logging.handlers import RotatingFileHandler

from bike.constants import LOG_LOCATION


logger = logging.Logger('bike', logging.DEBUG)

os.makedirs(
    os.path.dirname(LOG_LOCATION),
    exist_ok=True
)

handler = RotatingFileHandler(
    LOG_LOCATION,
    maxBytes=1000000,
    backupCount=20
)
handler.setFormatter(
    logging.Formatter(
        fmt='%(asctime)s|%(levelname)s| %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
)
logger.addHandler(handler)
