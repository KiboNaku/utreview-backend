from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utflow.models import *
from utflow import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time


@app.route('/api/populate_results', methods=['POST'])
def populate_results():
    start_time = time.time()
    search = request.get_json()['searchValue']
    print(search)
    search = search.lower()
    search_tokens = search.split()

    courses_list = []
    course_ids = []
    profs_list = []
    prof_ids = []

    if(search == " "):
        print("empty string")
        populate_all(courses_list, profs_list)
        courses = courses_list
        profs = profs_list
        result = jsonify({"courses": courses, "profs": profs})
        elapsed_time = time.time() - start_time
        print(elapsed_time)
        return result

    with course_ix.searcher() as searcher:
        query = QueryParser("content", course_ix.schema).parse(search)
        results = searcher.search(query, limit=50)
        for result in results:
            course_id = int(result["index"])
            if(course_id in course_ids):
                continue
            else:
                course_ids.append(course_id)
                course = Course.query.filter_by(id=course_id).first()
                append_course(course, courses_list, profs_list, prof_ids)
    courses = Course.query.all()
    for course in courses:
        if(search.replace(" ", "") in str(course)):
            if(course.id in course_ids):
                continue
            else:
                course_ids.append(course.id)
                append_course(course, courses_list, profs_list, prof_ids)

    with prof_ix.searcher() as searcher:
        query = QueryParser("content", prof_ix.schema).parse(search)
        results = searcher.search(query, limit=50)

        for result in results:
            prof_id = int(result["index"])
            if(prof_id in prof_ids):
                continue
            else:
                prof_ids.append(prof_id)
                prof = Prof.query.filter_by(id=prof_id).first()
                append_prof(prof, profs_list, courses_list, course_ids)

    courses = courses_list
    profs = profs_list
    if(len(courses_list) < 1):
        courses = "empty"
    if(len(profs_list) < 1):
        profs = "empty"

    result = jsonify({"courses": courses, "profs": profs})
    elapsed_time = time.time() - start_time
    print(elapsed_time)
    return result


def append_course(course, courses_list, profs_list, prof_ids):
    dept = course.dept
    for course_pc in course.pc:
        prof = course_pc.prof
        if(prof.id in prof_ids):
            continue
        prof_ids.append(prof.id)
        prof_object = {
            'id': prof.id,
            'profName': prof.name,
        }
        profs_list.append(prof_object)
    course_object = {
        'courseNum': dept.abr + " " + course.num,
        'courseName': course.name,
        'deptName': dept.name,
    }
    courses_list.append(course_object)


def append_prof(prof, profs_list, courses_list, course_ids):
    for prof_pc in prof.pc:
        course = prof_pc.course
        dept = course.dept
        if(course.id in course_ids):
            continue
        course_ids.append(course_ids)
        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
        }
        courses_list.append(course_object)

    prof_object = {
        'id': prof.id,
        'profName': prof.name,
    }
    profs_list.append(prof_object)


def populate_all(courses_list, profs_list):
    courses = Course.query.all()
    for course in courses:
        dept = course.dept
        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
            'deptName': dept.name,
        }
        courses_list.append(course_object)
    profs = Prof.query.all()
    for prof in profs:
        prof_object = {
            'id': prof.id,
            'profName': prof.name,
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
    # TODO: add user liked and disliked

    rtype = request.get_json()['type']
    name = request.get_json()['name']
    reviews = []

    if rtype == 'user':
        reviews = User.query.filter_by(email=name[0]).first().reviews
    elif rtype == 'prof':
        reviews = Prof.query.filter_by(name=name[0]).first().reviews
    elif rtype == 'course':
        dept_id = Dept.query.filter_by(abr=name[0]).first().id
        reviews = Course.query.filter_by(dept_id=dept_id, num=name[1])

    results = [
        {
            'id': result.id,
            'date_posted': result.date_posted,
            'course_review': result.course_review,
            'professor_review': result.professor_review,

            'user_posted': {
                'major': {
                    'abr': result.user_posted.major.abr,
                    'name': result.user_posted.major.name
                }
            },

            'professor': {
                'name': result.prof.name
            },

            'course': {
                'dept': {
                    'abr': result.course.dept.abr,
                    'name': result.course.dept.name
                },
                'name': result.course.name,
            },

            'course_rating': {
                'approval': result.course_rating.approval,
                'usefulness': result.course_rating.usefulness,
                'difficulty': result.course_rating.difficulty,
                'workload': result.course_rating.workload,
            },

            'professor_rating': {
                'approval': result.course_rating.approval,
                'clear': result.course_rating.clear,
                'engaging': result.course_rating.engaging,
                'grading': result.course_rating.grading,
            },
        }
        
        for result in results
    ]

    result = jsonify({"reviews": results})
    return result


@app.route('/api/get_image', methods=['GET'])
def get_image():
    images = Image.query.all()
    results = dict.fromkeys((range(len(images))))
    i = 0
    for image in images:
        results[i] = {
            'image': image.file_name
        }
        i = i+1

    result = jsonify({"images": results})
    return result


@app.route('/api/update_info', methods=['POST'])
def update_info():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    password = bcrypt.generate_password_hash(
        request.get_json()['password']).decode('utf-8')
    dept = Dept.query.filter_by(name=major).first()
    image_name = request.get_json()['image_file']
    image_file = Image.query.filter_by(file_name=image_name).first()

    user = User.query.filter_by(email=email).first()
    user.first_name = first_name
    user.last_name = last_name
    user.password = password
    user.image_id = image_file.id
    user.major_id = dept.id

    db.session.commit()

    access_token = create_access_token(identity={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'major': dept.name,
        'image_file': image_file.file_name
    })
    result = access_token

    return result
