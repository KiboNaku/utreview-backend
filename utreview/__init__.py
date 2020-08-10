
import os
from decouple import config
from flask import Flask
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import json
from utreview.services.fetch_ftp import key_current, key_next, key_future
from utreview.database.scheduled_course import int_or_none
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
import datetime
import pytz
from pytz import timezone


DEFAULT_LOG_FOLDER = 'log'
DEFAULT_LOG_FILE_NAME = "daily_backend_flask_app.log"

def create_app():

    app = Flask(__name__)
    db = SQLAlchemy(app)

    app.config['SECRET_KEY'] = config("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = config("LOCAL_DATABASE_URI")

    app.config.from_pyfile('mail.cfg')

    return app, db


def create_ix():

    from utreview.models.course import Course
    from utreview.models.prof import Prof

    course_schema = Schema(index=ID(stored=True), content=TEXT)
    course_ix = create_in("utreview/index/course", course_schema)
    course_writer = course_ix.writer()

    courses = Course.query.all()
    courses_tokens = [str(course).split() for course in courses]

    for course in courses:

        dept = course.dept
        course_content = " ".join([dept.abr, dept.name, course.num, course.title])
        course_writer.add_document(index=str(course.id), content=str(course_content))

    course_writer.commit()

    prof_schema = Schema(index=ID(stored=True), content=TEXT)
    prof_ix = create_in("utreview/index/prof", prof_schema)
    prof_writer = prof_ix.writer()

    profs = Prof.query.all()
    for prof in profs:

        prof_content = " ".join([prof.first_name, prof.last_name])
        prof_writer.add_document(index=str(prof.id), content=str(prof_content))

    prof_writer.commit()

    return course_ix, prof_ix


def update_sem_vals(sem_path):

    global sem_current
    global sem_next
    global sem_future

    sem_dict = None

    with open(sem_path, 'r') as f:
        sem_dict = json.load(f) 
    
    if sem_dict is None:
        return None, None, None
    return int_or_none(sem_dict[key_current]), int_or_none(sem_dict[key_next]), int_or_none(sem_dict[key_future])


def init_log():

    from pytz import utc
    def customTime(*args):
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

    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
    log_formatter.converter = customTime
    
    time_rotating_handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1)
    time_rotating_handler.suffix = "%Y%m%d"
    time_rotating_handler.setFormatter(log_formatter)
    logger.addHandler(time_rotating_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.setLevel(logging.DEBUG)

    return logger


sem_current, sem_next, sem_future = update_sem_vals('semester.txt')
logger = init_log()

app, db = create_app()
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)
course_ix, prof_ix = create_ix()
