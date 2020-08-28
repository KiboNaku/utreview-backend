
import re
import json

from string import ascii_lowercase
from titlecase import titlecase

from .add_to_database import (
	check_or_add_course,
	check_or_add_prof,
	check_or_add_scheduled_course,
	check_or_add_semester,
	check_or_add_prof_course,
	check_or_add_prof_course_semester,
	check_or_add_xlist
)
from .scheduled_course import ScheduledCourseInfo
from utreview import SPRING_SEM, SUMMER_SEM, FALL_SEM, sem_current, sem_next, sem_future
from utreview.models.course import *
from utreview.models.ecis import *
from utreview.models.others import *
from utreview.models.prof import *
from utreview.services.fetch_course_info import *
from utreview.services.fetch_ecis import *
from utreview.services.fetch_web import KEY_SEM, KEY_DEPT, KEY_CNUM, KEY_TITLE, KEY_UNIQUE, KEY_PROF
from utreview.services.logger import logger


def refresh_ecis():
	"""
	Set course and prof ecis_avg and ecis_students by iterating through ecis_scores
	"""

	logger.info("Refreshing course and professor ecis fields with respective data")
	query_tuple = (Course.query.all(), Prof.query.all())

	# will iterate between Course and Prof since code is identical
	for queries in query_tuple:
		for query in queries:

			if type(query) is Course:
				logger.debug(f"Refreshing ecis for Course: {query.dept} {query.num}")
			elif type(query) is Prof:
				logger.debug(f"Refreshing ecis for Prof: {query.first_name} {query.last_name}")

			ecis = 0
			students = 0

			# iterate through ecis scores specific to the course/prof
			for prof_course in query.prof_course:
				for prof_course_sem in prof_course.prof_course_sem:
					for ecis_child in prof_course_sem.ecis:
						ecis += ecis_child.course_avg * ecis_child.num_students
						students += ecis_child.num_students

			# average will be None if there are no students
			query.ecis_avg = (ecis / students) if students > 0 else None
			query.ecis_students = students
			db.session.commit()


def populate_ecis(file_path, pages):
	"""
	Populate database with ECIS information
	:param file_path: path to file containing data
	:type file_path: str
	:param pages: pages of file to parse
	:type pages: list[int] or list[str]
	"""

	# FOR FUTURE UPDATES, PLEASE READ:
	# remember to update Course and Prof ECIS fields when inputting new ECIS scores: ecis_avg and ecis_students

	logger.info(f'Populating ecis database with data from: {file_path}')
	ecis_lst = parse_ecis_excel(file_path, pages)

	for ecis in ecis_lst:

		# separate values from dictionary
		unique, c_avg, p_avg, students, yr, sem = (
			ecis[KEY_UNIQUE_NUM],
			ecis[KEY_COURSE_AVG],
			ecis[KEY_PROF_AVG],
			ecis[KEY_NUM_STUDENTS],
			ecis[KEY_YR],
			ecis[KEY_SEMESTER]
		)

		# check for existence of specified Semester, ProfCourseSemester in database
		logger.debug(f'Adding ecis for: unique={unique}, sem={yr}{sem}')
		sem_obj = Semester.query.filter_by(year=yr, semester=sem).first()
		if sem_obj is None:
			logger.debug(f"Cannot find semester for: {yr}{sem}. Skipping...")
			continue

		pcs_obj = ProfCourseSemester.query.filter_by(unique_num=unique, sem_id=sem_obj.id).first()
		if pcs_obj is None:
			logger.debug(
				f"Failed to find ProfCourseSemester for: unique={unique}, sem={yr}{sem}. Skipping..."
			)
			continue

		# assumption: only one ecis score per prof_course_semester instance -> else skip
		ecis_lst = pcs_obj.ecis
		if len(ecis_lst) >= 1:
			# ecis already exists
			continue

		# creating the ecis object
		ecis_obj = EcisScore(
			course_avg=c_avg,
			prof_avg=p_avg,
			num_students=students,
			prof_course_sem_id=pcs_obj.id)
		db.session.add(ecis_obj)
		db.session.commit()

		# updating course and prof ecis fields
		logger.debug("Updating prof and course ecis fields")
		pc_obj = pcs_obj.prof_course
		course_obj = pc_obj.course
		prof_obj = pc_obj.prof

		queries = ((course_obj, c_avg), (prof_obj, p_avg))
		for query, avg in queries:
			total_students = query.ecis_students + students
			total_avg = ((query.ecis_avg * query.ecis_students) if query.ecis_avg is not None else 0) + \
				((avg * students) if avg is not None else 0)
			query.ecis_avg = (total_avg / total_students) if total_students > 0 else None
			query.ecis_students = total_students

		db.session.commit()


def populate_sem(start_yr=2010, end_yr=2020):
	"""
	Populate database with semesters for the given year range. Will populate for spring, summer, fall semesters.
	:param start_yr: starting year for the populate
	:type start_yr: int
	:param end_yr: ending year for the populate
	:type end_yr: int
	"""

	logger.info(f"Populating database with semesters from {start_yr} to {end_yr}")
	for yr in range(start_yr, end_yr):
		for sem in (2, 6, 9):
			if Semester.query.filter_by(year=yr, semester=sem).first() is not None:
				check_or_add_semester(yr, sem)


def populate_prof_course(in_file):
	"""
	Populate database with Professor and Course relationship using data fetched from the web
	(utreview.services.fetch_web.fetch_prof_course_info only)
	:param in_file: file the data was fetched to
	:type in_file: str
	"""

	__sem_fall = "Fall"
	__sem_spring = "Spring"
	__sem_summer = "Summer"

	logger.info(f"Populating database with prof_course info using {in_file}")

	# creating list of prof-course relationships from the given file
	prof_courses = []
	with open(in_file, 'r') as f:
		for line in f:
			prof_courses.append(json.loads(line))
	cur_profs = Prof.query.all()

	# add each prof-course relationship to the database if appropriate
	for prof_course in prof_courses:

		# check for existence of professor -> add if does not exist
		prof_name = [name.strip() for name in prof_course[KEY_PROF].lower().split(",")]
		last, first = prof_name[0].strip(), prof_name[1].strip()
		last_words = [word.strip() for word in last.split(' ') if len(word.strip()) > 0]
		first_words = [word.strip() for word in first.split(' ') if len(word.strip()) > 0]

  
		target_prof = None
		for cur_prof in cur_profs:
			found = True

			cur_last, cur_first = cur_prof.last_name.lower(), cur_prof.first_name.lower()
			cur_last_words = [word.strip() for word in cur_last.split(' ') if len(word.strip()) > 0]
			cur_first_words = [word.strip() for word in cur_first.split(' ') if len(word.strip()) > 0]

			for word in last_words:
				if word not in cur_last_words:
					found = False
					break
			
			if found:
				for word in first_words:
					if word not in cur_first_words:
						found = False
						break
			
			if found:
				target_prof = cur_prof
				break
		
		if target_prof is None:
			logger.debug(f"Cannot find prof: {prof_course[KEY_PROF]}. Skipping...")
			continue
  
		# check for existence of department -> skip if does not exist
		abr = prof_course[KEY_DEPT].strip().upper()
		dept = Dept.query.filter_by(abr=abr).first()
		if dept is None:
			logger.debug(f"Cannot find dept: {abr}. Skipping...")
			continue

		# check if course exists -> add if does not exist
		# TODO: choosing topic 0 by default. Update when topic info available.
		num_results, course = check_or_add_course(dept, prof_course[KEY_CNUM], prof_course[KEY_TITLE])
		if num_results > 1:
			courses = Course.query.filter_by(dept_id=dept.id, num=prof_course[KEY_CNUM])
			for c in courses:
				if c.topic_num <= 0:
					course = c
		db.session.commit()
  
		# check if prof_course exists -> add if it doesn't
		_, prof_course_obj = check_or_add_prof_course(target_prof, course)
		db.session.commit()

		# parse semester to integer representation
		sem_lst = [s.strip() for s in prof_course[KEY_SEM].split(",")]
		if sem_lst[1] == __sem_spring:
			sem = SPRING_SEM
		elif sem_lst[1] == __sem_summer:
			sem = SUMMER_SEM
		elif sem_lst[1] == __sem_fall:
			sem = FALL_SEM
		else:
			logger.debug(f"Invalid semester: {sem_lst[1]}. Skipping...")
			continue

		yr = int(sem_lst[0].strip())

		# check for semester existence -> if it doesn't, add to database
		_, sem_obj = check_or_add_semester(yr, sem)

		# check for prof_course_semester existence -> if it doesn't add to database
		check_or_add_prof_course_semester(prof_course[KEY_UNIQUE], prof_course_obj, sem_obj)
		db.session.commit()


def populate_prof_eid(profs):
	# profs must be sorted in order of semester
	# NOTE: professors sometimes have different names by semester -> take most recent (check by eid)]

	cur_profs = Prof.query.all()

	for semester, name, eid in profs:
		
		if ',' not in name:
			logger.debug(f'Invalid prof name: {name}')
			continue
		
		name = name.lower()
		name = name.split(',')
		last, first = name[0].strip(), name[1].strip()
		last_words = [word.strip() for word in last.split(' ') if len(word.strip()) > 0]
		first_words = [word.strip() for word in first.split(' ') if len(word.strip()) > 0]

		# check if professor exists by eid
		target_prof = Prof.query.filter_by(eid=eid).first()

		# if None then check by name matching		
		if target_prof is None:
			for cur_prof in cur_profs:
				found = True

				cur_last, cur_first = cur_prof.last_name.lower(), cur_prof.first_name.lower()
				cur_last_words = [word.strip() for word in cur_last.split(' ') if len(word.strip()) > 0]
				cur_first_words = [word.strip() for word in cur_first.split(' ') if len(word.strip()) > 0]

				for word in cur_last_words:
					if word not in last_words:
						found = False
						break
				
				if found:
					for word in cur_first_words:
						if word not in first_words:
							found = False
							break
				
				if found:
					target_prof = cur_prof
					break

		first = first.title()
		last = last.title()

		if target_prof is None:
			logger.debug(f'Adding new prof: {first} {last}')
			new_prof = Prof(first_name=first, last_name=last, eid=eid)
			db.session.add(new_prof)
		else: 
			logger.debug(f'Updating prof: {target_prof.first_name} {target_prof.last_name} -> {first} {last}')
			target_prof.first_name = first
			target_prof.last_name = last
			target_prof.eid = eid

		db.session.commit()


def populate_dept(dept_info, override=False):
	"""
	Populate the database with departments
	:param dept_info: list of tuples with: (abbreviation, name)
	:type dept_info: tuple(str, str)
	:param override: override current department with same abbreviation if found in database
	:type override: bool
	"""

	logger.info("Populating database with departments")
	for abr, name in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:
			# add department to database
			abr = abr.strip()
			name = name.strip()

			logger.debug(f"Adding dept {name} ({abr}) to database")
			dept = Dept(abr=abr, name=name)
			db.session.add(dept)

		elif override:
			# override current department
			logger.debug(f"Overriding dept {name} ({abr}) to database")
			cur_dept.abr = abr
			cur_dept.name = name

		else:
			# department already exists and not overriding
			logger.debug(f"Already exists: dept {name} ({abr})")

		db.session.commit()


def populate_dept_info(dept_info):
	"""
	Populate department with additional information (college and department name)
	:param dept_info: list of tuples containing: (abbreviation, department name, college name)
	:type dept_info: list[tuple(str, str, str)
	"""
	logger.info('Populating departments with additional info')

	for abr, dept, college in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:
			logger.debug(f"Cannot find dept {abr}")
		else:
			logger.debug(f"Updating dept: {abr} with dept={dept}, college={college}")
			cur_dept.dept = dept
			cur_dept.college = college

		db.session.commit()


def reset_scheduled_info():
	logger.info("Resetting scheduled info")
	for scheduled_course in ScheduledCourse.query.all():
		scheduled_course.mark_deletion = False
		db.session.commit()


def refresh_review_info():
	"""
	Refresh course and prof review metric fields
	For Course: approval, difficulty, usefulness, workload
	For Prof: approval, clear, engaging, grading
	"""

	query_lst = (Course.query.all(), Prof.query.all())
	for queries in query_lst:
		for query in queries:

			if type(query) is Course:
				logger.debug(f"Refreshing review fields for Course: {query.dept} {query.num}")
			elif type(query) is Prof:
				logger.debug(f"Refreshing review fields for Prof: {query.first_name} {query.last_name}")

			# initiate variables
			query.num_ratings = len(query.reviews)
			approval = 0
			metrics = [0, 0, 0]

			# iterate through reviews and update metric values
			for review in query.reviews:
				approval += int(review.approval)
				if type(query) is Course:
					metrics[0] += review.difficulty
					metrics[1] += review.usefulness
					metrics[2] += review.workload
				elif type(query) is Prof:
					metrics[0] += review.clear
					metrics[1] += review.engaging
					metrics[2] += review.grading

			# do final metric calculation (averages)
			query.approval = approval / query.num_ratings if query.num_ratings > 0 else None
			metrics[0] = metrics[0] / query.num_ratings if query.num_ratings > 0 else None
			metrics[1] = metrics[1] / query.num_ratings if query.num_ratings > 0 else None
			metrics[2] = metrics[2] / query.num_ratings if query.num_ratings > 0 else None

			# update query based on type
			if type(query) is Course:
				query.difficulty = metrics[0]
				query.usefulness = metrics[1]
				query.workload = metrics[2]
			elif type(query) is Prof:
				query.difficulty = metrics[0]
				query.usefulness = metrics[1]
				query.workload = metrics[2]

			db.session.commit()


def populate_scheduled_course(course_info):
	"""
	Populate the database with scheduled course info as parsed from FTP
	:param course_info: list of course data
	:type course_info: list[dict]
	"""

	logger.info("Populating database with scheduled course info")
	s_course_queue = []

	for s_course in course_info:

		# create ScheduledCourseInfo object using the s_course dictionary
		try:
			scheduled = ScheduledCourseInfo(s_course)
		except ValueError as err:
			logger.warn(f"Populate scheduled course error: {err}. Skipping...")
			continue

		# check to see if dept exists
		dept_obj = Dept.query.filter_by(abr=scheduled.dept).first()
		if dept_obj is None:
			logger.debug(f"Populate scheduled course: cannot find department {scheduled.dept}. Skipping...")
			continue

		# check to see if course exists
		cur_courses = Course.query.filter_by(dept_id=dept_obj.id, num=scheduled.c_num)
		if len(cur_courses.all()) > 1:
			cur_courses = cur_courses.filter_by(topic_num=scheduled.topic)
		cur_course = cur_courses.first()

		if cur_course is None:
			course_log_description = f"{scheduled.dept} {scheduled.c_num} w/ topic num {scheduled.topic}"
			logger.debug(f"Populate scheduled course: cannot find course {course_log_description}. Skipping...")
			continue

		# check to see if prof exists --> if not then leave empty
		cur_prof = Prof.query.filter_by(eid=scheduled.prof_eid).first()

		if cur_prof is None:
			logger.warn(f"Could not find professor w/ EID={scheduled.prof_eid}. Leaving empty...")

		# check to see if semester exists else add semester
		_, semester = check_or_add_semester(yr=scheduled.yr, sem=scheduled.sem)

		# check to see if scheduled course exists else create new
		num_results, cur_schedule = check_or_add_scheduled_course(scheduled, cur_course, cur_prof, None, semester, add=False)
		if num_results > 0:
			logger.debug(f"""Updating scheduled course. Unique = {scheduled.unique_no}
					semester={repr(semester)}
					course={repr(cur_course)}
					prof={repr(cur_prof)}""")
			cur_schedule = scheduled.to_scheduled_course(cur_schedule, semester, cur_course, cur_prof, None)
		
		s_course_queue.append({
			'scheduled': cur_schedule,
			'prof': cur_prof,
			'course': cur_course,
			'semester': semester, 
			'unique': scheduled.unique_no,
			'xlist': scheduled.x_listings,
		})
	update_scheduled_courses(s_course_queue)	


def update_scheduled_courses(s_course_queue):

	logger.info("Updating scheduled course information")
	semesters = {
		'current': {
			'courses': {},
			'profs': {}
		},
		'next': {
			'courses': {},
			'profs': {}
		},
		'future': {
			'courses': {},
			'profs': {}
		}
	}
	cur_s_courses = ScheduledCourse.query.all()

	for i in range(min(len(cur_s_courses), len(s_course_queue))):

		cur_s_course = cur_s_courses[i]
		s_course = s_course_queue[i]

		cur_schedule = s_course['scheduled']
		cur_prof = s_course['prof']
		cur_course = s_course['course']
		semester = s_course['semester']
		unique_no = s_course['unique']
		xlist_str = s_course['xlist']
		
		# check to see if cross_listings exist else create new
		x_list = check_or_add_xlist(xlist_str, semester)

		update_scheduled_course(cur_s_course, cur_schedule, x_list)
		db.session.commit()

		# add prof course and prof course semester relationship if doesnt exist
		if cur_prof:
			_, prof_course = check_or_add_prof_course(cur_prof, cur_course)
			check_or_add_prof_course_semester(unique_no, prof_course, semester)	

		# update course and prof semester fields (whether they are teaching the respective semesters)
		full_semester = int(str(semester.year) + str(semester.semester))

		if full_semester == sem_current:
			if cur_course:
				semesters['current']['courses'][cur_course.id] = True
			if cur_prof:
				semesters['current']['profs'][cur_prof.id] = True
		elif full_semester == sem_next:
			if cur_course:
				semesters['next']['courses'][cur_course.id] = True
			if cur_prof:
				semesters['next']['profs'][cur_prof.id] = True
		elif full_semester == sem_future:
			if cur_course:
				semesters['future']['courses'][cur_course.id] = True
			if cur_prof:
				semesters['future']['profs'][cur_prof.id] = True

	logger.info("Checking scheduled data for uneven sizings")
	if len(s_course_queue) > len(cur_s_courses):
		logger.info("Have additional new schedueled courses")
		for s_course in s_course_queue[len(cur_s_courses):]:

			cur_schedule = s_course['scheduled']
			cur_prof = s_course['prof']
			cur_course = s_course['course']
			semester = s_course['semester']
			unique_no = s_course['unique']
			xlist_str = s_course['xlist']
		
			# check to see if cross_listings exist else create new
			x_list = check_or_add_xlist(xlist_str, semester)
			cur_schedule.cross_listed = x_list.id

			db.session.add(cur_schedule)
			db.session.commit()

			# add prof course and prof course semester relationship if doesnt exist
			if cur_prof:
				_, prof_course = check_or_add_prof_course(cur_prof, cur_course)
				check_or_add_prof_course_semester(unique_no, prof_course, semester)	

			# update course and prof semester fields (whether they are teaching the respective semesters)
			full_semester = int(str(semester.year) + str(semester.semester))

			if full_semester == sem_current:
				if cur_course:
					semesters['current']['courses'][cur_course.id] = True
				if cur_prof:
					semesters['current']['profs'][cur_prof.id] = True
			elif full_semester == sem_next:
				if cur_course:
					semesters['next']['courses'][cur_course.id] = True
				if cur_prof:
					semesters['next']['profs'][cur_prof.id] = True
			elif full_semester == sem_future:
				if cur_course:
					semesters['future']['courses'][cur_course.id] = True
				if cur_prof:
					semesters['future']['profs'][cur_prof.id] = True
	
	for s_course in ScheduledCourse.query.all():
		if s_course.mark_deletion is not None:
			s_course.mark_deletion = True
			db.session.commit()

	logger.info("Updating course and professor semesters")
	all_profs = Prof.query.all()
	all_courses = Course.query.all()

	for prof in all_profs:
		if (
			(prof.current_sem != semesters['current']['profs'].get(prof.id, False)) or 
			(prof.next_sem != semesters['next']['profs'].get(prof.id, False)) or 
			(prof.future_sem != semesters['future']['profs'].get(prof.id, False))
		):
			prof.current_sem = semesters['current']['profs'].get(prof.id, False)
			prof.next_sem = semesters['next']['profs'].get(prof.id, False)
			prof.future_sem = semesters['future']['profs'].get(prof.id, False)
			db.session.commit()

	for course in all_courses:
		if (
			(course.current_sem != semesters['current']['courses'].get(course.id, False)) or
			(course.next_sem != semesters['next']['courses'].get(course.id, False)) or 
			(course.future_sem != semesters['future']['courses'].get(course.id, False))
		):
			course.current_sem = semesters['current']['courses'].get(course.id, False)
			course.next_sem = semesters['next']['courses'].get(course.id, False)
			course.future_sem = semesters['future']['courses'].get(course.id, False)
			db.session.commit()


def update_scheduled_course(old, new, x_list):

	old.unique_no = new.unique_no
	old.session = new.session

	old.days = new.days
	old.time_from = new.time_from
	old.time_to = new.time_to
	old.location = new.location
	old.max_enrollement = new.max_enrollement
	old.seats_taken = new.seats_taken

	old.mark_deletion = None

	old.sem_id = new.sem_id
	old.course_id = new.course_id
	old.prof_id = new.prof_id
	old.cross_listed = x_list.id


def populate_prof(prof_info):
	"""
	Populate database with a professor using data fetched from the web
	:param prof_info: data fetched using fetch_prof from utreview.services.fetch_web
	:type prof_info: list
	"""

	if prof_info is not None and len(prof_info) > 1:

		first_name, last_name = __parse_prof_name(prof_info[0])
		eid = prof_info[1]

		cur_prof = Prof.query.filter_by(first_name=first_name, last_name=last_name, eid=eid).first()
		if cur_prof is None:
			logger.debug(f"Adding professor {first_name} {last_name}")
			prof = Prof(first_name=first_name, last_name=last_name, eid=eid)
			db.session.add(prof)
			db.session.commit()
		else:
			logger.debug(f"Professor {first_name} {last_name} already exists")
	else:
		logger.debug(f"Invalid input to populate_prof: {prof_info}")


def populate_course(course_info, cur_sem=None):
	"""
	Populate database with courses
	:param course_info: list of dictionaries containing course data
	:type course_info: list[dict]
	:param cur_sem: the current semester. if set to None, data will be replaced with most recent value
	:type cur_sem: int or None
	"""

	__inherit = "(See Base Topic for inherited information.)"
	null_depts = set()

	logger.info("Populating database with courses")

	for course in course_info:

		# fetch values from dictionary
		semester = course[KEY_SEM]
		dept = course[KEY_DEPT]
		num = course[KEY_NUM]
		title = course[KEY_TITLE]
		cs_title = course[KEY_CS_TITLE]
		description = course[KEY_DESCRIPTION]
		restrictions = course[KEY_RESTRICTION]
		t_num = course[KEY_TOPIC_NUM]
		pre_req = course[KEY_PRE_REQ]

		# check to see if dept exists --> else ski[
		dept_obj = Dept.query.filter_by(abr=dept).first()

		if dept_obj is None:
			null_depts.add(dept)
			continue

		# if topic number > 0, then title = modified cs title
		if t_num > 0:
			cs_title = __parse_title(cs_title)
			title = title if cs_title is None else cs_title

		# None if course doesn't currently exist
		old_course = None
		# define new base course variable
		new_course = Course(
			num=num,
			title=title,
			description=description,
			restrictions=restrictions,
			pre_req=pre_req,
			dept_id=dept_obj.id,
			topic_num=t_num
		)

		# condition on topic number
		if t_num >= 0:

			# all courses with same topic number --> should be unique topics
			# if len 0 --> new topic
			topic_courses_flask = Course.query.filter_by(dept_id=dept_obj.id, num=num)
			topic_courses = topic_courses_flask.all()

			# set topic number --> will create new topic if doesnt exist
			new_course.topic_id = __check_new_topic(topic_courses_flask)

			# assumption: unique based on topic number
			t_course_flask = topic_courses_flask.filter_by(topic_num=t_num)

			if t_num == 0:

				if len(t_course_flask.all()) > 0:
					old_course = t_course_flask.first()

				__populate_child_topics(new_course, topic_courses, __inherit)
			else:

				topic_zero = __get_topic_zero(topic_courses)

				if len(t_course_flask.all()) > 0:
					old_course = t_course_flask.first()

				__populate_child_topics(topic_zero, [new_course], __inherit)

		else:
			# course doesn't have topic number
			old_course = Course.query.filter_by(dept_id=dept_obj.id, num=num).first()

		# create new or replace old
		if old_course is None:
			# new course
			logger.debug(f"Creating new course {dept_obj.abr} {new_course.num}")
			db.session.add(new_course)
		elif cur_sem is None or semester == cur_sem:
			# course existed but replacing
			logger.debug(f"Replacing previous {old_course.dept.abr} {old_course.num}")
			__replace_course(old_course, new_course)
		else:
			# course existed and skipping
			logger.debug(f"Already existed: {old_course.dept.abr} {old_course.num}")

		db.session.commit()

	null_depts = list(null_depts)
	null_depts.sort()
	for dept in null_depts:
		logger.debug(f"Unexpected Error: department {dept} cannot be found in the database")


def __parse_title(cs_title):
	"""
	Parse title from raw input title with titlecase
	:param cs_title: raw cs title
	:type cs_title: str
	:return: parsed title string
	:rtype: str
	"""
	m = re.search(r"^\d+-(.*)", cs_title)

	if m is None:
		return None

	title_words = titlecase(m.group(1)).split()
	return ' '.join([word.upper() if __is_all_one_letter(word) else word for word in title_words])


def __is_all_one_letter(word):
	"""
	checks whether string is all one character
	:param word: word to check
	:type word: str
	:return: whether the string is all one character
	:rtype: bool
	"""
	word = word.lower()
	for c in ascii_lowercase:
		if word == c * len(word):
			return True
	return False


def __populate_child_topics(parent_topic, child_topics, inherit_str):
	"""
	Populate child topics with parent topic info
	:param parent_topic: parent topic object
	:type parent_topic: Course
	:param child_topics: child topic object
	:type child_topics: list[Course]
	:param inherit_str: string that marks an inherit-zone
	:type inherit_str: str
	"""
	for topic in child_topics:

		topic.description = topic.description.replace(inherit_str, parent_topic.description).strip()
		topic.restrictions = topic.restrictions.replace(inherit_str, parent_topic.restrictions).strip()
		topic.pre_req = topic.pre_req.replace(inherit_str, parent_topic.pre_req).strip()


def __check_new_topic(topic_courses_flask):
	"""
	Get topic if exists else create new topic
	:param topic_courses_flask: object containing topic courses
	"""
	if len(topic_courses_flask.all()) > 0:
		topic = topic_courses_flask.first().topic
	else:
		topic = Topic()
		db.session.add(topic)
		db.session.commit()

	return topic.id


def __replace_course(old_course, new_course):
	"""
	Update course info with new course info
	:param old_course: old course to replace
	:type old_course: Course
	:param new_course: new course with new course info
	:type new_course: Course
	"""
	old_course.title = new_course.title
	old_course.description = new_course.description
	old_course.restrictions = new_course.restrictions
	old_course.pre_req = new_course.pre_req
	old_course.topic_num = new_course.topic_num


def __get_topic_zero(topic_courses):
	"""
	Retrieve topic zero from list if exists else return None
	:param topic_courses: list of topic courses to iterate through
	:type topic_courses: list[Course]
	:return: topic course whose topic number is 0
	:rtype: Course or None
	"""
	for topic_course in topic_courses:
		if topic_course.topic_num == 0:
			return topic_course
	return None


def __parse_prof_name(name):
	"""
	Parse professor name from last_name, first_name format
	:param name: name to parse
	:type name: str
	:return: name split first_name, last_name
	:rtype: tuple(str, str)
	"""
	name_parts = name.split(',')[0].split()
	if len(name_parts) > 1:
		return name_parts[0], ' '.join(name_parts[1:])
	return '', name
