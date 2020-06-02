
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager


app = Flask(__name__)
app.config['SECRET_KEY'] = '3640067e2460696327ba681ffea475b1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

from utflow import routes
from utflow import signup_routes
from utflow import review_routes