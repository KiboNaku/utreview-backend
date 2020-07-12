from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time

from .course_info import get_ecis

@app.route('/api/populate_results', methods=['POST'])
def populate_results():
    """
    Returns a list of courses and profs based on a search value

    Args:
        searchValue (string): user input into search field

    Returns:
        result (json): Contains list of courses and profs
            {
                "courses" (list): list of courses
                    course_object = {
                        'id' (int): course id
                        'courseDept' (string): dept abr
                        'courseNum' (string): course num
                        'courseTitle' (string): course title
                        'courseTopic' (int): course topic number
                        'approval' (int): percentage who liked the course
                        'eCIS' (float): average ecis score of course
                        'numRatings' (int): number of ratings
                    }
                "profs" (list): profs list of profs
                    prof_object = {
                        'id' (int): prof id,
                        'firstName' (string): prof first name,
                        'lastName' (string): prof last name,
                        'approval' (int): percentage who like the prof
                        'eCIS' (float): average ecis score of prof
                        'numRatings' (int): number of ratings
                    }
            }
    """
    s_time = time.time()
    #  parse request search
    search = request.get_json()['searchValue'].lower().strip()

    # initialize list
    courses_list = []
    profs_list = []

    # filter query lists
    courses_query = [course for course in Course.query.all() if course.topic_num <=0]
    profs_query = Prof.query.all()

    # if empty search, then all courses
    if search == "":
        courses_list, profs_list = populate_all(courses_query, profs_query)
    else:
        courses_list, profs_list = populate_search(courses_query, profs_query, search)
    
    result = jsonify({"courses": courses_list, "profs": profs_list})

    print("final:", time.time()-s_time)
    return result


def populate_search(courses_query, profs_query, search):

    courses_list = []
    profs_list = []
    course_ids = []
    prof_ids = []
    search_tokens = search.split()

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
                
    for course in courses_query:
        if search.replace(" ", "") in str(course):
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

    if(len(courses_list) < 1):
        courses_list = "empty"
    if(len(profs_list) < 1):
        profs_list = "empty"

    return courses_list, profs_list


def populate_all(courses_query, profs_query):

    s_time = time.time()
    courses_list = []
    profs_list = []

    for course in courses_query:

        # course_ecis, prof_ecis = get_ecis(course)
        course_ecis, prof_ecis = "", ""
        dept = course.dept
        # course_reviews = course.reviews
        # num_ratings = len(course_reviews)
        num_ratings = 0
        percentLiked = None
        # if(len(course_reviews) == 0):
        #     percentLiked = None
        # else:
        #     percentLiked = 0
        #     for course_review in course_reviews:
        #         if(course_review.approval):
        #             percentLiked += 1
        #     percentLiked = round(percentLiked/len(course_reviews), 2) * 100
        course_object = {
            'id': course.id,
            'courseDept': dept.abr,
            'courseNum': course.num,
            'courseTitle': course.title,
            'courseTopic': course.topic_num,
            'approval': percentLiked,
            'eCIS': course_ecis,
            'numRatings': num_ratings
        }
        courses_list.append(course_object)
    print(time.time()-s_time)
    
    for prof in profs_query:
        course_ecis, prof_ecis = get_ecis(prof)
        prof_reviews = prof.reviews
        num_ratings = len(prof_reviews)
        if(len(prof_reviews) == 0):
            percentLiked = None
        else:
            percentLiked = 0
            for prof_review in prof_reviews:
                if(prof_review.approval):
                    percentLiked += 1
            percentLiked = round(percentLiked/len(prof_reviews), 2) * 100
        prof_object = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'approval': percentLiked,
            'eCIS': prof_ecis,
            'numRatings': num_ratings
        }
        profs_list.append(prof_object)
    print(time.time()-s_time)

    return courses_list, profs_list

def append_course(course, courses_list, profs_list, prof_ids):
    """
    Add a course object made from course to the courses_list,
    also add related professors to the profs_list

    Args:
        course (model instance): course we want to add to the list
        courses_list (list): list of current courses
        profs_list (list): list of current profs
        prof_ids (list): list of current prof ids (to check for duplicates)
    """
    dept = course.dept
    for course_pc in course.prof_course:
        prof = course_pc.prof
        course_ecis, prof_ecis = get_ecis(prof)
        if(prof.id in prof_ids):
            continue
        prof_ids.append(prof.id)
        prof_reviews = prof.reviews
        num_ratings = len(prof_reviews)
        if(len(prof_reviews) == 0):
            percentLiked = None
        else:
            percentLiked = 0
            for prof_review in prof_reviews:
                if(prof_review.approval):
                    percentLiked += 1
            percentLiked = round(percentLiked/len(prof_reviews), 2) * 100
        prof_object = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'approval': percentLiked,
            'eCIS': prof_ecis,
            'numRatings': num_ratings
        }
        profs_list.append(prof_object)
    course_reviews = course.reviews
    num_ratings = len(course_reviews)
    if(len(course_reviews) == 0):
        percentLiked = None
    else:
        percentLiked = 0
        for course_review in course_reviews:
            if(course_review.approval):
                percentLiked += 1
        percentLiked = round(percentLiked/len(course_reviews), 2) * 100
    course_ecis, prof_ecis = get_ecis(course)
    course_object = {
        'id': course.id,
        'courseDept': dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseTopic': course.topic_num,
        'approval': percentLiked,
        'eCIS': course_ecis,
        'numRatings': num_ratings
    }
    courses_list.append(course_object)


def append_prof(prof, profs_list, courses_list, course_ids):
    """
    Add a prof object made from prof to the profs_list,
    also add related courses to the courses_list

    Args:
        prof (model instance): prof we want to add to the list
        courses_list (list): list of current courses
        profs_list (list): list of current profs
        course_ids (list): list of current course ids (to check for duplicates)
    """
    for prof_pc in prof.prof_course:
        course = prof_pc.course
        course_ecis, prof_ecis = get_ecis(course)
        dept = course.dept
        if(course.id in course_ids):
            continue
        course_ids.append(course_ids)
        course_reviews = course.reviews
        num_ratings = len(course_reviews)
        if(len(course_reviews) == 0):
            percentLiked = None
        else:
            percentLiked = 0
            for course_review in course_reviews:
                if(course_review.approval):
                    percentLiked += 1
            percentLiked = round(percentLiked/len(course_reviews), 2) * 100
        course_object = {
            'id': course.id,
            'courseDept': dept.abr,
            'courseNum': course.num,
            'courseTitle': course.title,
            'courseTopic': course.topic_num,
            'approval': percentLiked,
            'eCIS': course_ecis,
            'numRatings': num_ratings
        }
        courses_list.append(course_object)
    course_ecis, prof_ecis = get_ecis(prof)
    prof_reviews = prof.reviews
    num_ratings = len(prof_reviews)
    if(len(prof_reviews) == 0):
        percentLiked = None
    else:
        percentLiked = 0
        for prof_review in prof_reviews:
            if(prof_review.approval):
                percentLiked += 1
        percentLiked = round(percentLiked/len(prof_reviews), 2) * 100
    prof_object = {
        'id': prof.id,
        'firstName': prof.first_name,
        'lastName': prof.last_name,
        'approval': percentLiked,
        'eCIS': prof_ecis,
        'numRatings': num_ratings
    }
    profs_list.append(prof_object)