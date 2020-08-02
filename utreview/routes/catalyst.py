import timeago, datetime
import requests
import sqlite3
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from utreview.models import *
from utreview import app, db, bcrypt, jwt, course_ix, prof_ix, sem_current, sem_next

@app.route('/api/grade_distributions', methods=['POST'])
def grade_distributions():

    course_dept = request.get_json()['course_dept']
    course_num = request.get_json()['course_num']
    prof_first = request.get_json()['prof_first']
    prof_last = request.get_json()['prof_last']
    prof_last = prof_last.split()
    prof_name = prof_last[len(prof_last) - 1] + ", " + prof_first

    receive = requests.get('https://rawgit.com/shishirjessu/db/master/grades.db')
    with open(r'C:\\Users\\zhang\\OneDrive\\Projects\\UTFlow-Backend\\utflow-backend\\grades.db', 'wb') as f:
        f.write(receive.content)

    database = r'C:\\Users\\zhang\\OneDrive\\Projects\\UTFlow-Backend\\utflow-backend\\grades.db'
    conn = create_connection(database)
    with conn:
        grades = select_row(conn, course_dept, prof_name, course_num)
        print(grades)
    
    return jsonify(grades)

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def select_row(conn, dept, prof_name, course_num):

    cur = conn.cursor()
    query = "SELECT * from agg WHERE sem like '%Aggregate%'"
    query += " and dept like '%" + dept + "%'"
    query += " and prof like '%" + prof_name + "%'"
    query += " and course_nbr like '%" + course_num + "%'"
    cur.execute(query)

    rows = cur.fetchall()
    if len(rows) == 0:
        return None

    A = A_minus = B_plus = B = B_minus = C_plus = C = C_minus = D_plus = D = D_minus = F = 0

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