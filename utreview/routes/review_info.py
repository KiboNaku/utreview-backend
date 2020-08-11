"""
This file contains all the routes related to reviews and the review form: 
    save_review
    new_review
    edit_review
    delete_review
    review_error
    review_feedback
"""

from flask import request, jsonify
from utreview.models import *
from utreview import app, db, bcrypt, jwt
import datetime

def semester_to_number(semester):
    """
    Converts string representation of semester to number representation

    Args:
        semester (string): string representation of semester

    Returns:
        sem (int): integer representation of semester
    """
    sem = None
    if(semester == "Fall"):
        sem = 9
    elif(semester == "Summer"):
        sem = 6
    elif(semester == "Spring"):
        sem = 2
    
    return sem

@app.route('/api/save_review', methods=['POST'])
def save_review():
    """
    Processes a review draft submitted by the user and adds it to the database

    Args (sent from front end):
        review_id(int): review id
        course_id (int): course id
        prof_id (int): prof id
        semester (string): semester season (Fall, Spring, or Summer)
        year (int): year
        user_email (string): user utexas email
        course_comments (string): course comments
        prof_comments (string): prof comments
        course_approval (boolean): approval rating
        prof_approval (boolean): approval rating
        course_usefulness (int): usefulness rating
        course_difficulty (int): difficulty rating
        course_workload (int): workload rating
        grade (string): grade (A - F)
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
    # get args from front end
    review_id = request.get_json()['review_id']
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

    # convert semester to number
    sem = semester_to_number(season)

    # obtain course, prof, and user model instances
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    # create new semester instance if it doesn't already exist
    semester = Semester.query.filter_by(semester=sem, year=year).first()
    if(semester == None):
        semester = Semester(semester=sem, year=year)
        db.session.add(semester)
        db.session.commit()
    
    # create a new review if review doesn't already exist, otherwise update old review
    if(review_id != None):
        review = Review.query.filter_by(id=review_id).first()
        prev_course_review = CourseReview.query.filter_by(review_id=review.id).first()
        prev_prof_review = ProfReview.query.filter_by(review_id=review.id).first()
        db.session.delete(prev_course_review)
        db.session.delete(prev_prof_review)
        db.session.commit()
    else:
        review = Review(user_id=user.id, sem_id=semester.id, grade=grade, date_posted=datetime.utcnow(), submitted=False)
        db.session.add(review)
        db.session.commit()

    # update review with new course review and prof review
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

@app.route('/api/new_review', methods=['POST'])
def new_review():
    """
    Processes a new review submitted by the user and adds it to the database

    Args (sent from front end):
        review_id (int) review id
        course_id (int): course id
        prof_id (int): prof id
        semester (string): semester season (Fall, Spring, or Summer)
        year (int): year
        user_email (string): user utexas email
        course_comments (string): course comments
        prof_comments (string): prof comments
        course_approval (boolean): approval rating
        prof_approval (boolean): approval rating
        course_usefulness (int): usefulness rating
        course_difficulty (int): difficulty rating
        course_workload (int): workload rating
        grade (string): grade (A - F)
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
    # get args from front end
    review_id = request.get_json()['review_id']
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

    # convert semester to number
    sem = semester_to_number(season)
    
    # obtain course, prof, and user model instances
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    # create new semester instance if it doesn't already exist
    semester = Semester.query.filter_by(semester=sem, year=year).first()
    if(semester == None):
        semester = Semester(semester=sem, year=year)
        db.session.add(semester)
        db.session.commit()

    # update course and professor metrics with ratings from review
    update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, False, None)
    update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, False, None)

    review = Review(user_id=user.id, sem_id=semester.id, grade=grade, date_posted=datetime.datetime.utcnow(), submitted=True)
    db.session.add(review)
    db.session.commit()

    # create new prof review and course review instances
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

def update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, editing, prev_course_review, commit=False):
    """
    Updates a course instance's overall metrics using ratings provided from the review form

    Args:
        course (model instance): course to update
        course_approval (boolean): approval rating
        course_difficulty (int): difficulty rating
        course_usefulness (int): usefulness rating
        course_workload (int): workload rating
        editing (boolean): true if updating an old review, false if creating a new review
        prev_course_review (model instance): contains previous course ratings
    """
    # if editing an old review, recalculate averages by removing values from previous review
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
        # if this is the first rating, initialize averages from null
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
            # recalculate averages based on new review ratings
            num_liked = course.approval * course.num_ratings
            if(course_approval):            
                course.approval = (num_liked + 1)/(course.num_ratings + 1)
            else:
                course.approval = num_liked/(course.num_ratings + 1)
            course.usefulness = (course.usefulness * course.num_ratings + course_usefulness)/(course.num_ratings + 1)
            course.difficulty = (course.difficulty * course.num_ratings + course_difficulty)/(course.num_ratings + 1)
            course.workload = (course.workload * course.num_ratings + course_workload)/(course.num_ratings + 1)
            course.num_ratings = course.num_ratings + 1
    
    if commit:
        db.session.commit()

def update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, editing, prev_prof_review, commit=False):
    """
    Updates a prof instance's overall metrics using ratings provided from the review form

    Args:
        prof (model instance): prof to update
        prof_approval (boolean): approval rating
        prof_clear (int): clear rating
        prof_engaging (int): engaging rating
        prof_grading (int): grading rating
        editing (boolean): true if updating an old review, false if creating a new review
        prev_prof_review (model instance): contains previous prof ratings
    """
    # if editing an old review, recalculate averages by removing values from previous review
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
        # if this is the first rating, initialize averages from null
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
            # recalculate averages based on new review ratings
            num_liked = prof.approval * prof.num_ratings
            if(prof_approval):            
                prof.approval = (num_liked + 1)/(prof.num_ratings + 1)
            else:
                prof.approval = num_liked/(prof.num_ratings + 1)
            prof.clear = (prof.clear * prof.num_ratings + prof_clear)/(prof.num_ratings + 1)
            prof.engaging = (prof.engaging * prof.num_ratings + prof_engaging)/(prof.num_ratings + 1)
            prof.grading = (prof.grading * prof.num_ratings + prof_grading)/(prof.num_ratings + 1)
            prof.num_ratings = prof.num_ratings + 1

    if commit:
        db.session.commit()


@app.route('/api/review_error', methods=['POST'])
def review_error():
    """
    Makes sure the prof/course/semester combination is valid for the given user,
    returns an error if not valid, returns a result if successful

    Args (sent from front end):
        course_id (int): course id
        prof_id (int): prof id
        semester (string): semester season (Fall, Spring, or Summer)
        year (int): year
        user_email (string): user utexas email
        
    Returns:
        result (json): Returns review info if successful, returns error in the form of a string if invalid
        result_review = {
            'user_email' (string): user utexas email,
            'profId' (int): prof id,
            'courseId' (int): course id
        }
    """ 
    # get args from front end   
    course_id = request.get_json()['course_id']
    prof_id = request.get_json()['prof_id']
    season = request.get_json()['semester']
    year = request.get_json()['year']
    user_email = request.get_json()['user_email']
    
    # convert semester to number
    sem = semester_to_number(season)

    # obtain course, prof, user, and semester model instances
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()
    semester = Semester.query.filter_by(semester=sem, year=year).first()
    
    course_name = course.dept.abr + " " + course.num
    prof_name = prof.first_name + " " + prof.last_name

    user_reviews = user.reviews_posted
    num_duplicates = 0
    duplicate_course_sem = False
    duplicate_course_prof = False

    # iterate through all reviews posted by the user
    for user_review in user_reviews:

        # check for duplicate course/prof combination
        if(user_review.course_review[0].course_id == course.id and user_review.prof_review[0].prof_id == prof_id):
            duplicate_course_prof = True
        
        # check for duplicate course/semester combination
        if(semester != None):
            if(user_review.semester.semester == semester.semester and user_review.semester.year == semester.year):
                if(user_review.course_review[0].course_id == course.id):
                    duplicate_course_sem = True

        # add up the number of duplicate courses
        if(user_review.course_review[0].course_id == course.id):
            num_duplicates += 1

    # return the error if one occurred, otherwise return review information
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
    # get args from front end
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

    # obtain course, prof, and user model instances
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(email=user_email).first()
    prof = Prof.query.filter_by(id=prof_id).first()

    # find review and update grade and date posted
    review = Review.query.filter_by(id=review_id).first()
    review.grade = grade
    review.date_posted = datetime.datetime.utcnow()

    # find old course review and prof review
    course_review = CourseReview.query.filter_by(review_id=review.id).first()
    prof_review = ProfReview.query.filter_by(review_id=review.id).first()

    # update course/prof metrics based off old ratings and new ratings
    update_course_stats(course, course_approval, course_difficulty, course_usefulness, course_workload, True, course_review)
    update_prof_stats(prof, prof_approval, prof_clear, prof_engaging, prof_grading, True, prof_review)

    # update metrics in course/prof objects
    course_review.approval = course_approval
    course_review.difficulty = course_difficulty
    course_review.usefulness = course_usefulness
    course_review.workload = course_workload
    course_review.comments = course_comments

    prof_review.approval = prof_approval
    prof_review.clear = prof_clear
    prof_review.engaging = prof_engaging
    prof_review.grading = prof_grading
    prof_review.comments = prof_comments

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
        "success" if successful
    """
    # get arg from front end
    review_id = request.get_json()['reviewId']

    # obtain review model instances
    review = Review.query.filter_by(id=review_id).first()
    prev_course_review = CourseReview.query.filter_by(review_id=review.id).first()
    prev_prof_review = ProfReview.query.filter_by(review_id=review.id).first()

    # delete review like/dislike instances associated with the review
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

    # update course metrics to reflect rating deletions
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

    # update prof metrics to reflect rating deletion
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

    # delete all review instances
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
    # get args from the front end
    is_like = request.get_json()['like']
    is_course = request.get_json()['isCourse']
    user_email = request.get_json()['userEmail']
    review_id = request.get_json()['reviewId']

    # obtain user model instance
    user = User.query.filter_by(email=user_email).first()
    
    # update course review like/dislike instance
    if(is_course):
        course_review = CourseReview.query.filter_by(id=review_id).first()

        # update model depending on whether the interaction was a like or dislike
        if(is_like):
            review_dislike = CourseReviewDisliked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
            # if a dislike already exists, delete it
            if(review_dislike):
                db.session.delete(review_dislike)
                review_like = CourseReviewLiked(user_id=user.id, course_review_id=course_review.id)
                db.session.add(review_like)
                db.session.commit()
            else:
                # otherwise check if a like already exists
                review_like = CourseReviewLiked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
                
                # if it exists, delete it, otherwise add it
                if(review_like):
                    db.session.delete(review_like)
                else:
                    review_like = CourseReviewLiked(user_id=user.id, course_review_id=course_review.id)
                    db.session.add(review_like)
                db.session.commit()
        else:
            review_like = CourseReviewLiked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
            
            # if a like already exists, delete it
            if(review_like):
                db.session.delete(review_like)
                review_dislike = CourseReviewDisliked(user_id=user.id, course_review_id=course_review.id)
                db.session.add(review_dislike)
                db.session.commit()
            else:
                # otherwise check if a dislike already exists
                review_dislike = CourseReviewDisliked.query.filter_by(user_id=user.id, course_review_id=course_review.id).first()
                
                # if it exists, delete it, otherwise add it
                if(review_dislike):
                    db.session.delete(review_dislike)
                else:
                    review_dislike = CourseReviewDisliked(user_id=user.id, course_review_id=course_review.id)
                    db.session.add(review_dislike)
                db.session.commit()
    else:
        # update prof review like/dislike instance
        prof_review = ProfReview.query.filter_by(review_id=review_id).first()

        # update model depending on whether the interaction was a like or dislike
        if(is_like):
            # if a dislike already exists, delete it
            review_dislike = ProfReviewDisliked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()

            if(review_dislike):
                db.session.delete(review_dislike)
                review_like = ProfReviewLiked(user_id=user.id, prof_review_id=prof_review.id)
                db.session.add(review_like)
                db.session.commit()
            else:
                # otherwise check if a like already exists
                review_like = ProfReviewLiked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
                
                # if it exists, delete it, otherwise add it
                if(review_like):
                    db.session.delete(review_like)
                else:
                    review_like = ProfReviewLiked(user_id=user.id, prof_review_id=prof_review.id)
                    db.session.add(review_like)
                db.session.commit()
        else:
            review_like = ProfReviewLiked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
            
            # if a like already exists, delete it
            if(review_like):
                db.session.delete(review_like)
                review_dislike = ProfReviewDisliked(user_id=user.id, prof_review_id=prof_review.id)
                db.session.add(review_dislike)
                db.session.commit()
            else:
                # otherwise check if a dislike already exists
                review_dislike = ProfReviewDisliked.query.filter_by(user_id=user.id, prof_review_id=prof_review.id).first()
                
                # if it exists, delete it, otherwise add it
                if(review_dislike):
                    db.session.delete(review_dislike)
                else:
                    review_dislike = ProfReviewDisliked(user_id=user.id, prof_review_id=prof_review.id)
                    db.session.add(review_dislike)
                db.session.commit()
    
    result = jsonify({"result": 'success'})
    return result
