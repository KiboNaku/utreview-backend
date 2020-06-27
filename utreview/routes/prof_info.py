from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time

@app.route('/api/prof_details', methods=['POST'])
def prof_details():
    prof_name = request.get_json()['profName']
    logged_in = request.get_json()['loggedIn']
    user_email = request.get_json()['userEmail']

    if(logged_in):
        curr_user = User.query.filter_by(email=user_email).first()

    prof_first, prof_last = get_prof_name(prof_name)
    prof_info = {
        "firstName": prof_first,
        "lastName": prof_last
    }

    prof = Prof.query.filter_by(first_name=prof_first, last_name=prof_last).first()

    prof_rating, review_list = get_prof_reviews(prof, logged_in, curr_user)
    course_schedule = get_prof_schedule(prof)
    course_list = get_prof_courses(prof)

    result = jsonify({"prof_info": prof_info,
                      "prof_rating": prof_rating,
                      "prof_courses": course_list,
                      "prof_schedule": prof_schedule,
                      "prof_reviews": review_list,})

    return result

def get_prof_name(prof_name):
    prof_parsed = prof_name.split()
    prof_first = prof_parsed[0]
    prof_last = ""
    for i in range(1, len(prof_parsed)):
        if(i == len(prof_parsed) - 1):
            prof_last += prof_last + prof_parsed[i]
        prof_last += prof_last + prof_parsed[i] + " "
    
    return prof_first, prof_last

def get_ecis(obj):
    ecis_scores = obj.ecis
    if len(ecis_scores) == 0:
        eCIS = None
    else:
        total_students = 0
        for ecis in ecis_scores:
            eCIS += ecis.avg * ecis.num_students
            total_students += ecis.num_students
        eCIS = round(eCIS / total_students, 1)
    return eCIS

def get_scheduled_course(scheduled_course):
    course = scheduled_course.course
    course_name = course.dept.abr + " " + course.num

    x_listed = []
    for x_course in scheduled_course.cross_listed.courses:
        x_listed.append(x_course.dept.abr + " " + x_course.num)

    scheduled_obj = {
        'uniqueNum': scheduled_course.unique_no,
        'days': scheduled_course.days,
        'timeFrom': scheduled_course.time_from,
        'timeTo': scheduled_course.time_to,
        'location': scheduled_course.location,
        'maxEnrollment': scheduled_course.max_enrollment,
        'seatsTaken': scheduled_course.seats_taken,
        'courseName': course_name,
        'crossListed': x_listed
    }
    return scheduled_obj

def get_prof_schedule(prof):
    current_sem = {
        'year': 2020,
        'sem': 6
    }

    future_sem = {
        'year': 2020,
        'sem': 9
    }
    current_list = []
    future_list = []
    profs_scheduled = prof.scheduled
    for scheduled_prof in profs_scheduled:
        scheduled_obj = get_scheduled_course(scheduled_prof)
        if(scheduled_prof.year == current_sem.year and
        scheduled_prof.semester == current_sem.sem):
            current_list.append(scheduled_obj)
        elif(scheduled_prof.year == future_sem.year and
        scheduled_prof.semester == future_sem.sem):
            future_list.append(scheduled_obj)
    prof_schedule = {
        "currentSem": current_list,
        "futureSem": future_list
    }

    return prof_schedule

def get_review_info(review, percentLiked, usefulness, difficulty, workload, logged_in, curr_user):
    semester = review.semester
    if(semester == 6):
        semester = "Summer"
    elif(semester == 9):
        semester = "Fall"
    elif(semester == 2):
        semester = "Spring"
    else:
        semester = "N/A"
    
    prof_review = review.prof_review[0]
    if(prof_review.approval):
        percentLiked += 1
    difficulty += prof_review.difficulty
    usefulness += prof_review.usefulness
    workload += prof_review.workload

    user = review.author
    course = review.course_review[0].course
    course_name = course.dept.abr + " " + course.num
    user_major = user.major
    profile_pic = user.pic

    num_liked = 0
    num_disliked = 0
    like_pressed = False
    dislike_pressed = False
    for like in prof_review.users_liked:
        num_liked += 1
        if(logged_in):
            if(curr_user.id == like.user_id):
                like_pressed = True

    for dislike in prof_review.users_disliked:
        num_disliked += 1
        if(logged_in):
            if(curr_user.id == dislike.user_id):
                dislike_pressed = True

    review_object = {
        'key': prof_review.id,
        'comments': prof_review.comments,
        'approval': prof_review.approval,
        'usefulness': prof_review.usefulness,
        'difficulty': prof_review.difficulty,
        'workload': prof_review.workload,
        'userMajor': user_major.name,
        'profPic': profile_pic.file_name,
        'profName': prof_name,
        'numLiked': num_liked,
        'numDisliked': num_disliked,
        'likePressed': like_pressed,
        'dislikePressed': dislike_pressed,
        'date': review.date_posted.strftime("%Y-%m-%d"),
        'year': review.year,
        'semester': semester
    }
    return review_object

def get_prof_reviews(prof, logged_in, curr_user):
    ecis_score = get_ecis(prof)
    prof_reviews = prof.reviews
    review_list = []
    if(len(prof_reviews) == 0):
        percentLiked = None
        clear = None
        engaging = None
        workload = None
    else:
        percentLiked = 0
        clear = 0
        engaging = 0
        workload = 0
        for prof_review in prof_reviews:
            review = prof_review.review
            review_object = get_review_info(review, percentLiked, 
                clear, engaging, workload, logged_in, curr_user)
            review_list.append(review_object)
        percentLiked = round(percentLiked/len(prof_reviews), 2) * 100
        clear = round(clear/len(prof_reviews), 1)
        usefulness = round(usefulness/len(prof_reviews), 1)
        workload = round(workload/len(prof_reviews), 1)
    numRatings = len(prof_reviews)
    prof_rating = {
        'eCIS': ecis_score,
        'percentLiked': percentLiked,
        'clear': clear,
        'usefulness': usefulness,
        'workload': workload,
        'numRatings': numRatings
    }
    return prof_rating, review_list

def get_course_profs(course, is_parent):
    prof_list = []
    course_prof = course.prof_course
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for prof_course in topic_course.prof_course:
                course_prof.append(prof_course)
    for prof_course in course_prof:
        prof = prof_course.prof
        prof_name = prof.first_name + " " + prof.last_name
        ecis_score = get_ecis(prof)
        prof_reviews = prof.reviews
        course_reviews = course.reviews
        review_ids = [course_review.review_id for course_review in course_reviews]
        reviews = []
        for prof_review in prof_reviews:
            if(prof_review.review_id in review_ids):
                reviews.append(prof_review.review)
        if(len(reviews) == 0):
            percentLiked = None
            clear = None
            engaging = None
            grading = None
        else:
            percentLiked = 0
            clear = 0
            engaging = 0
            grading = 0
            for review in reviews:
                prof_review = review.prof_review[0]
                if(prof_review.approval):
                    percentLiked += 1
                clear += prof_review.clear
                engaging += prof_review.engaging
                grading += prof_review.grading
            percentLiked = round(percentLiked/len(reviews), 2) * 100
            clear = round(clear/len(reviews), 1)
            engaging = round(engaging/len(reviews), 1)
            grading = round(grading/len(reviews), 1)
        prof_obj = {
            'name': prof_name,
            'percentLiked': percentLiked,
            'clear': clear,
            'engaging': engaging,
            'grading': grading,
            'eCIS': ecis_score
        }
        prof_list.append(prof_obj)
    
    return prof_list