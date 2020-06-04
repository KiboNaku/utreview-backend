


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser


app = Flask(__name__)
app.config['SECRET_KEY'] = '3640067e2460696327ba681ffea475b1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

from utflow.models import *

schema = Schema(index=ID(stored=True), content=TEXT)
ix = create_in("utflow/index", schema)
writer = ix.writer()

courses = Course.query.all()
courses_tokens = [str(course).split() for course in courses]

for course in courses:
    dept = Dept.query.filter_by(id=course.dept_id).first()

    course_content = ""
    course_content += dept.abr + " "
    course_content += dept.name + " "
    course_content += course.num + " "
    course_content += course.name + " "
    writer.add_document(index=str(course.id), content=str(course_content))

writer.commit()


from utflow import review_routes
from utflow import signup_routes
from utflow import routes
