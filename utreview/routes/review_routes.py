from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from course_info import get_course_name
from prof_info import get_prof_name
from utreview.models import *
from utreview import app, db, bcrypt, jwt

@app.route('/api/new_review', methods=['POST'])
def new_review():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    course_comments = request.get_json()['course_comments']
    prof_comments = request.get_json()['prof_comments']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']
    year = request.get_json()['year']
    semester = request.get_json()['semester']

    course_abr, course_no = get_course_name(course_name)
    prof_first, prof_last = get_prof_name(prof_name)

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(first_name=prof_first, last_name=prof_last).first()

    semester_no = 9
    if(semester == "Fall"):
        semester_no = 9
    elif(semester == "Spring"):
        semester_no = 2
    elif(semester == "Summer"):
        semester_no = 6

    review = Review(user_id=user.id, semester=semester_no, year=year)
    db.session.add(review)
    db.session.commit()

    course_review = CourseReview(review_id=review.id, course_id=course.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, 
                                 workload=course_workload, comments=course_comments)
    prof_review = ProfReview(review_id=review.id, prof_id=prof.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading, 
                               comments=prof_comments)

    db.session.add(course_review)
    db.session.add(prof_review)
    db.session.commit()

    result_review = {
        'id': review.id,
        'user_email': user_email,
        'prof_name': prof_name,
        'course_name': course_name
    }
    result = jsonify({'result': result_review})

    return result


@app.route('/api/review_error', methods=['POST'])
def review_error():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    year = request.get_json()['year']
    semester = request.get_json()['semester']

    semester_no = 9
    if(semester == "Fall"):
        semester_no = 9
    elif(semester == "Spring"):
        semester_no = 2
    elif(semester == "Summer"):
        semester_no = 6

    course_abr, course_no = get_course_name(course_name)
    prof_first, prof_last = get_prof_name(prof_name)

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(first_name=prof_first, last_name=prof_last).first()

    user_reviews = user.reviews_posted
    num_duplicates = 0
    duplicate = False
    for user_review in user_reviews:
        if(user_review.semester == semester_no and user_review.year == year):
            if(user_review.course_review.course_id == course.id):
                duplicate = True

    if duplicate:
        result = jsonify({'error': f"""You have already submitted a review for {course_name} for the {semester} {year} semester. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    elif num_duplicates >= 5:
        result = jsonify({'error': f"""You have exceeded the maximum amount of review submissions for {course_name}. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    else:
        result_review = {
            'user_email': user_email,
            'prof_name': prof_name,
            'course_name': course_name
        }
        result = jsonify({'result': result_review})

    return result


@app.route('/api/edit_review', methods=['POST'])
def edit_review():
    review_id = request.get_json()['review_id']
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    course_comments = request.get_json()['course_comments']
    prof_comments = request.get_json()['prof_comments']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']
    year = request.get_json()['year']
    semester = request.get_json()['semester']

    semester_no = 9
    if(semester == "Fall"):
        semester_no = 9
    elif(semester == "Spring"):
        semester_no = 2
    elif(semester == "Summer"):
        semester_no = 6

    course_abr, course_no = get_course_name(course_name)
    prof_first, prof_last = get_prof_name(prof_name)

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(first_name=prof_first, last_name=prof_last).first()

    review = Review.query.filter_by(id=review_id).first()
    review.year = year
    review.semester = semester_no
    
    prev_course_review = CourseReview.query.filter_by(review_id=review.id)
    prev_prof_review = ProfReview.query.filter_by(review_id=review.id)

    db.session.delete(prev_course_review)
    db.session.delete(prev_prof_review)
    db.session.commit()

    course_review = CourseReview(review_id=review.id, course_id=course.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, 
                                 workload=course_workload, comments=course_comments)
    prof_review = ProfReview(review_id=review.id, prof_id=prof.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading, 
                               comments=prof_comments)

    db.session.add(course_review)
    db.session.add(prof_review)
    db.session.commit()
    result_review = {
        'id': review.id,
        'user_email': user_email,
        'prof_name': prof_name,
        'course_name': course_name
    }
    result = jsonify({'result': result_review})

    return result

@app.route('/api/review_feedback', methods=['POST'])
def review_feedback():
    is_like = request.get_json()['like']
    user_email = request.get_json()['userEmail']
    review_id = request.get_json()['reviewId']

    user = User.query.filter_by(email=user_email).first()

    if(is_like):
        review_dislike = ReviewDisliked.query.filter_by(user_id=user.id, review_id=review_id).first()
        if(review_dislike):
            db.session.delete(review_dislike)
            review_like = ReviewLiked(user_id=user.id, review_id=review_id)
            db.session.add(review_like)
            db.session.commit()
        else:
            review_like = ReviewLiked.query.filter_by(user_id=user.id, review_id=review_id).first()
            if(review_like):
                db.session.delete(review_like)
            else:
                review_like = ReviewLiked(user_id=user.id, review_id=review_id)
                db.session.add(review_like)
            db.session.commit()
    else:
        review_like = ReviewLiked.query.filter_by(user_id=user.id, review_id=review_id).first()
        if(review_like):
            db.session.delete(review_like)
            review_dislike = ReviewDisliked(user_id=user.id, review_id=review_id)
            db.session.add(review_dislike)
            db.session.commit()
        else:
            review_dislike = ReviewDisliked.query.filter_by(user_id=user.id, review_id=review_id).first()
            if(review_dislike):
                db.session.delete(review_dislike)
            else:
                review_dislike = ReviewDisliked(user_id=user.id, review_id=review_id)
                db.session.add(review_dislike)
            db.session.commit()

    result = jsonify({"result": 'success'})
    return result
