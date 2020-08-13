
import datetime
import logging
import os

from logging.handlers import TimedRotatingFileHandler
from pytz import timezone

DEFAULT_LOG_FOLDER = 'log'
DEFAULT_LOG_FILE_NAME = "daily_backend_flask_app.log"


def init_log():
    from pytz import utc

    def custom_time(*args):
        utc_dt = utc.localize(datetime.datetime.utcnow())
        custom_tz = timezone("US/Central")
        converted = utc_dt.astimezone(custom_tz)
        return converted.timetuple()

    # create log folder if doesn't exist
    if not os.path.isdir(DEFAULT_LOG_FOLDER):
        os.mkdir(DEFAULT_LOG_FOLDER)

    log_path = os.path.join(DEFAULT_LOG_FOLDER, DEFAULT_LOG_FILE_NAME)

    # customize logger
    logger = logging.getLogger()

    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
                                      datefmt="%m/%d/%Y %I:%M:%S %p %Z")
    log_formatter.converter = custom_time

    time_rotating_handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1)
    time_rotating_handler.suffix = "%Y%m%d"
    time_rotating_handler.setFormatter(log_formatter)
    logger.addHandler(time_rotating_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.setLevel(logging.DEBUG)

    return logger


logger = init_log()
