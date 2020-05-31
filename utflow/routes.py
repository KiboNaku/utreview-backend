from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import *
from utflow import app, db, bcrypt, jwt


@app.route('/api/signup', methods=['POST'])
def register():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    password = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')

    user = User.query.filter_by(email=email).first()
    if user:
        result = jsonify({"error": "An account already exists for this email"})
    else:
        user = User(first_name=first_name, last_name=last_name,
                    email=email, major=major, password=password)
        db.session.add(user)
        db.session.commit()

        result_user = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'major': major
        }
        result = jsonify({'result': result_user})

    return result


@app.route('/api/login', methods=['POST'])
def login():
    email = request.get_json()['email']
    password = request.get_json()['password']

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity = {
            'first_name': user.first_name, 
            'last_name': user.last_name,
            'email': user.email,
            'major': user.major
            })
        result = access_token
    else:
        result = jsonify({"error": "Invalid username and password"})

    return result


@app.route('/api/get-course-num', methods=['GET'])
def getCourseNum():
    result = None
    return result


@app.route('/api/get-prof-name', methods=['GET'])
def getCourseNum():
    result = Prof.query()
    return result


@app.route('/api/review', methods=['POST'])
def review():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    course_review = request.get_json()['course_review']
    prof_review = request.get_json()['prof_review']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']

    course_parsed = course_name.split()
    course_abr = course_parsed[0]
    course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review(user_posted=user.id, course_id=course.id, professor_id=prof.id,
    professor_review=prof_review, course_review=course_review)

    

    result = ""

    return result