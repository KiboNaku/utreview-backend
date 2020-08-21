"""
This file contains routes to fetch and update various information from the profile page
    update_personal_info,
    update_profile_pic,
    review_list,
    get_profile_pic,
    has_password
"""

import timeago, datetime
import json
from flask import request, jsonify
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db
from whoosh.fields import *

@app.route('/api/update_personal_info', methods=['POST'])
def update_personal_info():
    """
    Update user's personal info, using information sent from edit profile
    Args:
        first_name (string): user first name
        last_name (string): user last name
        email (string): user email
        major (string): user major (from default list)
        other_major (string): user other major

    Returns:
        result (access token): contains securely stored information about the user 
        that can be accessed in the front end
            'first_name' (string): user first name
            'last_name' (string): user last name
            'email' (string): user utexas email
            'major' (string): user's major
            'profile_pic' (string): file name of profile pic
            'other_major' (string): user other major
    """
    # get args from front end
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    major = request.get_json()['major']
    other_major = request.get_json()['other_major']

    # obtain basic user information
    dept = Dept.query.filter_by(name=major).first()
    user = User.query.filter_by(email=email).first()
    user.first_name = first_name
    user.last_name = last_name

    # determine user major
    major_id = None
    if(major != None and major != ""):
        dept = Dept.query.filter_by(name=major).first()
        major_id = dept.id

    user.major_id = major_id
    user.other_major = other_major 

    db.session.commit()

    # create access token and return it
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
    """
    Update a user's profile pic
    Args:
        email (string): user email
        profile_pic (string): profile pic file name

    Returns:
        result (access token): contains securely stored information about the user 
        that can be accessed in the front end
            'first_name' (string): user first name
            'last_name' (string): user last name
            'email' (string): user utexas email
            'major' (string): user's major
            'profile_pic' (string): file name of profile pic
            'other_major' (string): user other major
    """

    # get args from the front end
    email = request.get_json()['email']
    profile_name = request.get_json()['profile_pic']

    # update user profile pic
    profile_pic = ProfilePic.query.filter_by(file_name=profile_name).first()
    user = User.query.filter_by(email=email).first()
    user.profile_pic_id = profile_pic.id

    db.session.commit()

    # create access token and return it
    access_token = create_access_token(identity={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'major': user.major.name,
        'profile_pic': profile_pic.file_name
    })
    result = access_token

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
            'timeAgo': timeago.format(result.date_posted, datetime.datetime.utcnow()),
            'date': str(result.date_posted),
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
                'semester': semester_string(result.semester.semester),
                'num': result.semester.year * 10 + result.semester.semester
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

@app.route('/api/has_password', methods=['POST'])
def has_password():
    """
    Given a user email, check if a password exists for the user

    Args (from front end):
        email (string): user utexas email

    Returns:
        hasPassword (boolean): true if user has a password, false if user doesn't
    """
    # get args from front end and obtain user
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()

    # check if password exists
    if(user.password_hash):
        result = jsonify({"hasPassword": True})
    else:
        result = jsonify({"hasPassword": False})
    
    return result