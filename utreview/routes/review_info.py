from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, json
from flask_jwt_extended import (create_access_token)
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
    season = request.get_json()['semester']
    year = request.get_json()['year']
    user_email = request.get_json()['user_email']
    course_comments = request.get_json()['course_comments']
    prof_comments = request.get_json()['prof_comments']
    course_approval = request.get_json()['course_approval']
    prof_approval = request.get_json()['prof_approval']
    course_usefulness = int(request.get_json()['course_usefulness'])
    course_difficulty = int(request.get_json()['course_difficulty'])
    course_workload = int(request.get_json()['course_workload'])
    grade = request.get_json()['grade']
    prof_clear = int(request.get_json()['prof_clear'])
    prof_engaging = int(request.get_json()['prof_engaging'])
    prof_grading = int(request.get_json()['prof_grading'])

    sem = None
    if(season == "Fall"):
        sem = 9
    elif(season == "Summer"):
        sem = 6
    elif(season == "Spring"):
        sem = 2

    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()
    semester = Semester.query.filter_by(semester=sem, year=year).first()
    if(semester == None):
        semester = Semester(semester=sem, year=year)
        db.session.add(semester)
        db.session.commit()

    update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, False, None)
    update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, False, None)

    review = Review(user_id=user.id, sem_id=semester.id, grade=grade, date_posted=datetime.utcnow())
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

def update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, editing, prev_course_review):
    if(editing):
        num_liked = course.approval * course.num_ratings
        if(course_approval): 
            if(not prev_course_review.approval):
                course.approval = (num_liked + 1)/(course.num_ratings)
        else:
            if(prev_course_review.approval):
                course.approval = (num_liked - 1)/(course.num_ratings)
        course.usefulness = (course.usefulness * course.num_ratings - prev_course_review.usefulness + course_usefulness)/(course.num_ratings)
        course.difficulty = (course.difficulty * course.num_ratings - prev_course_review.difficulty + course_difficulty)/(course.num_ratings)
        course.workload = (course.workload * course.num_ratings - prev_course_review.workload + course_workload)/(course.num_ratings)
    else:
        if(course.num_ratings == 0):
            if(course_approval):
                course.approval = 1
            else:
                course.approval = 0
            course.usefulness = course_usefulness
            course.difficulty = course_difficulty
            course.workload = course_workload
            course.num_ratings = 1
        else:
            num_liked = course.approval * course.num_ratings
            if(course_approval):            
                course.approval = (num_liked + 1)/(course.num_ratings + 1)
            else:
                course.approval = num_liked/(course.num_ratings + 1)
            course.usefulness = (course.usefulness * course.num_ratings + course_usefulness)/(course.num_ratings + 1)
            course.difficulty = (course.difficulty * course.num_ratings + course_difficulty)/(course.num_ratings + 1)
            course.workload = (course.workload * course.num_ratings + course_workload)/(course.num_ratings + 1)
            course.num_ratings = course.num_ratings + 1
    
    db.session.commit()

def update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, editing, prev_prof_review):
    if(editing):
        num_liked = prof.approval * prof.num_ratings
        if(prof_approval):
            if(not prev_prof_review.approval):
                prof.approval = (num_liked + 1)/(prof.num_ratings)
        else:
            if(prev_prof_review.approval):
                prof.approval = (num_liked - 1)/(prof.num_ratings)
        prof.clear = (prof.clear * prof.num_ratings - prev_prof_review.clear + prof_clear)/(prof.num_ratings)
        prof.engaging = (prof.engaging * prof.num_ratings - prev_prof_review.engaging + prof_engaging)/(prof.num_ratings)
        prof.grading = (prof.grading * prof.num_ratings - prev_prof_review.grading + prof_grading)/(prof.num_ratings)
    else:
        if(prof.num_ratings == 0):
            if(prof_approval):
                prof.approval = 1
            else:
                prof.approval = 0
            prof.clear = prof_clear
            prof.engaging = prof_engaging
            prof.grading = prof_grading
            prof.num_ratings = 1
        else:
            num_liked = prof.approval * prof.num_ratings
            if(prof_approval):            
                prof.approval = (num_liked + 1)/(prof.num_ratings + 1)
            else:
                prof.approval = num_liked/(prof.num_ratings + 1)
            prof.clear = (prof.clear * prof.num_ratings + prof_clear)/(prof.num_ratings + 1)
            prof.engaging = (prof.engaging * prof.num_ratings + prof_engaging)/(prof.num_ratings + 1)
            prof.grading = (prof.grading * prof.num_ratings + prof_grading)/(prof.num_ratings + 1)
            prof.num_ratings = prof.num_ratings + 1

    db.session.commit()


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
    season = request.get_json()['semester']
    year = request.get_json()['year']
    user_email = request.get_json()['user_email']
    
    sem = None
    if(season == "Fall"):
        sem = 9
    elif(season == "Summer"):
        sem = 6
    elif(season == "Spring"):
        sem = 2

    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()
    sem = Semester.query.filter_by(semester=sem, year=year).first()
    if(sem == None):
        result_review = {
            'user_email': user_email,
            'profId': prof.id,
            'courseId': course.id
        }
        result = jsonify({'result': result_review})
        return result
    
    course_name = course.dept.abr + " " + course.num
    prof_name = prof.first_name + " " + prof.last_name

    user_reviews = user.reviews_posted
    num_duplicates = 0
    duplicate_course_sem = False
    duplicate_course_prof = False
    for user_review in user_reviews:
        if(user_review.course_review[0].course_id == course.id and user_review.prof_review[0].prof_id == prof_id):
            duplicate_course_prof = True
        if(user_review.semester.semester == sem.semester and user_review.semester.year == sem.year):
            if(user_review.course_review[0].course_id == course.id):
                duplicate_course_sem = True
        if(user_review.course_review[0].course_id == course.id):
            num_duplicates += 1

    if duplicate_course_sem:
        result = jsonify({'error': f"""You have already submitted a review for {course_name} for the {season} {year} semester. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    elif num_duplicates >= 5:
        result = jsonify({'error': f"""You have exceeded the maximum amount of review submissions for {course_name}. 
        If you would like to edit an existing review, please visit your profile for a list of your exisitng reviews."""})
    elif duplicate_course_prof:
        result = jsonify({'error': f"""You have already submitted a review for {course_name} taught by {prof_name}. 
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
    course_usefulness = int(request.get_json()['course_usefulness'])
    course_difficulty = int(request.get_json()['course_difficulty'])
    course_workload = int(request.get_json()['course_workload'])
    grade = request.get_json()['grade']
    prof_clear = int(request.get_json()['prof_clear'])
    prof_engaging = int(request.get_json()['prof_engaging'])
    prof_grading = int(request.get_json()['prof_grading'])

    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    review = Review.query.filter_by(id=review_id).first()
    review.grade = grade
    review.date_posted = datetime.utcnow()

    prev_course_review = CourseReview.query.filter_by(review_id=review.id).first()
    prev_prof_review = ProfReview.query.filter_by(review_id=review.id).first()

    update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, True, prev_course_review)
    update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, True, prev_prof_review)

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

@app.route('/api/delete_review', methods=['POST'])
def delete_review():
    """
    Given a review id, delete the review from the database
    Also update prof and course metrics to reflect review deletion

    Args (sent from front end):
        review_id (int): review id

    Returns:

    """
    review_id = request.get_json()['reviewId']

    review = Review.query.filter_by(id=review_id).first()
    prev_course_review = CourseReview.query.filter_by(review_id=review.id).first()
    prev_prof_review = ProfReview.query.filter_by(review_id=review.id).first()
    for liked in prev_course_review.users_liked:
        db.session.delete(liked)
    for disliked in prev_course_review.users_disliked:
        db.session.delete(disliked)
    for liked in prev_prof_review.users_liked:
        db.session.delete(liked)
    for disliked in prev_prof_review.users_disliked:
        db.session.delete(disliked)
    db.session.commit()
    course = prev_course_review.course
    prof = prev_prof_review.prof

    if(course.num_ratings <= 1):
        course.num_ratings = 0
        course.approval = None
        course.usefulness = None
        course.difficulty = None
        course.workload = None
    else:
        num_liked = course.approval * course.num_ratings
        if(prev_course_review.approval): 
            course.approval = (num_liked - 1)/(course.num_ratings - 1)
        else:
            course.approval = (num_liked)/(course.num_ratings - 1)
        course.usefulness = (course.usefulness * course.num_ratings - prev_course_review.usefulness)/(course.num_ratings - 1)
        course.difficulty = (course.difficulty * course.num_ratings - prev_course_review.difficulty)/(course.num_ratings - 1)
        course.workload = (course.workload * course.num_ratings - prev_course_review.workload )/(course.num_ratings - 1)
        course.num_ratings = course.num_ratings - 1
    db.session.commit()

    if(prof.num_ratings <= 1):
        prof.num_ratings = 0
        prof.approval = None
        prof.clear = None
        prof.engaging = None
        prof.grading = None
    else:
        num_liked = prof.approval * prof.num_ratings
        if(prev_prof_review.approval):
            prof.approval = (num_liked - 1)/(prof.num_ratings - 1)
        else:
            prof.approval = (num_liked)/(prof.num_ratings - 1)
        prof.clear = (prof.clear * prof.num_ratings - prev_prof_review.clear)/(prof.num_ratings - 1)
        prof.engaging = (prof.engaging * prof.num_ratings - prev_prof_review.engaging)/(prof.num_ratings - 1)
        prof.grading = (prof.grading * prof.num_ratings - prev_prof_review.grading)/(prof.num_ratings - 1)
        prof.num_ratings = prof.num_ratings - 1

    db.session.delete(prev_course_review)
    db.session.delete(prev_prof_review)
    db.session.delete(review)
    db.session.commit()

    return "success"

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
    print(review_id)
    print(user)
    
    if(is_course):
        course_review = CourseReview.query.filter_by(id=review_id).first()
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
