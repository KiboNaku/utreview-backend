from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
from course_info import get_course_name
from prof_info import get_prof_name
from utreview.models import *
from utreview import app, db, bcrypt, jwt

@app.route('/api/new_review', methods=['POST'])
def new_review():
    """
    Processes a new review submitted by the user and adds it to the database

    Args (sent from front end):
        course_id (int): course id
        prof_id (int): prof id
        sem_id (int): semester id
        user_email (string): user utexas email
        course_comments (string): course comments
        prof_comments (string): prof comments
        course_approval (boolean): approval rating
        prof_approval (boolean): approval rating
        course_usefulness (int): usefulness rating
        course_difficulty (int): difficulty rating
        course_workload (int): workload rating
        grade (string): grade
        prof_clear (int): clear rating
        prof_engaging (int): engaging rating
        prof_grading (int): grading rating

    Returns:
        result (object): stores basic information about the review
            result_review = {
                'id' (int): review id
                'user_email' (string): user utexas email
                'profId' (int): prof id
                'courseId' (int): course id
            }
    """
    course_id = request.get_json()['course_id']
    prof_id = request.get_json()['prof_id']
    sem_id = request.get_json()['sem_id']
    user_email = request.get_json()['user_email']
    course_comments = request.get_json()['course_comments']
    prof_comments = request.get_json()['prof_comments']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    grade = request.get_json()['grade']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    sem = Semester.query.filter_by(id=sem_id).first()
    review = Review(user_id=user.id, sem_id=sem.id, grade=grade)
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
        'profId': prof.id,
        'courseId': course.id
    }
    result = jsonify({'result': result_review})

    return result


@app.route('/api/review_error', methods=['POST'])
def review_error():
    """
    Makes sure the prof/course/semester combination is valid for the given user,
    returns an error if not valid, returns a result if successful

    Args (sent from front end):
        course_id (int): course id
        prof_id (int): prof id
        sem_id (int): semester id
        user_email (string): user utexas email
        
    Returns:
        result (json): Returns review info if successful, returns error in the form of a string if invalid
        result_review = {
            'user_email' (string): user utexas email,
            'profId' (int): prof id,
            'courseId' (int): course id
        }
    """    
    course_id = request.get_json()['course_id']
    prof_id = request.get_json()['prof_id']
    sem_id = request.get_json()['sem_id']
    user_email = request.get_json()['user_email']

    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()
    sem = Semester.query.filter_by(id=sem_id).first()
    semester = ""
    if(sem.semester == 9):
        semester = "Fall"
    elif(sem.semester == 6):
        semester = "Summer"
    elif(sem.semester == 2):
        semester = "Spring"
    
    course_name = course.dept.abr + " " + course.num

    user_reviews = user.reviews_posted
    num_duplicates = 0
    duplicate = False
    for user_review in user_reviews:
        if(user_review.semester.semester == sem.semester and user_review.semester.year == sem.year):
            if(user_review.course_review.course_id == course.id):
                duplicate = True
        if(user_review.course_review.course_id == course.id):
            num_duplicates += 1

    if duplicate:
        result = jsonify({'error': f"""You have already submitted a review for {course_name} for the {semester} {sem.year} semester. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    elif num_duplicates >= 5:
        result = jsonify({'error': f"""You have exceeded the maximum amount of review submissions for {course_name}. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    else:
        result_review = {
            'user_email': user_email,
            'profId': prof.id,
            'courseId': course.id
        }
        result = jsonify({'result': result_review})

    return result


@app.route('/api/edit_review', methods=['POST'])
def edit_review():
    """
    Processes a review edit submitted by the user and updates the changes to the database

    Args (sent from front end):
        review_id (int): review id
        course_id (int): course id
        prof_id (int): prof id
        user_email (string): user utexas email
        course_comments (string): course comments
        prof_comments (string): prof comments
        course_approval (boolean): approval rating
        prof_approval (boolean): approval rating
        course_usefulness (int): usefulness rating
        course_difficulty (int): difficulty rating
        course_workload (int): workload rating
        grade (string): grade
        prof_clear (int): clear rating
        prof_engaging (int): engaging rating
        prof_grading (int): grading rating

    Returns:
        result (object): stores basic information about the review
            result_review = {
                'id' (int): review id
                'user_email' (string): user utexas email
                'profId' (int): prof id
                'courseId' (int): course id
            }
    """
    review_id = request.get_json()['review_id']
    course_id = request.get_json()['course_id']
    prof_id = request.get_json()['prof_id']
    user_email = request.get_json()['user_email']
    course_comments = request.get_json()['course_comments']
    prof_comments = request.get_json()['prof_comments']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = request.get_json()['course_usefulness']
    course_difficulty = request.get_json()['course_difficulty']
    course_workload = request.get_json()['course_workload']
    grade = request.get_json()['grade']
    prof_clear = request.get_json()['prof_clear']
    prof_engaging = request.get_json()['prof_engaging']
    prof_grading = request.get_json()['prof_grading']

    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    review = Review.query.filter_by(id=review_id).first()
    review.grade = grade

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
        'profId': prof.id,
        'courseId': course.id
    }
    result = jsonify({'result': result_review})

    return result

@app.route('/api/review_feedback', methods=['POST'])
def review_feedback():
    """
    Takes a user's interaction with a course/prof review and adds it (or updates it) to the database

    Args:
        like (boolean): signifies whether the interaction was a like or dislike
        isCourse (boolean): signifies whether the interaction was with a course review or prof review
        userEmail (string): user utexas email
        reviewId (int): review id

    Returns:
        result: success
    """
    is_like = request.get_json()['like']
    is_course = request.get_json()['isCourse']
    user_email = request.get_json()['userEmail']
    review_id = request.get_json()['reviewId']

    user = User.query.filter_by(email=user_email).first()
    
    if(is_course):
        course_review = CourseReview.query.filter_by(review_id=review_id).first()
        if(is_like):
            review_dislike = CourseReviewDisliked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
            if(review_dislike):
                db.session.delete(review_dislike)
                review_like = CourseReviewLiked(user_id=user.id, course_review_id=course_review.id)
                db.session.add(review_like)
                db.session.commit()
            else:
                review_like = CourseReviewLiked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
                if(review_like):
                    db.session.delete(review_like)
                else:
                    review_like = CourseReviewLiked(user_id=user.id, course_review_id=course_review.id)
                    db.session.add(review_like)
                db.session.commit()
        else:
            review_like = CourseReviewLiked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
            if(review_like):
                db.session.delete(review_like)
                review_dislike = CourseReviewDisliked(user_id=user.id, course_review_id=course_review.id)
                db.session.add(review_dislike)
                db.session.commit()
            else:
                review_dislike = CourseReviewDisliked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
                if(review_dislike):
                    db.session.delete(review_dislike)
                else:
                    review_dislike = CourseReviewDisliked(user_id=user.id, course_review_id=course_review.id)
                    db.session.add(review_dislike)
                db.session.commit()
    else:
        prof_review = ProfReview.query.filter_by(review_id=review_id).first()
        if(is_like):
            review_dislike = ProfReviewDisliked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
            if(review_dislike):
                db.session.delete(review_dislike)
                review_like = ProfReviewLiked(user_id=user.id, prof_review_id=prof_review.id)
                db.session.add(review_like)
                db.session.commit()
            else:
                review_like = ProfReviewLiked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
                if(review_like):
                    db.session.delete(review_like)
                else:
                    review_like = ProfReviewLiked(user_id=user.id, prof_review_id=prof_review.id)
                    db.session.add(review_like)
                db.session.commit()
        else:
            review_like = ProfReviewLiked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
            if(review_like):
                db.session.delete(review_like)
                review_dislike = ProfReviewDisliked(user_id=user.id, prof_review_id=prof_review.id)
                db.session.add(review_dislike)
                db.session.commit()
            else:
                review_dislike = ProfReviewDisliked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
                if(review_dislike):
                    db.session.delete(review_dislike)
                else:
                    review_dislike = ProfReviewDisliked(user_id=user.id, course_review_id=prof_review.id)
                    db.session.add(review_dislike)
                db.session.commit()
    
    result = jsonify({"result": 'success'})
    return result
