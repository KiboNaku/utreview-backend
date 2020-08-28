"""
This file contains routes to fetch information needed on the  page:
    get_utplus_course,
    get_utplus_prof

"""

import timeago, datetime
import json
import operator
from flask import request, jsonify
from utreview.models import *
from utreview import app
from .catalyst import course_median_grade, prof_median_grade
from .profile_info import get_parent_id

@app.route('/api/utplus_course', methods=['POST'])
def utplus_course():
    """
    Extracts all information needed for a course on UT Plus extension

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
    course_ratings = get_course_ratings(course)
    top_review = get_top_review(course)

    # return object storing all course details information
    result = jsonify({"course_info": course_info,
                      "course_ratings": course_ratings,
                      "top_review": top_review
                      })

    return result

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

    return course_link

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

def get_review_info(review):
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
            'likePressed' (boolean): whether the current user liked the review
            'dislikePressed' (boolean): whether the current user disliked the review
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

def get_top_review(course):
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
            for i in range(len(topic_course.reviews)):
                if(topic_course.reviews[i].id in course_reviews_ids):
                    continue
                course_reviews_ids.append(topic_course.reviews[i].id)
                course_reviews.append(topic_course.reviews[i])

    # iterate through all course reviews and add to review list
    review_list = []
    for course_review in course_reviews:
        review = course_review.review
        review_object = get_review_info(review)
        if review_object:
            review_list.append(review_object)
    
    if(len(review_list) == 0):
        return None
    
    review_list.sort(key=operator.itemgetter('numDisliked'), reverse=True)
    review_list.sort(key=operator.itemgetter('numLiked'))

    top_review = review_list[0]

    return top_review
