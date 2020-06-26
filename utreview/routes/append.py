from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix
from whoosh.index import create_in
from whoosh import scoring
from whoosh.fields import *
from whoosh.qparser import QueryParser
import time

def append_course(course, courses_list, profs_list, prof_ids):
    dept = course.dept
    for course_pc in course.pc:
        prof = course_pc.prof
        if(prof.id in prof_ids):
            continue
        prof_ids.append(prof.id)
        prof_object = {
            'id': prof.id,
            'profName': prof.name,
        }
        profs_list.append(prof_object)
    course_object = {
        'courseNum': dept.abr + " " + course.num,
        'courseName': course.name,
        'deptName': dept.name,
    }
    courses_list.append(course_object)


def append_prof(prof, profs_list, courses_list, course_ids):
    for prof_pc in prof.pc:
        course = prof_pc.course
        dept = course.dept
        if(course.id in course_ids):
            continue
        course_ids.append(course_ids)
        course_object = {
            'courseNum': dept.abr + " " + course.num,
            'courseName': course.name,
        }
        courses_list.append(course_object)

    prof_object = {
        'id': prof.id,
        'profName': prof.name,
    }
    profs_list.append(prof_object)

