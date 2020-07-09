
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


def create_app():

    app = Flask(__name__)
    db = SQLAlchemy(app)

    app.config['SECRET_KEY'] = config("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = config("LOCAL_DATABASE_URI")

    app.config['MAIL_SERVER'] = config("MAIL_SERVER")
    app.config['MAIL_USERNAME'] = config("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = config("MAIL_PASSWORD")
    app.config['MAIL_PORT'] = config("MAIL_PORT")
    app.config['MAIL_USE_SSL'] = config("MAIL_USE_SSL")
    app.config['MAIL_USE_TLS'] = config("MAIL_USE_TLS")

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


app, db = create_app()
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)
course_ix, prof_ix = create_ix()
