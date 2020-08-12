"""
This file contains routes to fetch grade distributions as well as functions to calculate median
grades from UT Catalyst grade distributions
    grade_distributions
    prof_median_grade
    course_median_grade
"""

import requests
import sqlite3

from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix, sem_current, sem_next

@app.route('/api/grade_distributions', methods=['POST'])
def grade_distributions():
    """
    Args (sent from front end):
        course_dept (string): course department
        course_num (string): course num
        prof_first (string): prof first name
        prof_last (string): prof last name

    Returns:
        grades (object): contains number of people obtaining each grade
    """
    # get args from front end
    course_dept = request.get_json()['course_dept']
    course_num = request.get_json()['course_num']
    prof_first = request.get_json()['prof_first']
    prof_last = request.get_json()['prof_last']

    # reformat prof name
    prof_first = prof_first.replace('\'', '')
    prof_last = prof_last.replace('\'', ' ')
    prof_last = prof_last.split()
    prof_name = prof_last[len(prof_last) - 1] + ", " + prof_first

    # code to fetch database from remote
    # receive = requests.get('https://rawgit.com/shishirjessu/db/master/grades.db')
    # with open(r'grades.db', 'wb') as f:
    #     f.write(receive.content)

    # connect to database file
    database = r'grades.db'
    conn = create_connection(database)
    with conn:
        # obtain grade distribution
        grades = get_grades(conn, prof_name, course_dept, course_num)
    
    return jsonify(grades)

def create_connection(db_file):
    """
    Given a database file, establish a connection

    Args:
        db_file (file): database file
    Returns:
        conn (database connection): used to connect to database
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def get_grades(conn, prof_name, course_dept, course_num):
    """
    Obtain grade distribution given a certain course and professor

    Args:
        conn (database connection): used to connect to database
        course_dept (string): course department
        prof_name (string): prof name formatted firstname, lastname
        course_num (string): course num

    Returns:
        result (object): grade distribution
    """

    # make database query
    cur = conn.cursor()
    query = "SELECT * from agg WHERE sem like '%Aggregate%'"
    query += " and dept like '%" + course_dept + "%'"
    query += " and prof like '%" + prof_name + "%'"
    query += " and course_nbr like '%" + course_num + "%'"
    print(query)
    cur.execute(query)

    # fetch row, return None if nothing fetched
    rows = cur.fetchall()
    print(rows)
    if len(rows) == 0:
        return None
    
    A = A_minus = B_plus = B = B_minus = C_plus = C = C_minus = D_plus = D = D_minus = F = 0
    # count number of each type of grade
    for row in rows:
        A += row[6]
        A_minus += row[7]
        B_plus += row[8]
        B += row[9]
        B_minus += row[10]
        C_plus += row[11]
        C += row[12]
        C_minus += row[13]
        D_plus += row[14]
        D += row[15]
        D_minus += row[16]
        F += row[17]

    result = {
        'A': A,
        'A-': A_minus,
        'B+': B_plus,
        'B': B,
        'B-': B_minus,
        'C+': C_plus,
        'C': C,
        'C-': C_minus,
        'D+': D_plus,
        'D': D,
        'D-': D_minus, 
        'F': F
    }
    return result

def course_median_grade(course_dept, course_num, topic_num, course_title):
    """
    Calculate median grade obtained in a course

    Args:
        course_dept (string): course department
        course_num (string): course num
        topic_num (int): course topic num
        course_title (string): course title

    Returns:
        grade (string): median grade
    """
    # code to fetch grade distrubtion data from remote
    # receive = requests.get('https://rawgit.com/shishirjessu/db/master/grades.db')
    # with open(r'C:\\Users\\zhang\\OneDrive\\Projects\\UTFlow-Backend\\utflow-backend\\grades.db', 'wb') as f:
    #     f.write(receive.content)

    #establish connection to database
    database = r'grades.db'
    conn = create_connection(database)
    with conn:
        # make database query
        cur = conn.cursor()
        query = "SELECT * from agg WHERE sem like '%Aggregate%'"
        query += " and dept like '%" + course_dept + "%'"
        query += " and course_nbr like '%" + course_num + "%'"
        if(topic_num > 0):
            query += " and course_name like '%" + course_title + "%'"
        cur.execute(query)

        # fetch rows, return none if nothing fetched
        rows = cur.fetchall()
        if len(rows) == 0:
            return None

        A = A_minus = B_plus = B = B_minus = C_plus = C = C_minus = D_plus = D = D_minus = F = 0   
        # calculate total number of each letter grade
        for row in rows:
            A += row[6]
            A_minus += row[7]
            B_plus += row[8]
            B += row[9]
            B_minus += row[10]
            C_plus += row[11]
            C += row[12]
            C_minus += row[13]
            D_plus += row[14]
            D += row[15]
            D_minus += row[16]
            F += row[17]
        
        # calculate total number of grades and the median index
        num_grades = A + A_minus + B_plus + B + B_minus + C_plus + C + C_minus + D_plus + D + D_minus + F
        median_index = num_grades//2

        # calculate which grade is at the median
        count = 0
        count += A
        if(count > median_index):
            return 'A'
        count += A_minus
        if(count > median_index):
            return 'A-'
        count += B_plus
        if(count > median_index):
            return 'B+'
        count += B
        if(count > median_index):
            return 'B'
        count += B_minus
        if(count > median_index):
            return 'B-'
        count += C_plus
        if(count > median_index):
            return 'C+'
        count += C
        if(count > median_index):
            return 'C'
        count += C_minus
        if(count > median_index):
            return 'C-'
        count += D_plus
        if(count > median_index):
            return 'D+'
        count += D
        if(count > median_index):
            return 'D'
        count += D_minus
        if(count > median_index):
            return 'D-'
        count += F
        if(count > median_index):
            return 'F'

def prof_median_grade(prof_first, prof_last):
    """
    Calculate median grade given by a prof

    Args:
        prof_first (string): prof first name
        prof_last (string): prof last name

    Returns:
        grade (string): median grade
    """
    # code to fetch grade distrubtion data from remote
    # receive = requests.get('https://rawgit.com/shishirjessu/db/master/grades.db')
    # with open(r'C:\\Users\\zhang\\OneDrive\\Projects\\UTFlow-Backend\\utflow-backend\\grades.db', 'wb') as f:
    #     f.write(receive.content)

    # establish connection to database
    database = r'grades.db'
    conn = create_connection(database)

    # reformat prof name
    prof_first = prof_first.replace('\'', '')
    prof_last = prof_last.replace('\'', ' ')
    prof_last = prof_last.split()
    prof_name = prof_last[len(prof_last) - 1] + ", " + prof_first

    with conn:
        # make database query
        cur = conn.cursor()
        query = "SELECT * from agg WHERE sem like '%Aggregate%'"
        query += " and prof like '%" + prof_name + "%'"
        cur.execute(query)

        # fetch rows, return none if nothing fetched
        rows = cur.fetchall()
        if len(rows) == 0:
            return None

        A = A_minus = B_plus = B = B_minus = C_plus = C = C_minus = D_plus = D = D_minus = F = 0   
        # calculate number of each letter grade given
        for row in rows:
            A += row[6]
            A_minus += row[7]
            B_plus += row[8]
            B += row[9]
            B_minus += row[10]
            C_plus += row[11]
            C += row[12]
            C_minus += row[13]
            D_plus += row[14]
            D += row[15]
            D_minus += row[16]
            F += row[17]
        
        # calculate total number of grades and median index
        num_grades = A + A_minus + B_plus + B + B_minus + C_plus + C + C_minus + D_plus + D + D_minus + F
        median_index = num_grades//2

        # calculate which grade is at the median
        count = 0
        count += A
        if(count > median_index):
            return 'A'
        count += A_minus
        if(count > median_index):
            return 'A-'
        count += B_plus
        if(count > median_index):
            return 'B+'
        count += B
        if(count > median_index):
            return 'B'
        count += B_minus
        if(count > median_index):
            return 'B-'
        count += C_plus
        if(count > median_index):
            return 'C+'
        count += C
        if(count > median_index):
            return 'C'
        count += C_minus
        if(count > median_index):
            return 'C-'
        count += D_plus
        if(count > median_index):
            return 'D+'
        count += D
        if(count > median_index):
            return 'D'
        count += D_minus
        if(count > median_index):
            return 'D-'
        count += F
        if(count > median_index):
            return 'F'
        