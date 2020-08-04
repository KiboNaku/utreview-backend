from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
import random

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/api/user_feedback', methods=['POST'])
def user_feedback():

    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    message = request.get_json()['message']

    msg = Message(
        'User Feedback',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=["utexas.review@gmail.com"])

    msg.html = render_template(
        'user_feedback.html', first_name=first_name, last_name=last_name, email=email, message=message)
    mail.send(msg)

    return 'Feedback Received'


@app.route('/api/report_comment', methods=['POST'])
def report_comment():

    review_id = request.get_json()['review_id']
    is_course = request.get_json()['is_course']
    selected_options = request.get_json()['selected_options']
    other_selected = request.get_json()['other_selected']
    other_option = request.get_json()['other_option']

    if(is_course):
        course_review = CourseReview.query.filter_by(id=review_id).first()
        review_topic = "Course"
        author_email = course_review.review.author.email
        review_topic_name = course_review.course.dept.abr + " " + course_review.course.num
        review_comments = course_review.comments
    else:
        prof_review = ProfReview.query.filter_by(id=review_id).first()
        review_topic = "Professor"
        author_email = prof_review.review.author.email
        review_topic_name = prof_review.prof.first_name + " " + prof_review.prof.last_name
        review_comments = prof_review.comments

    if(not other_selected):
        other_option = "N/A"

    msg = Message(
        'Report Comment',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=["utexas.review@gmail.com"])

    msg.html = render_template(
        'report_comment.html', options_selected=selected_options, other_selected=other_selected, other_option=other_option, review_topic=review_topic,
        author_email=author_email, review_topic_name=review_topic_name, review_comments=review_comments, review_id=review_id)
    mail.send(msg)

    return 'Feedback Received'


@app.route('/api/report_bug', methods=['POST'])
def report_bug():

    page = request.get_json()['page']
    bug_type = request.get_json()['bug_type']
    description = request.get_json()['description']

    msg = Message(
        'Report Bug',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=["utexas.review@gmail.com"])

    msg.html = render_template(
        'report_bug.html', page=page, bug_type=bug_type, description=description)
    mail.send(msg)

    return 'Feedback Received'
