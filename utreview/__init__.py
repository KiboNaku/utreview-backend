
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


app = Flask(__name__)
db = SQLAlchemy(app)

app.config.from_pyfile('mail.cfg')

app.config['SECRET_KEY'] = config("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = config("LOCAL_DATABASE_URI")

# app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST")
# app.config['MYSQL_PORT'] = 3306
# app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER")
# app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD")
# app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB")
# app.config['MYSQL_CURSORCLASS'] = os.environ.get("MYSQL_CURSORCLASS")

# mysql = MySQL(app)
# print(mysql)
# cur = mysql.connection.cursor()
# cur.execute("INSERT INTO entries(guestName, content) VALUES(%s, %s)", ("sneha", "is annie"))
# mysql.connection.commit()
# cur.close()

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

# from utreview import models

# course_schema = Schema(index=ID(stored=True), content=TEXT)
# course_ix = create_in("utreview/course_index", course_schema)
# course_writer = course_ix.writer()

# courses = Course.query.all()
# courses_tokens = [str(course).split() for course in courses]

# for course in courses:
#     dept = course.dept

#     course_content = ""
#     course_content += dept.abr + " "
#     course_content += dept.name + " "
#     course_content += course.num + " "
#     course_content += course.name + " "
#     course_writer.add_document(index=str(course.id), content=str(course_content))

# course_writer.commit()

# prof_schema = Schema(index=ID(stored=True), content=TEXT)
# prof_ix = create_in("utreview/prof_index", prof_schema)
# prof_writer = prof_ix.writer()

# profs = Prof.query.all()
# for prof in profs:
#     prof_name = prof.name.split('[, ]')
#     prof_content = ""
#     for string in prof_name:
#         prof_content += string + " "
#     prof_writer.add_document(index=str(prof.id), content=str(prof_content))
    # prof_writer.commit()


# from utreview import review_routes
# from utreview import signup_routes
# from utreview import routes
# from utreview import b_routes
