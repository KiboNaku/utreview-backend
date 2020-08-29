"""
This file contains routes to fetch information needed on the  page:
    utplus_course,
    utplus_prof

"""

import timeago, datetime
import json
import operator
from flask import request, jsonify
from utreview.models import *
from utreview import app
from .catalyst import course_median_grade, prof_median_grade
from .profile_info import get_parent_id 

@app.route('/api/utplus_prof', methods=['POST'])
def utplus_prof():
    """
    Extracts all information needed for a prof on UT Plus extension

    Arguments (Sent from the front end): 
        firstName (string): prof first name
        lastName (string): prof last name

    Returns:
        result(json): jsonified representation of prof information
            "prof_info" (object): basic prof info
            "prof_ratings" (object): prof average ratings
            "top_review" (object): top prof review
    """
    # get args from the front end
    first_name = request.get_json()['firstName']
    last_name = request.get_json()['lastName']

    # get prof details information
    prof_info, prof = get_prof_info(first_name, last_name)
    prof_ratings = get_prof_ratings(prof) if prof != None else None
    top_review = get_prof_top_review(prof) if prof != None else None

    # return object storing all prof details information
    result = jsonify({"prof_info": prof_info,
                      "prof_ratings": prof_ratings,
                      "top_review": top_review
                      })

    return result

@app.route('/api/utplus_course', methods=['POST'])
def utplus_course():
    """
    Extracts all information needed for a course on UT Plus extension,
    Returns None if the course isn't found

    Arguments (Sent from the front end): 
        courseDept (string): course dept abbreviation
        courseNum (string): course num

    Returns:
        result(json): jsonified representation of course information
            "course_info" (object): basic course info
            "course_ratings" (object): course average ratings
            "top_review" (object): top course review
    """
    # get args from the front end
    course_dept = request.get_json()['courseDept']
    course_num = request.get_json()['courseNum']

    # get course details information
    course_info, course = get_course_info(course_dept, course_num)
    course_ratings = get_course_ratings(course) if course != None else None
    top_review = get_course_top_review(course) if course != None else None

    # return object storing all course details information
    result = jsonify({"course_info": course_info,
                      "course_ratings": course_ratings,
                      "top_review": top_review
                      })

    return result

def get_prof_info(first_name, last_name):
    """
    Uses first name / last name to extract basic prof information from database

    Args:
        first_name (string): prof first name
        last_name (string): prof last name

    Returns:
        prof_info (object): contains basic prof information
            prof_info = {
                'id' (int): prof id
                'firstName' (string): prof first name
                'lastName' (string): prof last name,
                'medianGrade' (string): prof median grade,
                'profLink' (string): link to prof page on ut review
            }
        prof (model instance): prof specified by prof id
    """

    first_name = first_name.lower().replace(" ", "")
    last_name = last_name.lower().replace(" ", "")

    # find prof in database
    result_prof = None
    profs = Prof.query.all()
    for prof in profs:
        prof_first = prof.first_name.lower().replace(" ", "")
        prof_last = prof.last_name.lower().replace(" ", "")

        # prof is found if first and last names match
        if(first_name == prof_first and last_name == prof_last):
            result_prof = prof
            break
    
    if(result_prof == None):
        return None, None

    # find median grade for the prof
    median_grade = prof_median_grade(result_prof.first_name, result_prof.last_name)

    # get link to prof page on UT Review
    prof_link = get_prof_link(result_prof.first_name, result_prof.last_name)

    # return all prof info information
    prof_info = {
        'id': result_prof.id,
        'firstName': result_prof.first_name,
        'lastName': result_prof.last_name,
        'medianGrade': median_grade,
        'profLink': prof_link
    }

    return prof_info, result_prof

def get_course_info(course_dept, course_num):
    """
    Uses course dept / course num to extract basic course information from database

    Args:
        course_dept (string): course dept abbreviation
        course_num (string): course num

    Returns:
        course_info (object): contains basic course information
            course_info = {
                'id' (int): course id
                'courseDept' (string): course dept abbreviation
                'courseNum' (string): course number
                'courseTitle' (string): course title,
                'courseDes'(string): course description,
            }
        course (model instance): course specified by course id
    """
    # find course in database
    dept = Dept.query.filter_by(abr=course_dept).first()
    course = Course.query.filter_by(dept_id=dept.id, num=course_num).first()

    if(course == None):
        return None, None

    if(course.topic_num != -1):
        parent_id = get_parent_id(course.topic_id)
        course = Course.query.filter_by(id=parent_id).first()

    course_dept = course.dept
    topic_num = course.topic_num
    
    # find median grade for the course
    median_grade = course_median_grade(course_dept.abr, course.num, topic_num, course.title)

    # get link to course page on UT Review
    course_link = get_course_link(course_dept.abr, course.num, topic_num)

    # return all course info information
    course_info = {
        'id': course.id,
        'courseDept': course_dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseDes': course.description,
        'medianGrade': median_grade,
        'courseLink': course_link
    }

    return course_info, course

def get_prof_link(first_name, last_name):
    """
    Given some prof information, return the link to the prof page on UT Review

    Args:
        first_name (string): prof first name
        last_name (string): prof last name
    
    Returns:
        prof_link (string): link to the prof page on UT Review
    """
    prof_link = "https://www.utexasreview.com/prof-results/"
    prof_path = first_name.replace(" ", "").lower() + "_" + last_name.replace(" ", "").lower()
    prof_link += prof_path

    return prof_link

def get_course_link(course_dept, course_num, topic_num):
    """
    Given some course information, return the link to the course page on UT Review

    Args:
        course_dept (string): course dept abbreviation
        course_num (string): course num
        topic_num (int): course topic num
    
    Returns:
        course_link (string): link to the course page on UT Review
    """
    course_link = "https://www.utexasreview.com/course-results/"
    course_path = course_dept.replace(" ", "").lower() + "_" + course_num.replace(" ", "").lower()
    course_link += course_path
    if(topic_num != -1):
        course_link += "_" + str(topic_num)

    return course_link

def get_prof_ratings(prof):
    """
    Get all ratings information for a prof

    Args:
        prof (model instance): prof

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
    """
    # return prof rating information
    prof_rating = {
        'eCIS': round(prof.ecis_avg, 1) if prof.ecis_avg != None else None,
        'percentLiked': round(prof.approval, 2) * 100 if prof.approval != None else None,
        'clear': round(prof.clear, 1) if prof.clear != None else None,
        'engaging': round(prof.engaging, 1) if prof.engaging != None else None,
        'grading': round(prof.grading, 1) if prof.grading != None else None,
        'numRatings': prof.num_ratings
    }

    return prof_rating

def get_course_ratings(course):
    """
    Get all ratings information for a course

    Args:
        course (model instance): course

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
    """
    # return course rating information
    course_rating = {
        'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
        'percentLiked': round(course.approval, 2) * 100 if course.approval != None else None,
        'difficulty': round(course.difficulty, 1) if course.difficulty != None else None,
        'usefulness': round(course.usefulness, 1) if course.usefulness != None else None,
        'workload': round(course.workload, 1) if course.workload != None else None,
        'numRatings': course.num_ratings
    }

    return course_rating

def get_prof_review_info(review):
    """
    Get review information for a particular review instance

    Args:
        review (model instance): review

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
            'courseDept' (string): course dept
            'courseNum' (string): course num
            'grade' (string): grade the user got in the prof
            'numLiked' (int): number of likes the review has
            'numDisliked' (int): number of dislikes the review has
            'date' (string): date the review was posted converted to string format: ("%Y-%m-%d"),
            'year' (int): year user took the course
            'semester' (string): string representation of semester
        }
    """
    
    # convert semester to string representation
    semester = review.semester.semester
    if(semester == 6):
        semester = "Summer"
    elif(semester == 9):
        semester = "Fall"
    elif(semester == 2):
        semester = "Spring"
    else:
        semester = "N/A"
    
    # get prof review instance
    prof_review = review.prof_review[0]

    # get user and prof information
    user = review.author
    course = review.course_review[0].course
    user_major = user.major
    profile_pic = user.pic

    num_liked = 0
    num_disliked = 0

    # calculate number of likes and determine if current user liked the review
    for like in prof_review.users_liked:
        num_liked += 1

    # calulcate number of dislikes and determine if current user disliked the review
    for dislike in prof_review.users_disliked:
        num_disliked += 1
    
    # if the review comment is empty, return None
    if(prof_review.comments == ""):
        return None

    # return detailed review information
    review_object = {
        'id': prof_review.id,
        'comments': prof_review.comments,
        'approval': prof_review.approval,
        'clear': prof_review.clear,
        'engaging': prof_review.engaging,
        'grading': prof_review.grading,
        'user': {
            'major': user_major.name if user_major != None else user.other_major,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'email': user.email
        },
        'course': {
            'id': course.id,
            'courseDept': course.dept.abr,
            'courseNum': course.num,
        },
        'numLiked': num_liked,
        'numDisliked': num_disliked,
        'grade': review.grade,
        'dateString': timeago.format(review.date_posted, datetime.datetime.utcnow()),
        'date': str(review.date_posted),
        'year': review.semester.year,
        'semester': semester
    }

    return review_object

def get_course_review_info(review):
    """
    Get review information for a particular review instance

    Args:
        review (model instance): review

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
            'date' (string): date the review was posted converted to string format: ("%Y-%m-%d"),
            'year' (int): year user took the course
            'semester' (string): string representation of semester
        }
    """
    
    # convert semester to string representation
    semester = review.semester.semester
    if(semester == 6):
        semester = "Summer"
    elif(semester == 9):
        semester = "Fall"
    elif(semester == 2):
        semester = "Spring"
    else:
        semester = "N/A"
    
    # get course review instance
    course_review = review.course_review[0]

    # get user and prof information
    user = review.author
    prof = review.prof_review[0].prof
    user_major = user.major
    profile_pic = user.pic

    num_liked = 0
    num_disliked = 0

    # calculate number of likes and determine if current user liked the review
    for like in course_review.users_liked:
        num_liked += 1

    # calulcate number of dislikes and determine if current user disliked the review
    for dislike in course_review.users_disliked:
        num_disliked += 1
    
    # if the review comment is empty, return None
    if(course_review.comments == ""):
        return None

    # return detailed review information
    review_object = {
        'id': course_review.id,
        'comments': course_review.comments,
        'approval': course_review.approval,
        'usefulness': course_review.usefulness,
        'difficulty': course_review.difficulty,
        'workload': course_review.workload,
        'user': {
            'major': user_major.name if user_major != None else user.other_major,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'email': user.email
        },
        'prof': {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
        },
        'numLiked': num_liked,
        'numDisliked': num_disliked,
        'grade': review.grade,
        'dateString': timeago.format(review.date_posted, datetime.datetime.utcnow()),
        'date': str(review.date_posted),
        'year': review.semester.year,
        'semester': semester
    }

    return review_object

def get_prof_top_review(prof):
    """
    Get the top-rated review for the specified prof

    Args:
        prof (model instance): prof

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
    # obtain list of prof reviews
    prof_reviews = prof.reviews

    # iterate through all prof reviews and add to review list
    review_list = []
    for prof_review in prof_reviews:
        review = prof_review.review
        review_object = get_prof_review_info(review)
        if review_object:
            review_list.append(review_object)
    
    if(len(review_list) == 0):
        return None
    
    review_list = sorted(review_list, key=operator.itemgetter('numDisliked'))
    review_list = sorted(review_list, key=operator.itemgetter('numLiked'), reverse=True)

    top_review = review_list[0]

    return top_review

def get_course_top_review(course):
    """
    Get the top-rated review for the specified course

    Args:
        course (model instance): course

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
    # obtain list of course reviews
    course_reviews_ids = []
    course_reviews = course.reviews
    for i in range(len(course.reviews)):
        course_reviews_ids.append(course.reviews[i].id)

    # if course is parent topic, obtain reviews from children topics
    if(course.topic_num != -1):
        topic = course.topic
        for topic_course in topic.courses:
            topic_course_reviews = topic_course.reviews.copy()
            for i in range(len(topic_course_reviews)):
                if(topic_course_reviews[i].id in course_reviews_ids):
                    continue
                course_reviews_ids.append(topic_course_reviews[i].id)
                course_reviews.append(topic_course_reviews[i])

    # iterate through all course reviews and add to review list
    review_list = []
    for course_review in course_reviews:
        review = course_review.review
        review_object = get_course_review_info(review)
        if review_object:
            review_list.append(review_object)
    
    if(len(review_list) == 0):
        return None
    
    review_list = sorted(review_list, key=operator.itemgetter('numDisliked'))
    review_list = sorted(review_list, key=operator.itemgetter('numLiked'), reverse=True)

    top_review = review_list[0]

    return top_review
