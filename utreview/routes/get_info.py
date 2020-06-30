from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time


@app.route('/api/get_course_num', methods=['GET'])
def get_course_num():
    courses = Course.query.all()
    results = dict.fromkeys((range(len(courses))))
    i = 0
    for course in courses:
        dept = course.dept
        results[i] = {
            'id': course.id,
            'dept': dept.abr,
            'num': course.num,
            'title': course.title,
        }
        i = i+1

    result = jsonify({"courses": results})
    return result


@app.route('/api/get_major', methods=['GET'])
def get_major():
    majors = Dept.query.all()
    results = dict.fromkeys((range(len(majors))))
    i = 0
    for m in majors:
        results[i] = {
            'id': m.id,
            'abr': m.abr,
            'name': m.name
        }
        i = i+1

    result = jsonify({"majors": results})
    return result


@app.route('/api/get_profs', methods=['GET'])
def get_profs():
    profs = Prof.query.all()
    results = dict.fromkeys((range(len(profs))))
    i = 0
    for prof in profs:
        results[i] = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name
        }
        i = i+1

    result = jsonify({"professors": results})
    return result


@app.route('/api/get_profile_pic', methods=['GET'])
def get_profile_pic():
    profile_pics = ProfilePic.query.all()
    results = dict.fromkeys((range(len(profile_pics))))
    i = 0
    for profile_pic in profile_pics:
        results[i] = {
            'profile_pic': profile_pic.file_name
        }
        i = i+1

    result = jsonify({"profile_pics": results})
    return result

@app.route('/api/review_list', methods=['POST'])
def review_list():
    # TODO: add user liked and disliked

    rtype = request.get_json()['type']
    name = request.get_json()['name']
    reviews = []

    if rtype == 'user':
        reviews = User.query.filter_by(email=name[0]).first().reviews
    elif rtype == 'prof':
        reviews = Prof.query.filter_by(first_name=name[0], last_name=name[1]).first().reviews
    elif rtype == 'course':
        dept_id = Dept.query.filter_by(abr=name[0]).first().id
        reviews = Course.query.filter_by(dept_id=dept_id, num=name[1])

    results = [
        {
            'id': result.id,
            'date_posted': result.date_posted,
            'semester': result.semester,
            'course_comments': result.course_review.comments,
            'professor_comments': result.prof_review.comments,

            'user_posted': {
                'major': {
                    'abr': result.author.major.abr,
                    'name': result.author.major.name
                }
            },

            'professor': {
                'firstName': result.prof_review.prof.first_name,
                'lastName': result.prof_review.prof.last_name
            },

            'course': {
                'dept': {
                    'abr': result.course_review.course.dept.abr,
                    'name': result.course_review.course.dept.name
                },
                'num': result.course_review.course.num,
                'title': result.course_review.course.title,
            },

            'course_rating': {
                'approval': result.course_review.approval,
                'usefulness': result.course_review.usefulness,
                'difficulty': result.course_review.difficulty,
                'workload': result.course_review.workload,
            },

            'professor_rating': {
                'approval': result.prof_review.approval,
                'clear': result.prof_review.clear,
                'engaging': result.prof_review.engaging,
                'grading': result.prof_review.grading,
            },
        }
        
        for result in reviews
    ]

    result = jsonify({"reviews": results})
    return result


@app.route('/api/update_info', methods=['POST'])
def update_info():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    password_hash = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')
    dept = Dept.query.filter_by(name=major).first()
    profile_name = request.get_json()['profile_pic']
    profile_pic = ProfilePic.query.filter_by(file_name=profile_name).first()

    user = User.query.filter_by(email=email).first()
    user.first_name = first_name
    user.last_name = last_name
    user.password_hash = password_hash
    user.profile_pic_id = profile_pic.id
    user.major_id = dept.id

    db.session.commit()

    access_token = create_access_token(identity={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'major': dept.name,
        'profile_pic': profile_pic.file_name
    })
    result = access_token

    return result