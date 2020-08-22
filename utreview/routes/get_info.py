"""
This file contains get request routes to fetch various lists from the database
    get_course_num,
    get_major,
    get_semester,
    get_courses,
    get_topics,
    get_semester,
    get_profs

"""

import timeago
import datetime
import json
from flask import request, jsonify
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db
from whoosh.fields import *


@app.route('/api/get_courses', methods=['POST'])
def get_courses():
    """
    Gets list of all courses, filtered by a prof

    Args:
        profId (int): prof id,

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
    # get arg from front end
    prof_id = request.get_json()['profId']

    # find prof and get list of courses taught by the prof
    prof = Prof.query.filter_by(id=prof_id).first()
    prof_course = prof.prof_course

    # iterate through courses and add to list if not a child topic course
    courses = []
    course_ids = []
    for listing in prof_course:

        # if the course is a child topic, add the parent topic to the list
        course = listing.course
        if(course.topic_num > 0):
            topic_courses = course.topic.courses
            for topic_course in topic_courses:
                if(topic_course.topic_num == 0):
                    course = topic_course

        # skip if the course is already in the list
        if(course.id in course_ids):
            continue
        course_ids.append(course.id)

        # create course object and append to list if not already in list
        dept = course.dept
        course_obj = {
            'id': course.id,
            'dept': dept.abr,
            'num': course.num,
            'title': course.title,
            'topicId': course.topic_id,
            'topicNum': course.topic_num
        }
        courses.append(course_obj)

    result = jsonify({"courses": courses})

    return result


@app.route('/api/get_topics', methods=['POST'])
def get_topics():
    """
    Gets list of all topics, filtered by a topic id and prof id

    Args:
        topicId (int): topic id,
        profId (int): prof id

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
    # get args from front end
    topic_id = request.get_json()['topicId']
    prof_id = request.get_json()['profId']

    # find prof and get list of courses taught by the prof
    prof = Prof.query.filter_by(id=prof_id).first()
    prof_course = prof.prof_course

    # iterate through all courses and add to list if the topic ids match
    topics = []
    for listing in prof_course:

        # skip if topic id doesn't match
        course = listing.course
        if(course.topic_id != topic_id):
            continue

        # create topic object and append to list
        topic_obj = {
            'id': course.id,
            'topicTitle': course.title,
            'topicNum': course.topic_num
        }
        topics.append(topic_obj)

    result = jsonify({"topics": topics})

    return result


@app.route('/api/get_major', methods=['GET'])
def get_major():
    """
    Gathers list of all majors/departments and returns it to the front end

    Returns:
        results (list): list of all majors/departments
        results[i] = {
            'id' (int): major id,
            'abr' (string): major abr,
            'name' (string): major name
        }
    """

    majors = Dept.query.all()
    majors = sorted(majors, key=lambda major: major.name)
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


@app.route('/api/get_semester', methods=['GET'])
def get_semester():
    """
    Fetch current, next, and future semester values

    Returns:
        semesters (dict): Returns a mapping from current, next, and future to the corresponding semester
    """
    with open('input_data/semester.txt') as f:
        semesters = json.load(f)
        for key, value in semesters.items():
            if key == "current" or key == "future":
                if value is not None:
                    year = value[0:-1]
                    if value[-1] == '2':
                        semesters[key] = f'Spring {year}'
                    elif value[-1] == '6':
                        semesters[key] = f'Summer {year}'
                    elif value[-1] == '9':
                        semesters[key] = f'Fall {year}'
                else:
                    semesters[key] = None
            elif key == "next":
                if semesters["current"] is None:
                    semesters[key] = None
                else:
                    current_sem = semesters["current"].split()

                    future_sem_year = ""
                    future_sem_sem = ""
                    if(current_sem[0] == "Fall"):
                        future_sem_year = str(int(current_sem[1]) + 1)
                        future_sem_sem = "Spring"
                    elif(current_sem['sem'] == "Spring"):
                        future_sem_year = current_sem[1]
                        future_sem_sem = "Summer"
                    elif(current_sem['sem'] == "Summer"):
                        future_sem_year = current_sem[1]
                        future_sem_sem = "Fall"
                    
                    semesters[key] = future_sem_sem + " " + future_sem_year

        return semesters

    return None


@app.route('/api/get_profs', methods=['POST'])
def get_profs():
    """
    Gets list of all profs filtered by course

    Args:
        courseId (int): course id

    Returns:
        result (list): list of profs
        results[i] = {
            'id' (int): prof id,
            'firstName' (string): prof first name,
            'lastName' (string): prof last name,
        }
    """
    # get arg from front end
    course_id = request.get_json()['courseId']

    # find course and get list of profs that teach the course
    course = Course.query.filter_by(id=course_id).first()
    prof_course = course.prof_course

    # iterate through all profs and add to list
    profs = []
    for listing in prof_course:
        prof = listing.prof
        prof_obj = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
        }
        profs.append(prof_obj)

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

    # iterate through semester list and append each semester to list
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
