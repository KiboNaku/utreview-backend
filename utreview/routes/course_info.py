"""
This file contains routes to fetch information needed on the course details page:
    get_course_info,
    get_course_requisites,
    get_course_reviews,
    get_course_schedule,
    get_course_profs

"""

import timeago, datetime
from flask import request, jsonify
from utreview.models import *
from utreview import app
from .catalyst import course_median_grade

@app.route('/api/course_id', methods=['POST'])
def course_id():
    """
    Takes a course pathname and parses it to check if it is a valid course 

    Args:
        courseString (string): course pathname

    Returns:
        result (json): returns the course id and other info if successful, returns an error if failed
    """
    # get args from front end and split by _
    course_string = request.get_json()['courseString']
    course_parsed = course_string.split("_")

    # check to see if input is valid and parse out the course dept, course num, and topic num
    invalid_input = False
    if(len(course_parsed) == 2):
        # if two words, it must be a non topic course
        course_dept = course_parsed[0]
        course_num = course_parsed[1]
        topic_num = -1
    elif(len(course_parsed) == 3):
        # if three words, it must be a topic course
        course_dept = course_parsed[0]
        course_num = course_parsed[1]
        if(not course_parsed[2].isnumeric()):
            invalid_input = True
        else:
            topic_num = int(course_parsed[2])
    else:
        invalid_input = True


    course_found = False
    course_id = None
    parent_id = None

    # if the input is valid
    if(not invalid_input):
        # filter courses by number and topic number
        courses = Course.query.filter_by(num=course_num.upper(), topic_num=topic_num)

        # iterate through all courses
        for course in courses:
            dept = course.dept

            # if the depts are the same, the course has been found
            if(dept.abr.lower().replace(" ", "") == course_dept):
                course_found = True
                course_id = course.id
                result_dept = course.dept.abr
                result_num = course.num
                result_title = course.title

                # if the course is a topic course, find the topic id and parent id
                if(topic_num >= 0):
                    topic_id = course.topic_id

                    # find the parent id
                    for topic in course.topic.courses:
                        if(topic.topic_num == 0):
                            parent_id = topic.id
                else:
                    topic_id = -1

    # return info about the course if found, return error if not found
    if(course_found):
        result = jsonify({"courseId": course_id, "courseDept": result_dept, "courseNum": result_num, "courseTitle": result_title, "topicId": topic_id, "parentId": parent_id, "topicNum": topic_num})
    else:
        result = jsonify({"error": "No course was found"})

    return result

@app.route('/api/course_details', methods=['POST'])
def course_details():
    """
    Extracts all information needed for a particular course and sends it to the front end

    Arguments (Sent from the front end): 
        courseId (int): id of course
        loggedIn (boolean): specifies whether the user is logged in
        userEmail (string): email of user, if logged in

    Returns:
        result(json): jsonified representation of course information
            "course_info" (object): basic course info
            "course_rating" (object): course average ratings
            "course_requisites" (object): course requisites,
            "course_profs" (list): list of profs that teach the course
            "course_schedule" (object): course schedule
            "course_reviews" (list): list of reviews for the course
            "is_parent" (boolean): shows whether course is a parent topic
    """
    # get args from the front end
    course_id = request.get_json()['courseId']
    logged_in = request.get_json()['loggedIn']
    user_email = request.get_json()['userEmail']

    # get user info if logged in
    if(logged_in):
        curr_user = User.query.filter_by(email=user_email).first()
    else:
        curr_user = None

    # get course details information
    course_info, course, is_parent = get_course_info(course_id)
    course_requisites = get_course_requisites(course)
    course_rating, review_list = get_course_reviews(course, logged_in, curr_user, is_parent)
    course_schedule = get_course_schedule(course, is_parent)
    prof_list = get_course_profs(course, is_parent)

    # return object storing all course details information
    result = jsonify({"course_info": course_info,
                      "course_rating": course_rating,
                      "course_requisites": course_requisites,
                      "course_profs": prof_list,
                      "course_schedule": course_schedule,
                      "course_reviews": review_list,
                      "is_parent": is_parent})

    return result

def get_course_info(course_id):
    """
    Uses course id to extract basic course information from database

    Args:
        course_id (int): course id

    Returns:
        course_info (object): contains basic course information
            course_info = {
                'id' (int): course id
                'courseDept' (string): course dept abbreviation
                'courseNum' (string): course number
                'courseTitle' (string): course title,
                'courseDes'(string): course description,
                'topicNum' (int): topic number (if applicable)
                'parentTitle' (string): parent topic title,
                'topicsList' (list): list of topics belonging to parent topic
                    topic_obj = {
                        'id' (int): course topic id
                        'topicNum' (int): topic number
                        'title' (string): course topic title
                    }
            }
        course (model instance): course specified by course id
        is_parent (boolean): signifies whether the course is a parent topic
    """
    # find course in database
    course = Course.query.filter_by(id=course_id).first()
    course_dept = course.dept
    topic_num = course.topic_num

    # decide if course is a topic course, and whether its a parent topic
    is_parent = False
    parent_id = None
    if(topic_num == -1):
        # course is not a topic course
        parent_title = None
        topics_list = None
    elif(topic_num == 0):
        # course is a topic course, and the parent topic
        is_parent = True
        parent_id = course.id
        parent_title = course.title
        topic = course.topic
        topics_list = []
        # get list of topics under the parent topic
        for course_topic in topic.courses:
            if (course_topic.topic_num == 0):
                continue
            topic_obj = {
                'id': course_topic.id,
                'topicNum': course_topic.topic_num,
                'title': course_topic.title
            }
            topics_list.append(topic_obj)
        if(len(topics_list) == 0):
            is_parent = False
    else:
        # course is a topic course, but not the parent topic
        topic = course.topic
        parent_title = ""
        topics_list = None
        
        # find the parent topic for the course
        for course_topic in topic.courses:
            if course_topic.topic_num == 0:
                parent_title = course_topic.title
                parent_id = course_topic.id
    
    # find median grade for the course
    median_grade = course_median_grade(course_dept.abr, course.num, topic_num, course.title)

    # return all course info information
    course_info = {
        'id': course.id,
        'courseDept': course_dept.abr,
        'courseNum': course.num,
        'courseTitle': course.title,
        'courseDes': course.description,
        'topicId': course.topic_id,
        'topicNum': topic_num,
        'parentId': parent_id,
        'parentTitle': parent_title,
        'topicsList': topics_list,
        'medianGrade': median_grade
    }

    return course_info, course, is_parent

def get_course_requisites(course):
    """
    Gets course requisite information

    Args:
        course (model instance): course

    Returns:
        course_requisites (object): contains course requisite information
            course_requisites = {
                'preReqs' (string): course prerequisites
                'restrictions' (string): course restrictions
            }
    """
    course_requisites = {
        'preReqs': course.pre_req,
        'restrictions': course.restrictions
    }

    return course_requisites

def get_ecis(course, prof):
    """
    Given a course and prof model instance, obtain the average ecis scores over all semesters

    Args:
        course (model instance): course instance,
        prof (model instance): prof instance
        
    Returns:
        course_ecis (float): Average course ecis score
        prof_ecis (float): Average prof ecis score
    """
    # get prof course model instance
    prof_course = ProfCourse.query.filter_by(course_id=course.id, prof_id=prof.id).first()

    # check if prof_course is None
    if prof_course is None:
        return None, None

    scores = []
    # get list of ecis scores for each semester for the prof/course combination
    for pcs in prof_course.prof_course_sem:
        for ecis in pcs.ecis:
            scores.append(ecis)

    if len(scores) == 0:
        course_ecis = None
        prof_ecis = None
    else:
        # calculate average prof/course ecis score for the prof/course combination
        total_students = 0
        course_ecis = 0
        prof_ecis = 0
        for ecis in scores:
            course_ecis += ecis.course_avg * ecis.num_students
            prof_ecis += ecis.prof_avg * ecis.num_students
            total_students += ecis.num_students
        course_ecis = round(course_ecis / total_students, 1)
        prof_ecis = round(prof_ecis / total_students, 1)

    return course_ecis, prof_ecis

def time_to_string(time_to_string):
    """
    Converts a number string representing a military time value to the corresponding
    time value with an AM/PM format

    Args:
        time_to_string (string): military time value (ex: 1230)

    Returns:
        time_string (string): AM/PM format of the time (ex: 12:30PM)
    """

    # check if arg is None
    if(time_to_string == None):
        return None

    # initialize string and get integer value from input
    time_string = ""
    time_num = int(time_to_string)
    
    if(time_num < 1200 and time_num >= 100):
        # 1:00AM to 11:59AM
        if(len(time_to_string) == 3):
            time_string = time_to_string[0:1] + ":" + time_to_string[1:3]
        else:
            time_string = time_to_string[0:2] + ":" + time_to_string[2:4]
        time_string += " AM"
    elif(time_num <= 0 and time_num < 100):
        # 12:00AM to 12:59AM
        time_string = "12" + ":" + time_to_string[1:3] + " AM"
    elif(time_num >= 1200 and time_num < 1300):
        # 12:00PM to 12:59PM
        time_string = "12" + ":" + time_to_string[2:4] + " PM"
    else:
        # 1:00PM to 11:59PM
        time_num = time_num - 1200
        time_to_string = str(time_num) 
        if(len(time_to_string) == 3):
            time_string = time_to_string[0:1] + ":" + time_to_string[1:3]
        else:
            time_string = time_to_string[0:2] + ":" + time_to_string[2:4]   
        time_string += " PM"

    return time_string

def get_scheduled_course(scheduled_course, is_parent):
    """
    Obtain information for the scheduled course

    Args:
        scheduled_course (model instance): scheduled course
        is_parent (boolean): true if course is a parent topic

    Returns:
        scheduled_obj (obj): Contains detailed information about the scheduled course
            scheduled_obj = {
                "id" (int): scheduled id,
                'uniqueNum' (int): scheduled course unique number
                'days' (string): days of the week course is taught
                'timeFrom' (string): starting time
                'timeTo' (string): ending time
                'location' (string): building and room number
                'maxEnrollment' (int): max enrollment
                'seatsTaken' (int): seats taken
                'profId' (int): professor id
                'profFirst' (string): professor first name
                'profLast' (string): professor last name
                'semester' (int): integer representation of semester
                'year' (int): year
                'crossListed' (list): list of cross listed courses
                    x_listed_obj = {
                        'id' (int): course id
                        'dept' (string): course deptartment abbreviation
                        'num' (string): course num
                        'title' (string): course title
                        'topicNum' (int): topic number
                    }
            }
    """
    # get prof and semester information
    prof = scheduled_course.prof
    semester_name = ""
    if(scheduled_course.semester.semester == 2):
        semester_name = "Spring"
    elif(scheduled_course.semester.semester == 6):
        semester_name = "Summer"
    elif(scheduled_course.semester.semester == 9):
        semester_name = "Fall"

    # obtain list of cross listed courses
    x_listed = []
    x_listed_ids = []
    x_listed_ids.append(scheduled_course.course.id)
    if(scheduled_course.xlist is not None):
        for x_course in scheduled_course.xlist.courses:
            if(x_course.course.id in x_listed_ids):
                continue
            if(is_parent and x_course.course.topic_num != 0):
                continue
            x_listed_ids.append(x_course.course.id)
            x_listed_obj = {
                'id': x_course.course.id,
                'dept': x_course.course.dept.abr,
                'num': x_course.course.num,
                'title': x_course.course.title,
                'topicNum': x_course.course.topic_num
            }
            x_listed.append(x_listed_obj)

    # return scheduled course information
    scheduled_obj = {
        "id": scheduled_course.id,
        'uniqueNum': scheduled_course.unique_no,
        'days': scheduled_course.days,
        'timeFrom': time_to_string(scheduled_course.time_from),
        'timeTo': time_to_string(scheduled_course.time_to),
        'location': scheduled_course.location,
        'maxEnrollment': scheduled_course.max_enrollement,
        'seatsTaken': scheduled_course.seats_taken,
        'profId': prof.id if prof is not None else None,
        'profFirst': prof.first_name if prof is not None else None,
        'profLast': prof.last_name if prof is not None else None,
        'crossListed': x_listed,
        'semester': semester_name,
        'year': scheduled_course.semester.year
    }

    return scheduled_obj

def get_course_schedule(course, is_parent):
    """
    Get course schedule information for the current and next semesters

    Args:
        course (model instance): course
        is_parent (boolean): signifies whether the course is a parent topic

    Returns:
        course_schedule (obj): course schedule information for most recent two semesters
        course_schedule = {
            "currentSem" (list): list of scheduled courses for the current semester
            "futureSem" (list): list of scheduled courses for the future semester
        }
    """
    # current and future semester, as labeled by FTP, update manually
    with open('semester.txt') as f:
        semesters = json.load(f)
        
    current_sem = {
        'year': int(semesters['current'][0:-1]) if semesters['current'] is not None else None,
        'sem': int(semesters['current'][-1]) if semesters['current'] is not None else None
    }

    future_sem_year = None
    future_sem_sem = None
    if(current_sem['year'] is not None):
        if(current_sem['sem'] == 9):
            future_sem_year = current_sem['year'] + 1
            future_sem_sem = 2
        elif(current_sem['sem'] == 2):
            future_sem_year = current_sem['year']
            future_sem_sem = 6
        elif(current_sem['sem'] == 6):
            future_sem_year = current_sem['year']
            future_sem_sem = 9

    future_sem = {
        'year': future_sem_year,
        'sem': future_sem_sem
    }

    # obtain list of scheduled courses for current and future semesters
    current_list = []
    future_list = []
    courses_scheduled_ids = []
    courses_scheduled = course.scheduled.copy()
    for i in range(len(course.scheduled)):
        courses_scheduled_ids.append(course.scheduled[i].id)
    
    # if course is a parent topic, get list of scheduled instances for children topics
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for topic_scheduled in topic_course.scheduled:
                if(topic_scheduled.id in courses_scheduled_ids):
                    continue
                courses_scheduled_ids.append(topic_scheduled.id)
                courses_scheduled.append(topic_scheduled)

    # for each scheduled course instance, get scheduled course information and append it to corresponding list
    for scheduled_course in courses_scheduled:
        scheduled_obj = get_scheduled_course(scheduled_course, is_parent)
        if(scheduled_course.semester.year == current_sem['year'] and
        scheduled_course.semester.semester == current_sem['sem']):
            current_list.append(scheduled_obj)
        elif(scheduled_course.semester.year == future_sem['year'] and
        scheduled_course.semester.semester == future_sem['sem']):
            future_list.append(scheduled_obj)

    if(current_sem['year'] == None):
        current_list = None
    if(future_sem['year'] == None):
        future_list = None
        
    course_schedule = {
        "currentSem": current_list,
        "futureSem": future_list
    }

    return course_schedule

def get_review_info(review, logged_in, curr_user):
    """
    Get review information for a particular review instance

    Args:
        review (model instance): review
        percentLiked (int): percent liked over all reviews
        usefulness (int): average usefulness over all reviews
        difficulty (int): average difficulty over all reviews
        workload (int): average workload over all reviews
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user

    Returns:
        review_object (object): Object containing detailed information about the review
            review_object = {
            'id' (int): review id
            'comments (string)': comments on the course
            'approval' (boolean): whether the user liked or disliked the course
            'usefulness' (int): usefulness rating
            'difficulty' (int): difficulty rating
            'workload' (int): workload rating
            'userMajor' (string): author's major
            'profilePic' (string): author's profile picture
            'profId' (int): prof id
            'profFirst' (string): prof first name
            'profLast' (string): prof last name
            'grade' (string): grade the user got in the course
            'numLiked' (int): number of likes the review has
            'numDisliked' (int): number of dislikes the review has
            'likePressed' (boolean): whether the current user liked the review
            'dislikePressed' (boolean): whether the current user disliked the review
            'date' (string): date the review was posted converted to string format: ("%Y-%m-%d"),
            'year' (int): year user took the course
            'semester' (string): string representation of semester
        }
    """
    
    # convert semester to string representation
    semester = review.semester.semester
    if(semester == 6):
        semester = "Summer"
    elif(semester == 9):
        semester = "Fall"
    elif(semester == 2):
        semester = "Spring"
    else:
        semester = "N/A"
    
    # get course review instance
    course_review = review.course_review[0]

    # get user and prof information
    user = review.author
    prof = review.prof_review[0].prof
    user_major = user.major
    profile_pic = user.pic

    num_liked = 0
    num_disliked = 0
    like_pressed = False
    dislike_pressed = False

    # calculate number of likes and determine if current user liked the review
    for like in course_review.users_liked:
        num_liked += 1
        if(logged_in):
            if(curr_user.id == like.user_id):
                like_pressed = True

    # calulcate number of dislikes and determine if current user disliked the review
    for dislike in course_review.users_disliked:
        num_disliked += 1
        if(logged_in):
            if(curr_user.id == dislike.user_id):
                dislike_pressed = True
    
    # if the review comment is empty, return None
    if(course_review.comments == ""):
        return None

    # return detailed review information
    review_object = {
        'id': course_review.id,
        'comments': course_review.comments,
        'approval': course_review.approval,
        'usefulness': course_review.usefulness,
        'difficulty': course_review.difficulty,
        'workload': course_review.workload,
        'userMajor': user_major.name if user_major != None else user.other_major,
        'profilePic': profile_pic.file_name,
        'profId': prof.id,
        'profFirst': prof.first_name,
        'profLast': prof.last_name,
        'numLiked': num_liked,
        'grade': review.grade,
        'numDisliked': num_disliked,
        'writtenByUser': user.email == curr_user.email if logged_in else False,
        'likePressed': like_pressed,
        'dislikePressed': dislike_pressed,
        'dateString': timeago.format(review.date_posted, datetime.datetime.utcnow()),
        'date': str(review.date_posted),
        'year': review.semester.year,
        'semester': semester
    }

    return review_object

def get_course_reviews(course, logged_in, curr_user, is_parent):
    """
    Get information for all reviews of the course

    Args:
        course (model instance): course
        logged_in (boolean): tells whether user is logged in
        curr_user (model instance): currently logged in user
        is_parent (boolean): whether course is a parent topic

    Returns:
        course_rating (object): average rating for the course in all categories
            course_rating = {
                'eCIS' (float): average course ecis score over all semesters
                'percentLiked' (float): percentage that liked the course
                'difficulty' (float): average difficulty
                'usefulness' (float): average usefulness
                'workload' (float): average workload
                'numRatings' (int): number of ratings
            }
        review_list (list): list of all reviews for the course
    """
    # obtain list of course reviews
    course_reviews_ids = []
    course_reviews = course.reviews
    for i in range(len(course.reviews)):
        course_reviews_ids.append(course.reviews[i].id)

    # if course is parent topic, obtain reviews from children topics
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for i in range(len(topic_course.reviews)):
                if(topic_course.reviews[i].id in course_reviews_ids):
                    continue
                course_reviews_ids.append(topic_course.reviews[i].id)
                course_reviews.append(topic_course.reviews[i])

    # iterate through all course reviews and add to review list
    review_list = []
    for course_review in course_reviews:
        review = course_review.review
        review_object = get_review_info(review, logged_in, curr_user)
        if review_object:
            review_list.append(review_object)

    # return course rating information
    course_rating = {
        'eCIS': round(course.ecis_avg, 1) if course.ecis_avg != None else None,
        'percentLiked': round(course.approval, 2) * 100 if course.approval != None else None,
        'difficulty': round(course.difficulty, 1) if course.difficulty != None else None,
        'usefulness': round(course.usefulness, 1) if course.usefulness != None else None,
        'workload': round(course.workload, 1) if course.workload != None else None,
        'numRatings': course.num_ratings
    }

    return course_rating, review_list

def get_course_profs(course, is_parent):
    """
    Gets information for all profs that teach the course

    Args:
        course (model instance): course
        is_parent (boolean): whether course is a parent topic

    Returns:
        prof_list (list): list of all professors that teach the course
            prof_obj = {
                'id' (int): prof id
                'firstName' (string): prof first name
                'lastName' (string): prof last name,
                'percentLiked' (int): percentage that liked the prof for the course
                'clear' (float): average clear rating
                'engaging' (float): average engaging rating
                'grading' (float): average grading rating
                'eCIS' (float): ecis prof score
            }
    """
    # obtain list of all profs that teach the course
    prof_list = []
    course_prof = course.prof_course
    course_prof_ids = []
    for i in range(len(course.prof_course)):
        course_prof_ids.append(course.prof_course[i].id)

    # if course is parent topic, obtain profs for all children topics
    if(is_parent):
        topic = course.topic
        for topic_course in topic.courses:
            for i in range(len(topic_course.prof_course)):
                if(topic_course.prof_course[i].id in course_prof_ids):
                    continue
                course_prof_ids.append(topic_course.prof_course[i].id)
                course_prof.append(topic_course.prof_course[i])
    
    # iterate through course prof instances and add to course prof list
    for prof_course in course_prof:

        prof = prof_course.prof
        course_ecis, prof_ecis = get_ecis(course, prof)

        prof_reviews = prof.reviews
        course_reviews = course.reviews
        review_ids = [course_review.review_id for course_review in course_reviews]
        reviews = []

        # iterate through all prof reviews and calculate average metrics
        for prof_review in prof_reviews:
            if(prof_review.review_id in review_ids):
                reviews.append(prof_review.review)

        # calculate average metrics       
        if(len(reviews) == 0):
            percentLiked = None
            clear = None
            engaging = None
            grading = None
        else:
            percentLiked = 0
            clear = 0
            engaging = 0
            grading = 0

            # iterate through all the reviews
            for review in reviews:
                prof_review = review.prof_review[0]
                if(prof_review.approval):
                    percentLiked += 1
                clear += prof_review.clear
                engaging += prof_review.engaging
                grading += prof_review.grading

            percentLiked = round(percentLiked/len(reviews), 2) * 100
            clear = round(clear/len(reviews), 1)
            engaging = round(engaging/len(reviews), 1)
            grading = round(grading/len(reviews), 1)

        # return object containing prof information
        prof_obj = {
            'id': prof.id,
            'firstName': prof.first_name,
            'lastName': prof.last_name,
            'percentLiked': percentLiked,
            'clear': clear,
            'engaging': engaging,
            'grading': grading,
            'eCIS': prof_ecis
        }
        prof_list.append(prof_obj)
    
    return prof_list

