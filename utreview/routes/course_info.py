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

@app.route('/api/course_id', methods=['POST'])
def course_id():
    """
    Takes a course pathname and parses it to check if it is a valid course 

    Args:
        courseString (string): course pathname

    Returns:
        result (json): returns the course id if successful, returns an error if failed
    """
    course_string = request.get_json()['courseString']
    course_parsed = course_string.split("_")
    invalid_input = False
    if(len(course_parsed) == 2):
        course_dept = course_parsed[0]
        course_num = course_parsed[1]
        topic_num = -1
    elif(len(course_parsed) == 3):
        course_dept = course_parsed[0]
        course_num = course_parsed[1]
        if(not course_parsed[2].isnumeric()):
            invalid_input = True
        else:
            topic_num = int(course_parsed[2])
    else:
        invalid_input = True

    course_found = False
    course_id = None
    parent_id = None
    if(not invalid_input):
        courses = Course.query.filter_by(num=course_num.upper(), topic_num=topic_num)
        for course in courses:
            dept = course.dept
            if(dept.abr.lower().replace(" ", "") == course_dept):
                course_found = True
                course_id = course.id
                result_dept = course.dept.abr
                result_num = course.num
                if(topic_num >= 0):
                    topic_id = course.topic_id
                    for topic in course.topic.courses:
                        if(topic.topic_num == 0):
                            parent_id = topic.id
                else:
                    topic_id = -1

    if(course_found):
        result = jsonify({"courseId": course_id, "courseDept": result_dept, "courseNum": result_num, "topicId": topic_id, "parentId": parent_id})
    else:
        result = jsonify({"error": "No course was found"})
    return result

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
    else:
        curr_user = None

    print("get course info")
    course_info, course, is_parent = get_course_info(course_id)
    print("get course requisites")
    course_requisites = get_course_requisites(course)
    print("get course reviews")
    course_rating, review_list = get_course_reviews(course, logged_in, curr_user, is_parent)
    print("get course schedule")
    course_schedule = get_course_schedule(course, is_parent)
    print("get course profs")
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
                'courseDept' (string): course dept abbreviation
                'courseNum' (string): course number
                'courseTitle' (string): course title,
                'courseDes'(string): course description,
                'topicNum' (int): topic number (if applicable)
                'parentTitle' (string): parent topic title,
                'topicsList' (list): list of topics belonging to parent topic
                    topic_obj = {
                        'id' (int): course topic id
                        'topicNum' (int): topic number
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
    parent_id = None
    if(topic_num == -1):
        parent_title = None
        topics_list = None
    elif(topic_num == 0):
        is_parent = True
        parent_id = course.id
        parent_title = course.title
        topic = course.topic
        topics_list = []
        for course_topic in topic.courses:
            if (course_topic.topic_num == 0):
                continue
            topic_obj = {
                'id': course_topic.id,
                'topicNum': course_topic.topic_num,
                'title': course_topic.title
            }
            topics_list.append(topic_obj)
        if(len(topics_list) == 0):
            is_parent = False
    else:
        topic = course.topic
        parent_title = ""
        topics_list = None

        for course_topic in topic.courses:
            print(course_topic)
            if course_topic.topic_num == 0:
                parent_title = course_topic.title
                parent_id = course_topic.id

    course_info = {
        'id': course.id,
        'courseDept': course_dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseDes': course.description,
        'topicId': course.topic_id,
        'topicNum': topic_num,
        'parentId': parent_id,
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
        'preReqs': course.pre_req,
        'restrictions': course.restrictions
    }
    return course_requisites

def get_ecis(course, prof):
    """
    Given a course and prof model instance, obtain the average ecis scores over all semesters

    Args:
        course (model instance): course instance,
        prof (model instance): prof instance
        
    Returns:
        course_ecis (float): Average course ecis score
        prof_ecis (float): Average prof ecis score
    """
    ecis_scores = EcisScore.query.all()
    scores = []
    for ecis_score in ecis_scores:
        if(ecis_score.course_id == course.id and ecis_score.prof_id == prof.id):
            scores.append(ecis_score)
    if len(scores) == 0:
        course_ecis = None
        prof_ecis = None
    else:
        total_students = 0
        course_ecis = 0
        prof_ecis = 0
        for ecis in scores:
            course_ecis += ecis.course_avg * ecis.num_students
            prof_ecis += ecis.prof_avg * ecis.num_students
            total_students += ecis.num_students
        course_ecis = round(course_ecis / total_students, 1)
        prof_ecis = round(prof_ecis / total_students, 1)
    return course_ecis, prof_ecis

def time_to_string(time_to_string):
    if(time_to_string == None):
        return None
    time_string = ""
    time_num = int(time_to_string)
    
    if(time_num < 1200 and time_num >= 100):
        if(len(time_to_string) == 3):
            time_string = time_to_string[0:1] + ":" + time_to_string[1:3]
        else:
            time_string = time_to_string[0:2] + ":" + time_to_string[2:4]
        time_string += " AM"
    elif(time_num <= 0 and time_num < 100):
        time_string = "12" + ":" + time_to_string[1:3] + " AM"
    elif(time_num <= 1200 and time_num < 1300):
        time_string = "12" + ":" + time_to_string[2:4] + " PM"
    else:
        time_num = time_num - 1200
        time_to_string = str(time_num) 
        if(len(time_to_string) == 3):
            time_string = time_to_string[0:1] + ":" + time_to_string[1:3]
        else:
            time_string = time_to_string[0:2] + ":" + time_to_string[2:4]   
        time_string += " PM"
    return time_string

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
                        'topicNum' (int): topic number
                    }
            }
    """
    prof = scheduled_course.prof
    semester_name = ""
    if(scheduled_course.semester.semester == 2):
        semester_name = "Spring"
    elif(scheduled_course.semester.semester == 6):
        semester_name = "Summer"
    elif(scheduled_course.semester.semester == 9):
        semester_name = "Fall"

    x_listed = []
    if(scheduled_course.cross_listed is not None):
        for x_course in scheduled_course.cross_listed.courses:
            x_listed_obj = {
                'id': x_course.id,
                'dept': x_course.dept.abr,
                'num': x_course.num,
                'title': x_course.title,
                'topicNum': x_course.topic_num
            }
            x_listed.append(x_listed_obj)

    scheduled_obj = {
        "id": scheduled_course.id,
        'uniqueNum': scheduled_course.unique_no,
        'days': scheduled_course.days,
        'timeFrom': time_to_string(scheduled_course.time_from),
        'timeTo': time_to_string(scheduled_course.time_to),
        'location': scheduled_course.location,
        'maxEnrollment': scheduled_course.max_enrollement,
        'seatsTaken': scheduled_course.seats_taken,
        'profId': prof.id,
        'profFirst': prof.first_name,
        'profLast': prof.last_name,
        'crossListed': x_listed,
        'semester': semester_name,
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
    courses_scheduled_ids = []
    courses_scheduled = course.scheduled
    for i in range(len(course.scheduled)):
        courses_scheduled_ids.append(course.scheduled[i].id)
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for i in range(len(topic_course.scheduled)):
                if(topic_course.scheduled[i].id in courses_scheduled_ids):
                    continue
                courses_scheduled_ids.append(topic_course.scheduled[i].id)
                courses_scheduled.append(topic_course.scheduled[i])
    for scheduled_course in courses_scheduled:
        scheduled_obj = get_scheduled_course(scheduled_course)
        if(scheduled_course.semester.year == current_sem['year'] and
        scheduled_course.semester.semester == current_sem['sem']):
            current_list.append(scheduled_obj)
        elif(scheduled_course.semester.year == future_sem['year'] and
        scheduled_course.semester.semester == future_sem['sem']):
            future_list.append(scheduled_obj)

    course_schedule = {
        "currentSem": current_list,
        "futureSem": future_list
    }

    return course_schedule

def get_review_info(review, logged_in, curr_user):
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
    
    course_review = review.course_review[0]

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
        'grade': review.grade,
        'numDisliked': num_disliked,
        'likePressed': like_pressed,
        'dislikePressed': dislike_pressed,
        'dateString': timeago.format(review.date_posted, datetime.datetime.utcnow()),
        'date': review.date_posted.strftime("%Y-%m-%d"),
        'year': review.semester.year,
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

    course_reviews_ids = []
    course_reviews = course.reviews
    for i in range(len(course.reviews)):
        course_reviews_ids.append(course.reviews[i].id)
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for i in range(len(topic_course.reviews)):
                if(topic_course.reviews[i].id in course_reviews_ids):
                    continue
                course_reviews_ids.append(topic_course.reviews[i].id)
                course_reviews.append(topic_course.reviews[i])

    review_list = []
    for course_review in course_reviews:
        review = course_review.review
        review_object = get_review_info(review, logged_in, curr_user)
        review_list.append(review_object)
    course_rating = {
        'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
        'percentLiked': round(course.approval, 2) * 100 if course.approval != None else None,
        'difficulty': round(course.difficulty, 1) if course.difficulty != None else None,
        'usefulness': round(course.usefulness, 1) if course.usefulness != None else None,
        'workload': round(course.workload, 1) if course.workload != None else None,
        'numRatings': course.num_ratings
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
    course_prof_ids = []
    for i in range(len(course.prof_course)):
        course_prof_ids.append(course.prof_course[i].id)
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for i in range(len(topic_course.prof_course)):
                if(topic_course.prof_course[i].id in course_prof_ids):
                    continue
                course_prof_ids.append(topic_course.prof_course[i].id)
                course_prof.append(topic_course.prof_course[i])
    for prof_course in course_prof:
        prof = prof_course.prof
        course_ecis, prof_ecis = get_ecis(course, prof)
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
            'eCIS': prof_ecis
        }
        prof_list.append(prof_obj)
    
    return prof_list

