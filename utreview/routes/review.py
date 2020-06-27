from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from utreview.models import *
from utreview import app, db, bcrypt, jwt

@app.route('/api/new_review', methods=['POST'])
def new_review():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    course_review = request.get_json()['course_review']
    prof_review = request.get_json()['prof_review']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']

    course_parsed = course_name.split()
    if(len(course_parsed) == 3):
        course_abr = course_parsed[0] + " " + course_parsed[1]
        course_no = course_parsed[2]
    else:
        if(len(course_parsed[0]) == 1):
            course_abr = course_parsed[0] + "  "
        elif(len(course_parsed[0]) == 2):
            course_abr = course_parsed[0] + " "
        else:
            course_abr = course_parsed[0]
        course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review(user_posted=user.id, course_id=course.id, professor_id=prof.id,
                    professor_review=prof_review, course_review=course_review)
    db.session.add(review)
    db.session.commit()

    course_rating = CourseRating(review_id=review.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, workload=course_workload)
    prof_rating = ProfessorRating(review_id=review.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading)

    db.session.add(course_rating)
    db.session.add(prof_rating)
    db.session.commit()

    result_review = {
        'user_email': user_email,
        'prof_name': prof_name,
        'course_name': course_name
    }
    result = jsonify({'result': result_review})

    return result


@app.route('/api/duplicate_review', methods=['POST'])
def duplicate_review():
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']

    course_parsed = course_name.split()
    if(len(course_parsed) == 3):
        course_abr = course_parsed[0] + " " + course_parsed[1]
        course_no = course_parsed[2]
    else:
        if(len(course_parsed[0]) == 1):
            course_abr = course_parsed[0] + "  "
        elif(len(course_parsed[0]) == 2):
            course_abr = course_parsed[0] + " "
        else:
            course_abr = course_parsed[0]
        course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review.query.filter_by(user_posted=user.id, 
    professor_id=prof.id, course_id=course.id).first()

    if review:
        result = jsonify({'error': "Review for this course/prof combination already exists for this user"})
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
    course_name = request.get_json()['course_name']
    prof_name = request.get_json()['prof_name']
    user_email = request.get_json()['user_email']
    course_review = request.get_json()['course_review']
    prof_review = request.get_json()['prof_review']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']

    course_parsed = course_name.split()
    if(len(course_parsed) == 3):
        course_abr = course_parsed[0] + " " + course_parsed[1]
        course_no = course_parsed[2]
    else:
        if(len(course_parsed[0]) == 1):
            course_abr = course_parsed[0] + "  "
        elif(len(course_parsed[0]) == 2):
            course_abr = course_parsed[0] + " "
        else:
            course_abr = course_parsed[0]
        course_no = course_parsed[1]

    course_dept = Dept.query.filter_by(abr=course_abr).first()
    course = Course.query.filter_by(
        num=course_no, dept_id=course_dept.id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(name=prof_name).first()

    review = Review.query.filter_by(user_posted=user.id, 
    professor_id=prof.id, course_id=course.id).first()
    
    prev_course_rating = CourseRating.query.filter_by(review_id=review.id)
    prev_prof_rating = ProfessorRating.query.filter_by(review_id=review.id)

    db.session.delete(prev_course_rating)
    db.session.delete(prev_prof_rating)
    db.session.commit()

    course_rating = CourseRating(review_id=review.id, approval=course_approval,
                                 usefulness=course_usefulness, difficulty=course_difficulty, workload=course_workload)
    prof_rating = ProfessorRating(review_id=review.id, approval=prof_approval,
                               clear=prof_clear, engaging=prof_engaging, grading=prof_grading)

    db.session.add(course_rating)
    db.session.add(prof_rating)
    db.session.commit()

    result_review = {
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