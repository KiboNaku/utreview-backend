import timeago, datetime
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from .course_info import get_ecis, time_to_string
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time

@app.route('/api/prof_id', methods=['POST'])
def prof_id():
    """
    Takes a prof pathname and parses it to check if it is a valid prof 

    Args:
        profString (string): prof pathname

    Returns:
        result (json): returns the prof id if successful, returns an error if failed
    """
    prof_string = request.get_json()['profString']
    prof_parsed = prof_string.split("_")
    invalid_input = False
    if(len(prof_parsed) == 2):
        first_name = prof_parsed[0]
        last_name = prof_parsed[1]
        topic_num = -1
    else:
        invalid_input = True

    prof_found = False
    prof_id = None
    if(not invalid_input):
        profs = Prof.query.all()
        for prof in profs:
            prof_first = prof.first_name.lower().replace(" ", "")
            prof_last = prof.last_name.lower().replace(" ", "")
            if(first_name == prof_first and last_name == prof_last):
                prof_found = True
                prof_id = prof.id
                result_first = prof.first_name
                result_last = prof.last_name
    if(prof_found):
        result = jsonify({"profId": prof_id, "firstName": result_first, "lastName": result_last})
    else:
        result = jsonify({"error": "No prof was found"})
    return result

@app.route('/api/prof_details', methods=['POST'])
def prof_details():
    """
    Extracts all information needed for a particular prof and sends it to the front end

    Arguments (Sent from the front end): 
        profId (int): id of prof
        loggedIn (boolean): specifies whether the user is logged in
        userEmail (string): email of user, if logged in

    Returns:
        result(json): jsonified representation of prof information
            "prof_info" (object): basic prof info
                prof_info = {
                    "id" (int): prof id,
                    "firstName" (string): prof.first_name,
                    "lastName" (string): prof last name
                }
            "prof_rating" (object): prof average ratings
            "prof_courses" (list): list of courses taught by the prof
            "prof_schedule" (object): prof schedule
            "prof_reviews" (list): list of reviews for the prof
    """
    prof_id = request.get_json()['profId']
    logged_in = request.get_json()['loggedIn']
    user_email = request.get_json()['userEmail']

    if(logged_in):
        curr_user = User.query.filter_by(email=user_email).first()
    else:
        curr_user = None

    prof = Prof.query.filter_by(id=prof_id).first()
    prof_info = {
        "id": prof.id,
        "firstName": prof.first_name,
        "lastName": prof.last_name
    }

    prof_rating, review_list = get_prof_reviews(prof, logged_in, curr_user)
    prof_schedule = get_prof_schedule(prof)
    course_list = get_prof_courses(prof)

    result = jsonify({"prof_info": prof_info,
                      "prof_rating": prof_rating,
                      "prof_courses": course_list,
                      "prof_schedule": prof_schedule,
                      "prof_reviews": review_list,})

    return result

def get_scheduled_prof(scheduled_prof):
    """
    Obtain information for the scheduled prof

    Args:
        scheduled_prof (model instance): scheduled prof

    Returns:
        scheduled_obj (obj): Contains detailed information about the scheduled prof
            scheduled_obj = {
                "id" (int): scheduled id,
                'uniqueNum' (int): scheduled course unique number
                'days' (string): days of the week course is taught
                'timeFrom' (string): starting time
                'timeTo' (string): ending time
                'location' (string): building and room number
                'maxEnrollment' (int): max enrollment
                'seatsTaken' (int): seats taken
                'courseId' (int): course id
                'courseDept' (string): course dept abr
                'courseNum' (string): course num
                'semester' (int): integer representation of semester
                'year' (int): year
                'crossListed' (list): list of cross listed courses
                    x_listed_obj = {
                        'id' (int): course id
                        'dept' (string): course deptartment abbreviation
                        'num' (string): course num
                        'title' (string): course title
                    }
            }
    """
    course = scheduled_prof.course

    x_listed = []
    if(scheduled_prof.cross_listed is not None):
        for x_course in scheduled_prof.cross_listed.courses:
            x_listed_obj = {
                'id': x_course.id,
                'dept': x_course.dept.abr,
                'num': x_course.num,
                'title': x_course.title
            }
            x_listed.append(x_course.dept.abr + " " + x_course.num)

    scheduled_obj = {
        "id": scheduled_prof.id,
        'uniqueNum': scheduled_prof.unique_no,
        'days': scheduled_prof.days,
        'timeFrom': time_to_string(scheduled_prof.time_from),
        'timeTo': time_to_string(scheduled_prof.time_to),
        'location': scheduled_prof.location,
        'maxEnrollment': scheduled_prof.max_enrollement,
        'seatsTaken': scheduled_prof.seats_taken,
        'courseId': course.id,
        'courseDept': course.dept.abr,
        'courseNum': course.num,
        'topicNum': course.topic_num,
        'crossListed': x_listed
    }
    return scheduled_obj

def get_prof_schedule(prof):
    """
    Get prof schedule information for the current and next semesters

    Args:
        prof (model instance): prof

    Returns:
        prof (obj): prof schedule information for most recent two semesters
        prof_schedule = {
            "currentSem" (list): list of scheduled prof for the current semester
            "futureSem" (list): list of scheduled prof for the future semester
        }
    """
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
        scheduled_obj = get_scheduled_prof(scheduled_prof)
        if(scheduled_prof.semester.year == current_sem['year'] and
        scheduled_prof.semester.semester == current_sem['sem']):
            current_list.append(scheduled_obj)
        elif(scheduled_prof.semester.year == future_sem['year']  and
        scheduled_prof.semester.semester == future_sem['sem'] ):
            future_list.append(scheduled_obj)
    prof_schedule = {
        "currentSem": current_list,
        "futureSem": future_list
    }

    return prof_schedule

def get_review_info(review, logged_in, curr_user):
    """
    Get review information for a particular review instance

    Args:
        review (model instance): review
        percentLiked (int): percent liked over all reviews
        clear (int): average clear over all reviews
        engaging (int): average engaging over all reviews
        grading (int): average grading over all reviews
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user

    Returns:
        review_object (object): Object containing detailed information about the review
            review_object = {
            'id' (int): review id
            'comments (string)': comments on the prof
            'approval' (boolean): whether the user liked or disliked the prof
            'clear' (int): clear rating
            'engaging' (int): engaging rating
            'grading' (int): grading rating
            'userMajor' (string): author's major
            'profilePic' (string): author's profile picture
            'courseId' (int): course id
            'courseDept' (string): course dept abr
            'courseNum' (string): course num
            'courseTopic' (int): course topic num
            'grade' (string): grade the user got in the course
            'numLiked' (int): number of likes the review has
            'numDisliked' (int): number of dislikes the review has
            'likePressed' (boolean): whether the current user liked the review
            'dislikePressed' (boolean): whether the current user disliked the review
            'date' (string): date the review was posted converted to string format: ("%Y-%m-%d"),
            'year' (int): year user took the course
            'semester' (string): string representation of semester
        }
    """
    semester = review.semester.semester
    if(semester == 6):
        semester = "Summer"
    elif(semester == 9):
        semester = "Fall"
    elif(semester == 2):
        semester = "Spring"
    else:
        semester = "N/A"
    
    prof_review = review.prof_review[0]

    user = review.author
    course = review.course_review[0].course
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
        'id': prof_review.id,
        'comments': prof_review.comments,
        'approval': prof_review.approval,
        'clear': prof_review.clear,
        'engaging': prof_review.engaging,
        'grading': prof_review.grading,
        'userMajor': user_major.name,
        'profilePic': profile_pic.file_name,
        'courseId': course.id,
        'courseDept': course.dept.abr,
        'courseNum': course.num,
        'courseTopic': course.topic_num,
        'grade': review.grade,
        'numLiked': num_liked,
        'numDisliked': num_disliked,
        'likePressed': like_pressed,
        'dislikePressed': dislike_pressed,
        'date': review.date_posted.strftime("%Y-%m-%d"),
        'dateString': timeago.format(review.date_posted, datetime.datetime.utcnow()),
        'year': review.semester.year,
        'semester': semester
    }
    return review_object

def get_prof_reviews(prof, logged_in, curr_user):
    """
    Get information for all reviews of the prof

    Args:
        prof (model instance): prof
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user

    Returns:
        prof_rating (object): average rating for the prof in all categories
            prof_rating = {
                'eCIS' (float): average prof ecis score over all semesters
                'percentLiked' (float): percentage that liked the prof
                'clear' (float): average clear
                'engaging' (float): average engaging
                'grading' (float): average grading
                'numRatings' (int): number of ratings
            }
        review_list (list): list of all reviews for the prof
    """
    prof_reviews = prof.reviews
    review_list = []
    for prof_review in prof_reviews:
        review = prof_review.review
        review_object = get_review_info(review, logged_in, curr_user)
        review_list.append(review_object)
    prof_rating = {
        'eCIS': round(prof.ecis_avg, 1) if prof.ecis_avg != None else None,
        'percentLiked': round(prof.approval, 2) * 100 if prof.approval != None else None,
        'clear': round(prof.clear, 1) if prof.clear != None else None,
        'engaging': round(prof.engaging, 1) if prof.engaging != None else None,
        'grading': round(prof.grading, 1) if prof.grading != None else None,
        'numRatings': prof.num_ratings
    }
    return prof_rating, review_list

def get_prof_courses(prof):
    """
    Gets information for all courses that are taught by the prof

    Args:
        prof (model instance): prof

    Returns:
        course_list (list): list of all courses taught by the prof
            course_obj = {
                'id' (int): course id
                'courseDept' (string): course dept abr
                'courseNum' (string): course num
                'topicNum' (int): topic number
                'percentLiked' (int): percentage that liked the course for the prof
                'difficulty' (float): average difficulty rating
                'usefulness' (float): average usefulness rating
                'workload' (float): average workload rating
                'eCIS' (float): ecis prof score
            }
    """
    course_list = []
    course_prof = prof.prof_course
    for prof_course in course_prof:
        course = prof_course.course
        course_ecis, prof_ecis = get_ecis(course, prof)
        prof_reviews = prof.reviews
        course_reviews = course.reviews
        review_ids = [prof_review.review_id for prof_review in prof_reviews]
        reviews = []
        for course_review in course_reviews:
            if(course_review.review_id in review_ids):
                reviews.append(course_review.review)
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
            for review in reviews:
                course_review = review.course_review[0]
                if(course_review.approval):
                    percentLiked += 1
                difficulty += course_review.difficulty
                usefulness += course_review.usefulness
                workload += course_review.workload
            percentLiked = round(percentLiked/len(reviews), 2) * 100
            difficulty = round(difficulty/len(reviews), 1)
            usefulness = round(usefulness/len(reviews), 1)
            workload = round(workload/len(reviews), 1)
        course_obj = {
            'id': course.id,
            'courseDept': course.dept.abr,
            'courseNum': course.num,
            'topicNum': course.topic_num,
            'percentLiked': percentLiked,
            'difficulty': difficulty,
            'usefulness': usefulness,
            'workload': workload,
            'eCIS': course_ecis
        }
        course_list.append(course_obj)
    
    return course_list