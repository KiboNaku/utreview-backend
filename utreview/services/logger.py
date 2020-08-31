
import datetime
import logging
import os
import sys

from logging.handlers import TimedRotatingFileHandler
from pytz import timezone

DEFAULT_LOG_FOLDER = 'log'
DEFAULT_LOG_FILE_NAME = "daily_backend_flask_app.log"


def init_log():
    """
    initialize a logger
    :return: initialized logger to use for logging purposes
    :rtype: RootLogger
    """
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


def error_log_handler(type, value, tb):
    """
    Function used for overriding the error_handler in the system.
    """
    logger.exception(f"Uncaught exception: {str(value)}")


logger = init_log()
sys.excepthook = error_log_handler
