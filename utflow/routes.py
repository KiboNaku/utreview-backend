from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import *
from utflow import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser


@app.route('/api/populate_results', methods=['POST'])
def populate_results():

    search = request.get_json()['searchValue']
    search = search.lower()
    search_tokens = search.split()

    courses_list = []
    course_ids = []
    profs_list = []
    prof_ids = []

    with course_ix.searcher() as searcher:
        query = QueryParser("content", course_ix.schema).parse(search)
        results = searcher.search(query, limit=50)
        for result in results:
            course_id = int(result["index"])
            if(course_id in course_ids):
                continue
            else:
                course_ids.append(course_id)
                append_course(course_id, courses_list, profs_list, prof_ids)

    courses = Course.query.all()
    for course in courses:
        if(search.replace(" ", "") in str(course)):
            if(course.id in course_ids):
                continue
            else:
                course_ids.append(course.id)
                append_course(course.id, courses_list, profs_list, prof_ids)

    with prof_ix.searcher() as searcher:
        query = QueryParser("content", prof_ix.schema).parse(search)
        results = searcher.search(query, limit=50)

        for result in results:
            prof_id = int(result["index"])
            if(prof_id in prof_ids):
                continue
            else:
                prof_ids.append(prof_id)
                append_prof(prof_id, profs_list, courses_list, course_ids)

    courses = courses_list
    profs = profs_list
    if(len(courses_list) < 1):
        courses = "empty"
    if(len(profs_list) < 1):
        profs = "empty"

    result = jsonify({"courses": courses, "profs": profs})
    return result


def append_course(course_id, courses_list, profs_list, prof_ids):
    course = Course.query.filter_by(id=course_id).first()
    dept = Dept.query.filter_by(id=course.dept_id).first()
    prof_list = []
    for course_pc in course.pc:
        prof = Prof.query.filter_by(id=course_pc.prof_id).first()
        prof_list.append(prof.name)
        if(prof.id in prof_ids):
            continue
        prof_ids.append(prof.id)
        course_list = []
        for prof_pc in prof.pc:
            prof_course = Prof.query.filter_by(id=prof_pc.course_id).first()
            prof_dept = Dept.query.filter_by(id=prof_course.dept_id).first()
            course_list.append(prof_dept.abr + ' ' + prof_course.num)

        prof_object = {
            'id': prof.id,
            'profName': prof.name,
            'taughtCourses': course_list
        }
        profs_list.append(prof_object)
    course_object = {
        'courseNum': dept.abr + " " + course.num,
        'courseName': course.name,
        'deptName': dept.name,
        'professors': prof_list
    }
    courses_list.append(course_object)


def append_prof(prof_id, profs_list, courses_list, course_ids):
    prof = Prof.query.filter_by(id=prof_id).first()
    course_list = []
    for prof_pc in prof.pc:
        course = Prof.query.filter_by(id=prof_pc.course_id).first()
        dept = Dept.query.filter_by(id=course.dept_id).first()
        course_list.append(dept.abr + ' ' + course.num)
        if(course.id in course_ids):
            continue
        course_ids.append(course_ids)
        prof_list = []
        for course_pc in course.pc:
            course_prof = Prof.query.filter_by(id=course_pc.prof_id).first()
            prof_list.append(course_prof.name)
        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
            'professors': prof_list
        }
        courses_list.append(course_object)

    prof_object = {
        'id': prof.id,
        'profName': prof.name,
        'taughtCourses': course_list
    }
    profs_list.append(prof_object)


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
            'name': prof.name
        }
        i = i+1

    result = jsonify({"professors": results})
    return result


@app.route('/api/course_info', methods=['POST'])
def course_info():
    course_name = request.get_json()['courseNum']
    logged_in = request.get_json()['loggedIn']
    user_email = request.get_json()['userEmail']
    if(logged_in):
        curr_user = User.query.filter_by(email=user_email).first()
    course_parsed = course_name.split()
    if(len(course_parsed) == 3):
        course_abr = course_parsed[0] + " " + course_parsed[1]
        course_no = course_parsed[2]
    else:
        if(len(course_parsed[0]) == 1):
            course_abr = course_parsed[0] + "  "
        elif(len(course_parsed[0]) == 2):
            course_abr = course_parsed[0] + " "
        else:
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
    review_list = []
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
            user = User.query.filter_by(id=reviews[i].user_posted).first()
            prof = Prof.query.filter_by(id=reviews[i].professor_id).first()
            user_dept = Dept.query.filter_by(id=user.major_id).first()
            num_liked = 0
            num_disliked = 0
            like_pressed = False
            dislike_pressed = False
            for like in reviews[i].users_liked:
                num_liked += 1
                if(logged_in):
                    if(curr_user.id == like.user_id):
                        like_pressed = True

            for dislike in reviews[i].users_disliked:
                num_disliked += 1
                if(logged_in):
                    if(curr_user.id == dislike.user_id):
                        dislike_pressed = True
            review_object = {
                'key': reviews[i].id,
                'review': reviews[i].course_review,
                'liked': rating.approval,
                'usefulness': rating.usefulness,
                'difficulty': rating.difficulty,
                'workload': rating.workload,
                'userMajor': user_dept.name,
                'profPic': "https://images.dog.ceo/breeds/pembroke/n02113023_12785.jpg",
                'profName': prof.name,
                'numLiked': num_liked,
                'numDisliked': num_disliked,
                'likePressed': like_pressed,
                'dislikePressed': dislike_pressed,
                'date': reviews[i].date_posted.strftime("%m/%d/%Y")
            }
            review_list.append(review_object)
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
        reviews = Review.query.filter_by(
            professor_id=prof.id, course_id=course.id).all()
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
                      "course_profs": prof_list,
                      "course_reviews": review_list})

    return result


@app.route('/api/review_list', methods=['POST'])
def review_list():
    reviews = Review.query.all()
    results = dict.fromkeys((range(len(reviews))))
    i = 0
    for review in reviews:
        results[i] = {
            'id': review.id,
        }
        i = i+1

    result = jsonify({"reviews": results})
    return result
