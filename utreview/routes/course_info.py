from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time

@app.route('/api/course_details', methods=['POST'])
def course_details():
    """
    Extracts all information needed for a particular course and sends it to the front end

    Arguments (Sent from the front end): 
        courseId (int): id of course
        loggedIn (boolean): specifies whether the user is logged in
        userEmail (string): email of user, if logged in

    Returns:
        result(json): jsonified representation of course information
            "course_info" (object): basic course info
            "course_rating" (object): course average ratings
            "course_requisites" (object): course requisites,
            "course_profs" (list): list of profs that teach the course
            "course_schedule" (object): course schedule
            "course_reviews" (list): list of reviews for the course
            "is_parent" (boolean): shows whether course is a parent topic
    """

    course_id = request.get_json()['courseId']
    logged_in = request.get_json()['loggedIn']
    user_email = request.get_json()['userEmail']

    if(logged_in):
        curr_user = User.query.filter_by(email=user_email).first()

    course_info, course, is_parent = get_course_info(course_id)
    course_requisites = get_course_requisites(course)
    course_rating, review_list = get_course_reviews(course, logged_in, curr_user, is_parent)
    course_schedule = get_course_schedule(course, is_parent)
    prof_list = get_course_profs(course, is_parent)

    result = jsonify({"course_info": course_info,
                      "course_rating": course_rating,
                      "course_requisites": course_requisites,
                      "course_profs": prof_list,
                      "course_schedule": course_schedule,
                      "course_reviews": review_list,
                      "is_parent": is_parent})

    return result

def get_course_info(course_id):
    """
    Uses course id to extract basic course information from database

    Args:
        course_id (int): course id

    Returns:
        course_info (object): contains basic course information
            course_info = {
                'id' (int): course id
                'courseDep' (string): course dept abbreviation
                'courseNum' (string): course number
                'courseTitle' (string): course title,
                'courseDes'(string): course description,
                'topicTitle' (string): topic title
                'parentTitle' (string): parent topic title,
                'topicsList' (list): list of topics belonging to parent topic
                    topic_obj = {
                        'id' (int): course topic id
                        'title' (string): course topic title
                    }
            }
        course (model instance): course specified by course id
        is_parent (boolean): signifies whether the course is a parent topic
    """
    course = Course.query.filter_by(id=course_id).first()
    course_dept = course.dept
    topic_num = course.topic_num

    is_parent = False
    if(topic_num == -1):
        topic_title = None
        parent_title = None
        topics_list = None
    elif(topic_num == 0):
        is_parent = True
        topic_title = course.title
        parent_title = course.title
        topic = course.topic
        topics_list = []
        for course_topic in topic.courses:
            topic_obj = {
                'id': course_topic.id,
                'title': course_topic.title
            }
            topics_list.append(topic_obj)
    else:
        topic_title = course.title
        topic = course.topic
        parent_title = ""
        for course_topic in topic.courses:
            if course_topic.topic_num == 0:
                parent_title = course_topic.title

    course_info = {
        'id': course.id,
        'courseDep': course_dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseDes': course.description,
        'topicTitle': topic_title,
        'parentTitle': parent_title,
        'topicsList': topics_list
    }

    return course_info, course, is_parent

def get_course_requisites(course):
    """
    Gets course requisite information

    Args:
        course (model instance): course

    Returns:
        course_requisites (object): contains course requisite information
            course_requisites = {
                'preReqs' (string): course prerequisites
                'restrictions' (string): course restrictions
            }
    """
    course_requisites = {
        'preReqs': course.pre_reqs,
        'restrictions': course.restrictions
    }
    return course_requisites

def get_ecis(obj):
    """
    Given a course or prof model instance, obtain the average ecis scores over all semesters

    Args:
        obj (model instance): course or prof instance
        
    Returns:
        course_ecis (float): Average course ecis score
        prof_ecis (float): Average prof ecis score
    """
    ecis_scores = obj.ecis
    if len(ecis_scores) == 0:
        course_ecis = None
        prof_ecis = None
    else:
        total_students = 0
        course_ecis = 0
        prof_ecis = 0
        for ecis in ecis_scores:
            course_ecis += ecis.course_avg * ecis.num_students
            prof_ecis += ecis.prof_avg * ecis.num_students
            total_students += ecis.num_students
        course_ecis = round(course_ecis / total_students, 1)
        prof_ecis = round(prof_ecis / total_students, 1)
    return course_ecis, prof_ecis

def get_scheduled_course(scheduled_course):
    """
    Obtain information for the scheduled course

    Args:
        scheduled_course (model instance): scheduled course

    Returns:
        scheduled_obj (obj): Contains detailed information about the scheduled course
            scheduled_obj = {
                "id" (int): scheduled id,
                'uniqueNum' (int): scheduled course unique number
                'days' (string): days of the week course is taught
                'timeFrom' (string): starting time
                'timeTo' (string): ending time
                'location' (string): building and room number
                'maxEnrollment' (int): max enrollment
                'seatsTaken' (int): seats taken
                'profId' (int): professor id
                'profFirst' (string): professor first name
                'profLast' (string): professor last name
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
    prof = scheduled_course.prof

    x_listed = []
    for x_course in scheduled_course.cross_listed.courses:
        x_listed_obj = {
            'id': x_course.id,
            'dept': x_course.dept.abr,
            'num': x_course.num,
            'title': x_course.title
        }
        x_listed.append(x_listed_obj)

    scheduled_obj = {
        "id": scheduled_course.id,
        'uniqueNum': scheduled_course.unique_no,
        'days': scheduled_course.days,
        'timeFrom': scheduled_course.time_from,
        'timeTo': scheduled_course.time_to,
        'location': scheduled_course.location,
        'maxEnrollment': scheduled_course.max_enrollment,
        'seatsTaken': scheduled_course.seats_taken,
        'profId': prof.id,
        'profFirst': prof.first_name,
        'profLast': prof.last_name,
        'crossListed': x_listed,
        'semester': scheduled_course.semester.semester,
        'year': scheduled_course.semester.year
    }
    return scheduled_obj

def get_course_schedule(course, is_parent):
    """
    Get course schedule information for the current and next semesters

    Args:
        course (model instance): course
        is_parent (boolean): signifies whether the course is a parent topic

    Returns:
        course_schedule (obj): course schedule information for most recent two semesters
        course_schedule = {
            "currentSem" (list): list of scheduled courses for the current semester
            "futureSem" (list): list of scheduled courses for the future semester
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
    courses_scheduled = course.scheduled
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for scheduled in topic_course.scheduled:
                courses_scheduled.append(scheduled)
    for scheduled_course in courses_scheduled:
        scheduled_obj = get_scheduled_course(scheduled_course)
        if(scheduled_course.semester.year == current_sem.year and
        scheduled_course.semester.semester == current_sem.sem):
            current_list.append(scheduled_obj)
        elif(scheduled_course.semester.year == future_sem.year and
        scheduled_course.semester.semester == future_sem.sem):
            future_list.append(scheduled_obj)

    course_schedule = {
        "currentSem": current_list,
        "futureSem": future_list
    }

    return course_schedule

def get_review_info(review, percentLiked, usefulness, difficulty, workload, logged_in, curr_user):
    """
    Get review information for a particular review instance

    Args:
        review (model instance): review
        percentLiked (int): percent liked over all reviews
        usefulness (int): average usefulness over all reviews
        difficulty (int): average difficulty over all reviews
        workload (int): average workload over all reviews
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user

    Returns:
        review_object (object): Object containing detailed information about the review
            review_object = {
            'id' (int): review id
            'comments (string)': comments on the course
            'approval' (boolean): whether the user liked or disliked the course
            'usefulness' (int): usefulness rating
            'difficulty' (int): difficulty rating
            'workload' (int): workload rating
            'userMajor' (string): author's major
            'profilePic' (string): author's profile picture
            'profId' (int): prof id
            'profFirst' (string): prof first name
            'profLast' (string): prof last name
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
    
    course_review = review.course_review[0]
    if(course_review.approval):
        percentLiked += 1
    difficulty += course_review.difficulty
    usefulness += course_review.usefulness
    workload += course_review.workload

    user = review.author
    prof = review.prof_review[0].prof
    user_major = user.major
    profile_pic = user.pic

    num_liked = 0
    num_disliked = 0
    like_pressed = False
    dislike_pressed = False
    for like in course_review.users_liked:
        num_liked += 1
        if(logged_in):
            if(curr_user.id == like.user_id):
                like_pressed = True

    for dislike in course_review.users_disliked:
        num_disliked += 1
        if(logged_in):
            if(curr_user.id == dislike.user_id):
                dislike_pressed = True

    review_object = {
        'id': course_review.id,
        'comments': course_review.comments,
        'approval': course_review.approval,
        'usefulness': course_review.usefulness,
        'difficulty': course_review.difficulty,
        'workload': course_review.workload,
        'userMajor': user_major.name,
        'profilePic': profile_pic.file_name,
        'profId': prof.id,
        'profFirst': prof.first_name,
        'profLast': prof.last_name,
        'numLiked': num_liked,
        'numDisliked': num_disliked,
        'likePressed': like_pressed,
        'dislikePressed': dislike_pressed,
        'date': review.date_posted.strftime("%Y-%m-%d"),
        'year': review.year,
        'semester': semester
    }
    return review_object

def get_course_reviews(course, logged_in, curr_user, is_parent):
    """
    Get information for all reviews of the course

    Args:
        course (model instance): course
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user
        is_parent (boolean): whether course is a parent topic

    Returns:
        course_rating (object): average rating for the course in all categories
            course_rating = {
                'eCIS' (float): average course ecis score over all semesters
                'percentLiked' (float): percentage that liked the course
                'difficulty' (float): average difficulty
                'usefulness' (float): average usefulness
                'workload' (float): average workload
                'numRatings' (int): number of ratings
            }
        review_list (list): list of all reviews for the course
    """
    ecis_course_score, ecis_prof_score = get_ecis(course)
    course_reviews = course.reviews
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for topic_review in topic_course.reviews:
                course_reviews.append(topic_review)
    review_list = []
    if(len(course_reviews) == 0):
        percentLiked = None
        difficulty = None
        usefulness = None
        workload = None
    else:
        percentLiked = 0
        difficulty = 0
        usefulness = 0
        workload = 0
        for course_review in course_reviews:
            review = course_review.review
            review_object = get_review_info(review, percentLiked, 
                difficulty, usefulness, workload, logged_in, curr_user)
            review_list.append(review_object)
        percentLiked = round(percentLiked/len(course_reviews), 2) * 100
        difficulty = round(difficulty/len(course_reviews), 1)
        usefulness = round(usefulness/len(course_reviews), 1)
        workload = round(workload/len(course_reviews), 1)
    numRatings = len(course_reviews)
    course_rating = {
        'eCIS': ecis_course_score,
        'percentLiked': percentLiked,
        'difficulty': difficulty,
        'usefulness': usefulness,
        'workload': workload,
        'numRatings': numRatings
    }
    return course_rating, review_list

def get_course_profs(course, is_parent):
    """
    Gets information for all profs that teach the course

    Args:
        course (model instance): course
        is_parent (boolean): whether course is a parent topic

    Returns:
        prof_list (list): list of all professors that teach the course
            prof_obj = {
                'id' (int): prof id
                'firstName' (string): prof first name
                'lastName' (string): prof last name,
                'percentLiked' (int): percentage that liked the prof for the course
                'clear' (float): average clear rating
                'engaging' (float): average engaging rating
                'grading' (float): average grading rating
                'eCIS' (float): ecis prof score
            }
    """
    prof_list = []
    course_prof = course.prof_course
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for prof_course in topic_course.prof_course:
                course_prof.append(prof_course)
    for prof_course in course_prof:
        prof = prof_course.prof
        ecis_course_score, ecis_prof_score = get_ecis(prof)
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
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'percentLiked': percentLiked,
            'clear': clear,
            'engaging': engaging,
            'grading': grading,
            'eCIS': ecis_prof_score
        }
        prof_list.append(prof_obj)
    
    return prof_list

