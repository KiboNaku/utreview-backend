from flask import render_template, url_for, flash, redirect
from utflow import app
from utflow.models import *

@app.route("/")
@app.route("/home")
def home():
    depts = Dept.query.all()
    return render_template('home.html', depts=depts) 
