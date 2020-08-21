"""
This file contains routes to populate courses/profs on the search results page:
    populate_results,
    populate_all,
    populate_search
"""

from flask import request, jsonify
from utreview.models import *
from utreview import app, course_ix, prof_ix
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

    return result


def populate_search(courses_query, profs_query, search):
    """
    Given a search value, search, return all profs and courses that relate to the search

    Args:
        courses_query (course query): all courses in the database
        profs_query (prof query): all profs in the database
        search (string): user search value

    Returns:
        courses_list (list), prof_list (list) : list of courses and profs respectively
    """
    # initialize lists to store courses/profs
    courses_list = []
    profs_list = []
    course_ids = []
    prof_ids = []
    search_tokens = search.split()

    # use search engine library to search through courses with search token
    with course_ix.searcher() as searcher:
        query = QueryParser("content", course_ix.schema).parse(search)
        results = searcher.search(query, limit=50)

        # add result to course list if not already added
        for result in results:
            course_id = int(result["index"])
            if(course_id in course_ids):
                continue
            else:
                course_ids.append(course_id)
                course = Course.query.filter_by(id=course_id).first()
                append_course(course, courses_list, profs_list, prof_ids)

    # check if search value is a substring of a course name         
    for course in courses_query:
        course_str = course.dept.abr + course.num
        course_str = course_str.lower().replace(" ", "")

        if search.replace(" ", "") in course_str:
            if(course.id in course_ids):
                continue
            else:
                course_ids.append(course.id)
                append_course(course, courses_list, profs_list, prof_ids)

    # use search engine library to search through profs with search token
    with prof_ix.searcher() as searcher:
        query = QueryParser("content", prof_ix.schema).parse(search)
        results = searcher.search(query, limit=50)

        # add result to prof list if not already added
        for result in results:
            prof_id = int(result["index"])
            if(prof_id in prof_ids):
                continue
            else:
                prof_ids.append(prof_id)
                prof = Prof.query.filter_by(id=prof_id).first()
                append_prof(prof, profs_list, courses_list, course_ids)

    # check if search value is substring of prof name
    for prof in profs_query:
        prof_str = prof.first_name + prof.last_name
        prof_str = prof_str.lower().replace(" ", "")

        if search.replace(" ", "") in prof_str:
            if(prof.id in prof_ids):
                continue
            else:
                prof_ids.append(prof.id)
                append_prof(prof, profs_list, courses_list, course_ids)

    # check if no results found
    if(len(courses_list) < 1):
        courses_list = "empty"
    if(len(profs_list) < 1):
        profs_list = "empty"

    return courses_list, profs_list


def populate_all(courses_query, profs_query):
    """
    Return a list of all profs and courses 

    Args:
        courses_query (course query): all courses in the database
        profs_query (prof query): all profs in the database

    Returns:
        courses_list (list), prof_list (list) : list of courses and profs respectively
    """
    # intialize lists to store courses/profs
    s_time = time.time()
    courses_list = []
    profs_list = []

    # for every course in the database, add to courses list
    for course in courses_query:
        dept = course.dept
        course_object = {
            'id': course.id,
            'courseDept': dept.abr,
            'courseNum': course.num,
            'courseTitle': course.title,
            'courseTopic': course.topic_num,
            'approval': round(course.approval, 2) * 100 if course.approval != None else None,
            'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
            'numRatings': course.num_ratings,
            'semesters': (course.current_sem, course.next_sem, course.future_sem)
        }
        courses_list.append(course_object)

    # for every prof in the database, add to profs list
    for prof in profs_query:
        prof_object = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'approval': round(prof.approval, 2) * 100 if prof.approval != None else None,
            'eCIS': round(prof.ecis_avg, 1) if prof.ecis_avg != None else None,
            'numRatings': prof.num_ratings,
            'semesters': (prof.current_sem, prof.next_sem, prof.future_sem)
        }
        profs_list.append(prof_object)

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
    # for all the profs that teach the course, add it to profs list if not already there
    dept = course.dept
    for course_pc in course.prof_course:
        prof = course_pc.prof
        if(prof.id in prof_ids):
            continue
        prof_ids.append(prof.id)
        prof_object = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'approval': round(prof.approval, 2) * 100 if prof.approval != None else None,
            'eCIS': round(prof.ecis_avg, 1) if prof.ecis_avg != None else None,
            'numRatings': prof.num_ratings,
            'semesters': (prof.current_sem, prof.next_sem, prof.future_sem)
        }
        profs_list.append(prof_object)

    # add course object to courses list
    course_object = {
        'id': course.id,
        'courseDept': dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseTopic': course.topic_num,
        'approval': round(course.approval, 2) * 100 if course.approval != None else None,
        'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
        'numRatings': course.num_ratings,
        'semesters': (course.current_sem, course.next_sem, course.future_sem)
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
    # for all the courses taught by the prof, add it to courses list if not already there
    for prof_pc in prof.prof_course:
        course = prof_pc.course
        dept = course.dept
        if(course.id in course_ids):
            continue
        course_ids.append(course_ids)
        course_object = {
            'id': course.id,
            'courseDept': dept.abr,
            'courseNum': course.num,
            'courseTitle': course.title,
            'courseTopic': course.topic_num,
            'approval': round(course.approval, 2) * 100 if course.approval != None else None,
            'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
            'numRatings': course.num_ratings,
            'semesters': (course.current_sem, course.next_sem, course.future_sem)
        }
        courses_list.append(course_object)

    # add prof object to profs list
    prof_object = {
        'id': prof.id,
        'firstName': prof.first_name,
        'lastName': prof.last_name,
        'approval': round(prof.approval, 2) * 100 if prof.approval != None else None,
        'eCIS': round(prof.ecis_avg, 1) if prof.ecis_avg != None else None,
        'numRatings': prof.num_ratings,
        'semesters': (prof.current_sem, prof.next_sem, prof.future_sem)
    }
    profs_list.append(prof_object)