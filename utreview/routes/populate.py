from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time


@app.route('/api/populate_results', methods=['POST'])
def populate_results():
    start_time = time.time()
    search = request.get_json()['searchValue']
    search = search.lower()
    search_tokens = search.split()

    courses_list = []
    course_ids = []
    profs_list = []
    prof_ids = []

    if(search == " "):
        populate_all(courses_list, profs_list)
        courses = courses_list
        profs = profs_list
        result = jsonify({"courses": courses, "profs": profs})
        elapsed_time = time.time() - start_time
        return result

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
    courses = Course.query.all()
    for course in courses:
        if(search.replace(" ", "") in str(course)):
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

    courses = courses_list
    profs = profs_list
    if(len(courses_list) < 1):
        courses = "empty"
    if(len(profs_list) < 1):
        profs = "empty"

    result = jsonify({"courses": courses, "profs": profs})
    elapsed_time = time.time() - start_time
    print(elapsed_time)
    return result

def populate_all(courses_list, profs_list):
    courses = Course.query.all()
    for course in courses:
        dept = course.dept
        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
            'deptName': dept.name,
        }
        courses_list.append(course_object)
    profs = Prof.query.all()
    for prof in profs:
        prof_object = {
            'id': prof.id,
            'profName': prof.name,
        }
        profs_list.append(prof_object)