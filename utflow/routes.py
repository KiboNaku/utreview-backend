from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import *
from utflow import app, db, bcrypt, jwt

@app.route('/api/populate_courses', methods=['GET'])
def populate_courses():

    courses = Course.query.all()
    courses_list = []
    for course in courses:
        dept = Dept.query.filter_by(id=course.dept_id).first()
        prof_list = []
        for pc in course.pc:
            prof = Prof.query.filter_by(id=pc.prof_id).first()
            prof_list.append(prof.name)

        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
            'professors': prof_list
        }
        courses_list.append(course_object)

    result = jsonify({"courses": courses_list})

    return result


@app.route('/api/populate_profs', methods=['GET'])
def populate_profs():

    profs = Prof.query.all()
    prof_list = []
    for prof in profs:
        course_list = []
        for pc in prof.pc:
            course = Prof.query.filter_by(id=pc.course_id).first()
            dept = Dept.query.filter_by(id=course.dept_id).first()
            course_list.append(dept.abr + ' ' + course.num)

        prof_object = {
            'id': prof.id,
            'profName': prof.name,
            'taughtCourses': course_list
        }
        prof_list.append(prof_object)

    result = jsonify({"professors": prof_list})
    return result


@app.route('/api/get_course_num', methods=['GET'])
def get_course_num():
    courses = Course.query.all()
    results = dict.fromkeys((range(len(courses))))
    i = 0
    for course in courses:
        dept = Dept.query.filter_by(id=course.dept_id).first()
        results[i] = {
            'id': course.id,
            'num': dept.abr + " " + course.num,
            'name': course.name,
        }
        i = i+1
    
    result = jsonify({"courses": results})
    return result


@app.route('/api/get-profs', methods=['GET'])
def getProfs():
    profs = Prof.query.all()
    results = dict.fromkeys((range(len(profs))))
    i = 0
    for prof in profs:
        results[i] = {
            'id': prof.id,
            'name': prof.name
        }
        i = i+1
    
    result = jsonify({"professors": results})
    return result


@app.route('/api/get_major', methods=['GET'])
def getMajor():
    major = Dept.query.all()
    results = dict.fromkeys((range(len(major))))
    i = 0
    for m in major:
        results[i] = {
            'id': m.id,
            'name': m.name
        }
        i=i+1
        
    result = jsonify({'majors': results})
    return result


@app.route('/api/course_info', methods=['POST'])
def course_info():
    course_name = request.get_json()['courseNum']
    course_parsed = course_name.split()
    course_abr = course_parsed[0]
    course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()

    course_info = {
        'courseDep': course_dept.abr,
        'courseNo': course.num,
        'courseName': course.name,
        'courseDes': course.description
    }
    scores = course.scores
    if len(scores) == 0:
        eCIS = None
    else:
        eCIS = scores[0].avg

    reviews = course.reviews
    if(len(reviews) == 0):
        percentLiked = None
        difficulty = None
        usefulness = None
        workload = None
    else:
        percentLiked = 0
        difficulty = 0
        usefulness = 0
        workload = 0
        for i in range(len(reviews)):
            rating = CourseRating.query.filter_by(
                review_id=reviews[i].id).first()
            if(rating.approval):
                percentLiked += 1
            difficulty += rating.difficulty
            usefulness += rating.usefulness
            workload += rating.workload
        percentLiked = round(percentLiked/len(reviews), 2) * 100
        difficulty = round(difficulty/len(reviews), 1)
        usefulness = round(usefulness/len(reviews), 1)
        workload = round(workload/len(reviews), 1)
    course_rating = {
        'eCIS': eCIS,
        'percentLiked': percentLiked,
        'difficulty': difficulty,
        'usefulness': usefulness,
        'workload': workload
    }

    prof_list = []
    for pc in course.pc:
        prof = Prof.query.filter_by(id=pc.prof_id).first()
        scores = prof.scores
        if len(scores) == 0:
            eCIS = None
        else:
            eCIS = scores[0].avg
        reviews = Review.query.filter_by(professor_id=prof.id, course_id=course.id).all()
        if(len(reviews) == 0):
            percentLiked = None
        else:
            percentLiked = 0
            for i in range(len(reviews)):
                rating = ProfessorRating.query.filter_by(
                    review_id=reviews[i].id).first()
                if(rating.approval):
                    percentLiked += 1
            percentLiked = round(percentLiked/len(reviews), 2) * 100
        prof_obj = {
            'name': prof.name,
            'percentLiked': percentLiked,
            'eCIS': eCIS
        }
        prof_list.append(prof_obj)

    result = jsonify({"course_info": course_info,
                      "course_rating": course_rating,
                      "course_profs": prof_list})

    return result