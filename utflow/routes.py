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
    dept = Dept.query.filter_by(name=major).first()

    user = User.query.filter_by(email=email).first()
    if user:
        result = jsonify({"error": "An account already exists for this email"})
    else:
        user = User(first_name=first_name, last_name=last_name,
                    email=email, major=major, password=password, major_id=dept.id)
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
        access_token = create_access_token(identity={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'major': user.major
        })
        result = access_token
    else:
        result = jsonify({"error": "Invalid username and password"})

    return result


@app.route('/api/get-depts', methods=[GET])
def getDepts():
    result = Dept.query.all()
    return result


@app.route('/api/get-courses', methods=['GET'])
def getCourses():
    result = Course.query.all()
    return result


@app.route('/api/get-profs', methods=['GET'])
def getProfs():
    result = Prof.query.all()
    return result


@app.route('/api/new_review', methods=['POST'])
def new_review():
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
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review(user_posted=user.id, course_id=course.id, professor_id=prof.id,
                    professor_review=prof_review, course_review=course_review)

    db.session.add(review)
    db.session.commit()

    course_rating = CourseRating(review_id=review.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, workload=course_workload)
    prof_rating = ProfessorRating(review_id=review.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading)

    db.session.add(course_rating)
    db.session.add(prof_rating)
    db.session.commit()

    result_review = {
        'user_email': user_email,
        'prof_name': prof_name,
        'course_name': course_name
    }
    result = jsonify({'result': result_review})

    return result

@app.route('/api/duplicate_review', methods=['POST'])
def duplicate_review():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']

    course_parsed = course_name.split()
    course_abr = course_parsed[0]
    course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review.query.filter_by(user_posted=user.id, 
    professor_id=prof.id, course_id=course.id).first()

    if review:
        result = jsonify({'error': "Review for this course/prof combination already exists for this user"})
    else:
        result_review = {
            'user_email': user_email,
            'prof_name': prof_name,
            'course_name': course_name
        }
        result = jsonify({'result': result_review})

    return result

@app.route('/api/edit_review', methods=['POST'])
def edit_review():
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
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review.query.filter_by(user_posted=user.id, 
    professor_id=prof.id, course_id=course.id).first()
    
    prev_course_rating = CourseRating.query.filter_by(review_id=review.id)
    prev_prof_rating = ProfessorRating.query.filter_by(review_id=review.id)

    db.session.delete(prev_course_rating)
    db.session.delete(prev_prof_rating)
    db.session.commit()

    course_rating = CourseRating(review_id=review.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, workload=course_workload)
    prof_rating = ProfessorRating(review_id=review.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading)

    db.session.add(course_rating)
    db.session.add(prof_rating)
    db.session.commit()

    result_review = {
        'user_email': user_email,
        'prof_name': prof_name,
        'course_name': course_name
    }
    result = jsonify({'result': result_review})

    return result
