
import json

from decouple import config
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from whoosh.index import create_in
from whoosh.fields import *

from utreview.services.fetch_ftp import key_current, key_next, key_future


def create_app():

    new_app = Flask(__name__)
    new_db = SQLAlchemy(new_app)

    new_app.config['SECRET_KEY'] = config("SECRET_KEY")
    new_app.config['SQLALCHEMY_DATABASE_URI'] = config("LOCAL_DATABASE_URI")

    new_app.config.from_pyfile('mail.cfg')

    return new_app, new_db


def create_ix():

    from utreview.models.course import Course
    from utreview.models.prof import Prof

    course_schema = Schema(index=ID(stored=True), content=TEXT)
    new_course_ix = create_in("utreview/index/course", course_schema)
    course_writer = new_course_ix.writer()

    courses = Course.query.all()
    # courses_tokens = [str(course).split() for course in courses]

    for my_course in courses:

        dept = my_course.dept
        course_content = " ".join([dept.abr, dept.name, my_course.num, my_course.title])
        course_writer.add_document(index=str(my_course.id), content=str(course_content))

    course_writer.commit()

    prof_schema = Schema(index=ID(stored=True), content=TEXT)
    new_prof_ix = create_in("utreview/index/prof", prof_schema)
    prof_writer = new_prof_ix.writer()

    profs = Prof.query.all()
    for my_prof in profs:

        prof_content = " ".join([my_prof.first_name, my_prof.last_name])
        prof_writer.add_document(index=str(my_prof.id), content=str(prof_content))

    prof_writer.commit()

    return new_course_ix, new_prof_ix


def update_sem_vals(sem_path):
    global sem_current
    global sem_next
    global sem_future

    with open(sem_path, 'r') as f:
        sem_dict = json.load(f) 
    
    if sem_dict is not None:
        sem_current = int_or_none(sem_dict[key_current]) 
        sem_next = int_or_none(sem_dict[key_next])
        sem_future = int_or_none(sem_dict[key_future])


def int_or_none(obj):
    try:
        return int(obj)
    except (ValueError, TypeError):
        return None


SPRING_SEM = 2
SUMMER_SEM = 6
FALL_SEM = 9

sem_current, sem_next, sem_future = None, None, None
update_sem_vals('input_data/semester.txt')

app, db = create_app()
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)
course_ix, prof_ix = create_ix()
from utreview.routes import *
