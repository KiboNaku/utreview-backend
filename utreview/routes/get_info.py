import timeago, datetime
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

@app.route('/api/get_courses', methods=['POST'])
def get_courses():
    """
    Gets list of all courses, filtered by a semester

    Args:
        semesterId (int): semester id,
        all (boolean): if true, returns all courses, if false, filter by semester

    Returns:
        result (list): list of courses
        course_obj = {
            'id' (int): course id,
            'dept' (string): dept abr,
            'num' (string): course num,
            'title' (string): course title,
            'topicId' (int): course topic id (if applicable)
            'topicNum' (int): course topic number
        }
    """
    sem_id = request.get_json()['semesterId']
    get_all = request.get_json()['all']
    course_ids = []
    courses = []
    topics = []
    prof_ids = []
    profs = []
    if(get_all):
        courses_list = Course.query.all()
        for course in courses_list:
            dept = course.dept
            course_obj = {
                'id': course.id,
                'dept': dept.abr,
                'num': course.num,
                'title': course.title,
                'topicId': course.topic_id,
                'topicNum': course.topic_num
            }   
            if(course.topic_num > 0):
                topics.append(course_obj)
            else:
                courses.append(course_obj)
    else:
        semester = Semester.query.filter_by(id=sem_id).first()
        prof_course_sem = semester.prof_course_sem
        
        for listing in prof_course_sem:
            course = listing.prof_course.course
            prof = listing.prof_course.prof
            if(course.id not in course_ids):
                dept = course.dept.abr
                course_ids.append(course.id)
                course_obj = {
                    'id': course.id,
                    'dept': dept,
                    'num': course.num,
                    'title': course.title,
                    'topicId': course.topic_id,
                    'topicNum': course.topic_num
                }
                if(course.topic_num > 0):
                    topics.append(course_obj)
                elif(course.topic_num == 0):
                    topics.append(course_obj)
                    courses.append(course_obj)
                else:
                    courses.append(course_obj)
            
            if(prof.id not in prof_ids):
                prof_ids.append(prof.id)
                prof_obj = {
                    'id': prof.id,
                    'firstName': prof.first_name,
                    'lastName': prof.last_name
                }
                profs.append(prof_obj)
    result = jsonify({"courses": courses, "topics": topics, "profs": profs})
    return result


@app.route('/api/get_topics', methods=['POST'])
def get_topics():
    """
    Gets list of all topics, filtered by a topic id and semester id, if semester id
    is null, disregard the semester

    Args:
        topicId (int): topic id

    Returns:
        result (list): list of topics
        course_obj = {
            'id' (int): course id,
            'dept' (string): dept abr,
            'num' (string): course num,
            'title' (string): course title,
            'topicId' (int): course topic id (if applicable)
        }
    """
    topic_id = request.get_json()['topicId']
    sem_id = request.get_json()['semesterId']
    topics = []
    topic_ids = []
    profs = []
    prof_ids = []
    if(sem_id == None):
        topic = Topic.query.filter_by(id=topic_id).first()
        for course in topic.courses:
            topic_obj = {
                'id': course.id,
                'topicTitle': course.title,
                'topicNum': course.topic_num
            }
            topics.append(topic_obj)
    else:
        semester = Semester.query.filter_by(id=sem_id).first()
        prof_course_sem = semester.prof_course_sem
        for listing in prof_course_sem:
            course = listing.prof_course.course
            prof = listing.prof_course.prof
            if(course.id not in topic_ids and course.topic_id == topic_id):        
                topic_ids.append(course.id)
                topic_obj = {
                    'id': course.id,
                    'topicTitle': course.title,
                    'topicNum': course.topic_num
                }
                topics.append(topic_obj)
            if(prof.id not in prof_ids):
                prof_ids.append(prof.id)
                prof_obj = {
                    'id': prof.id,
                    'firstName': prof.first_name,
                    'lastName': prof.last_name
                }
                profs.append(prof_obj)

    result = jsonify({"topics": topics, "profs": profs})
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


@app.route('/api/get_profs', methods=['POST'])
def get_profs():
    """
    Gets list of all profs filtered by course and semester

    Args:
        semesterId (int): semeseter id
        courseId (int): course id
        all (boolean): if true return all profs, if false return filtered list

    Returns:
        result (list): list of profs
        results[i] = {
            'id' (int): prof id,
            'firstName' (string): prof first name,
            'lastName' (string): prof last name,
        }
    """
    sem_id = request.get_json()['semesterId']
    course_id = request.get_json()['courseId']
    get_all = request.get_json()['all']
    prof_ids = []
    profs = []
    if(get_all):
        prof_list = Prof.query.all()
        for prof in prof_list:
            prof_obj = {
                'id': prof.id,
                'firstName': prof.first_name,
                'lastName': prof.last_name,
            }
            profs.append(prof_obj)
    else:
        semester = Semester.query.filter_by(id=sem_id).first()
        
        prof_course_sem = semester.prof_course_sem
        
        for listing in prof_course_sem:
            course = listing.prof_course.course
            if(course_id == course.id):
                prof = listing.prof_course.prof
                if(prof.id in prof_ids):
                    continue
                prof_ids.append(prof.id)
                prof_obj = {
                    'id': prof.id,
                    'firstName': prof.first_name,
                    'lastName': prof.last_name,
                }
                profs.append(prof_obj)
    print(profs)
    result = jsonify({"profs": profs})
    return result

@app.route('/api/get_semesters', methods=['GET'])
def get_semesters():
    """
    Gets list of all semesters

    Returns:
        result (list): list of semesters
        results[i] = {
            'id' (int): prof id,
            'semester' (string): string representation of semester,
            'year' (int): year,
        }
    """
    semesters = Semester.query.all()
    results = dict.fromkeys((range(len(semesters))))
    i = 0
    for sem in semesters:
        sem_string = ""
        if(sem.semester == 6):
            sem_string = "Summer"
        elif(sem.semester == 9):
            sem_string = "Fall"
        elif(sem.semester == 2):
            sem_string = "Spring"

        results[i] = {
            'id': sem.id,
            'semester': sem_string,
            'year': sem.year
        }
        i = i+1

    result = jsonify({"semesters": results})
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
        reviews = User.query.filter_by(email=name).first().reviews_posted
    elif rtype == 'prof':
        reviews = Prof.query.filter_by(first_name=name[0], last_name=name[1]).first().reviews
    elif rtype == 'course':
        dept_id = Dept.query.filter_by(abr=name[0]).first().id
        reviews = Course.query.filter_by(dept_id=dept_id, num=name[1])

    results = [
        {
            'id': result.id,
            'date': timeago.format(result.date_posted, datetime.datetime.utcnow()),
            'grade': result.grade,

            'user': {
                'major': {
                    'abr': result.author.major.abr if result.author.major_id != None else None,
                    'name': result.author.major.name if result.author.major_id != None else result.author.other_major
                }
            },

            'semester': {
                'id': result.semester.id,
                'year': result.semester.year,
                'semester': semester_string(result.semester.semester)
            },

            'prof': {
                'id': result.prof_review[0].prof.id,
                'firstName': result.prof_review[0].prof.first_name,
                'lastName': result.prof_review[0].prof.last_name
            },

            'course': {
                'id': result.course_review[0].course.id,
                'dept': {
                    'abr': result.course_review[0].course.dept.abr,
                    'name': result.course_review[0].course.dept.name
                },
                'num': result.course_review[0].course.num,
                'title': result.course_review[0].course.title,
                'topicNum': result.course_review[0].course.topic_num,
                'topicId': result.course_review[0].course.topic_id,
                'parentId': get_parent_id(result.course_review[0].course.topic_id)
            },

            'courseRating': {
                'approval': result.course_review[0].approval,
                'usefulness': result.course_review[0].usefulness,
                'difficulty': result.course_review[0].difficulty,
                'workload': result.course_review[0].workload,
                'comments': result.course_review[0].comments
            },

            'profRating': {
                'approval': result.prof_review[0].approval,
                'clear': result.prof_review[0].clear,
                'engaging': result.prof_review[0].engaging,
                'grading': result.prof_review[0].grading,
                'comments': result.prof_review[0].comments
            },
        }
        
        for result in reviews
    ]

    result = jsonify({"reviews": results})
    return result

def semester_string(semester_num):
    if(semester_num == 6):
        return "Summer"
    elif(semester_num == 9):
        return "Fall"
    elif(semester_num == 2):
        return "Spring"
    else:
        return ""

def get_parent_id(topic_id):
    if(topic_id == None): 
        return None
    topic = Topic.query.filter_by(id=topic_id).first()
    for course in topic.courses:
        if(course.topic_num == 0):
            return course.id


@app.route('/api/update_personal_info', methods=['POST'])
def update_personal_info():
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    other_major = request.get_json()['other_major']
    dept = Dept.query.filter_by(name=major).first()

    user = User.query.filter_by(email=email).first()
    user.first_name = first_name
    user.last_name = last_name

    major_id = None
    if(major != None and major != ""):
        dept = Dept.query.filter_by(name=major).first()
        major_id = dept.id

    user.other_major = other_major 

    db.session.commit()

    access_token = create_access_token(identity={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'major': user.major.name if user.major_id != None else None,
        'profile_pic': user.pic.file_name,
        'other_major': user.other_major
    })
    result = access_token

    return result

@app.route('/api/update_profile_pic', methods=['POST'])
def update_profile_pic():
    email = request.get_json()['email']
    profile_name = request.get_json()['profile_pic']
    profile_pic = ProfilePic.query.filter_by(file_name=profile_name).first()

    user = User.query.filter_by(email=email).first()
    user.profile_pic_id = profile_pic.id

    db.session.commit()

    access_token = create_access_token(identity={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'major': user.major.name,
        'profile_pic': profile_pic.file_name
    })
    result = access_token

    return result