"""
This file contains all the routes related to users reporting issues/giving feedback: 
    user_feedback,
    report_comment,
    report_bug
"""

from flask import render_template, request
from utreview.models import *
from utreview import app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message

mail = Mail(app)

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


@app.route('/api/user_feedback', methods=['POST'])
def user_feedback():
    """
    Takes information from the contact us page, formats the information, and sends it as an email
    Args:
        first_name (string): user first name
        last_name (string): user last name
        email (string): user email
        message (string): user message

    """
    # get args from front end
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    message = request.get_json()['message']

    # generate user feedback email
    msg = Message(
        'User Feedback',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=["utexas.review@gmail.com"])

    # send email
    msg.html = render_template(
        'user_feedback.html', first_name=first_name, last_name=last_name, email=email, message=message)
    mail.send(msg)

    return 'Feedback Received'


@app.route('/api/report_comment', methods=['POST'])
def report_comment():
    """
    Takes information from a user's comment report and sends it as an email
    Args:
        review_id (int): review id,
        is_course (boolean): true if the comment is about a course, false if about a prof
        selected_options (list): list of options the user selected that described the comment
        other_selected (boolean): true if the user selected the other option, false if not
        other_option (string): what user entered in the other option, if selected

    """

    # get args from the front end
    review_id = request.get_json()['review_id']
    is_course = request.get_json()['is_course']
    selected_options = request.get_json()['selected_options']
    other_selected = request.get_json()['other_selected']
    other_option = request.get_json()['other_option']

    # format information differently depending on whether the review content is about a course or a prof
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

    # checks to see if the "Other" option was selected
    if(not other_selected):
        other_option = "N/A"

    # generates report comment email
    msg = Message(
        'Report Comment',
        sender=("UT Review", "utexas.review@gmail.com"),
        recipients=["utexas.review@gmail.com"])

    # send email
    msg.html = render_template(
        'report_comment.html', options_selected=selected_options, other_selected=other_selected, other_option=other_option, review_topic=review_topic,
        author_email=author_email, review_topic_name=review_topic_name, review_comments=review_comments, review_id=review_id)
    mail.send(msg)

    return 'Feedback Received'


@app.route('/api/report_bug', methods=['POST'])
def report_bug():
    """
    Takes information from a user's bug report and sends it as an email
    Args:
        page (string): page that user found the bug on
        bug_type (string): the type of bug that was found
        description (string): user description of the bug
    """

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
