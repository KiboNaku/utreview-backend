
import re
import json

from string import ascii_lowercase
from titlecase import titlecase

from .scheduled_course import ScheduledCourseInfo
from utreview import logger, sem_current, sem_next, sem_future
from utreview.models.course import *
from utreview.models.ecis import *
from utreview.models.others import *
from utreview.models.prof import *
from utreview.services.fetch_course_info import *
from utreview.services.fetch_ecis import *


def refresh_ecis():
	"""
	Set course and prof ecis_avg and ecis_students by iterating through ecis_scores
	"""

	logger.info("Refreshing course and professor ecis fields with respective data")
	query_tuple = (Course.query.all(), Prof.query.all())

	for queries in query_tuple:
		for query in queries:
			ecis = 0
			students = 0
			for prof_course in query.prof_course:
				for prof_course_sem in prof_course.prof_course_sem:
					for ecis_child in prof_course_sem.ecis:
						ecis += ecis_child.course_avg * ecis_child.num_students
						students += ecis_child.num_students

			if students > 0:
				query.ecis_avg = ecis / students
			query.ecis_students = students
			db.session.commit()


def populate_ecis(file_path, pages):
	"""
	Populate database with ECIS information
	:param file_path: path to file containing data
	:type file_path: str
	:param pages: pages of file to parse
	:type pages: list[str]
	"""

	# remember to update Course and Prof ECIS fields when inputting new ECIS scores: ecis_avg and ecis_students

	logger.info(f'Populating ecis database with data from: {file_path}')
	ecis_lst = parse_ecis_excel(file_path, pages)

	for ecis in ecis_lst:

		unique, c_avg, p_avg, students, yr, sem = (
			ecis[KEY_UNIQUE_NUM],
			ecis[KEY_COURSE_AVG],
			ecis[KEY_PROF_AVG],
			ecis[KEY_NUM_STUDENTS],
			ecis[KEY_YR],
			ecis[KEY_SEM]
		)

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

		# assumption: only one ecis score per prof_course_semester instance
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

	for yr in range(start_yr, end_yr):
		for sem in (2, 6, 9):
			if Semester.query.filter_by(year=yr, semester=sem).first() is not None:
				semester = Semester(year=yr, semester=sem)
				db.session.add(semester)
	
	db.session.commit()


def populate_prof_course(in_file):

	from utreview.services.fetch_web import KEY_SEM, KEY_DEPT, KEY_CNUM, KEY_TITLE, KEY_UNIQUE, KEY_PROF
	__sem_fall = "Fall"
	__sem_spring = "Spring"
	__sem_summer = "Summer"

	prof_courses = []
	with open(in_file, 'r') as f:
		for line in f:
			prof_courses.append(json.loads(line))

	for prof_course in prof_courses:

		prof_name = [name.strip() for name in prof_course[KEY_PROF].split(",")]
		prof = Prof.query.filter_by(first_name=prof_name[1], last_name=prof_name[0]).first()

		if prof is None:
			# print("Adding new prof:", prof_course[KEY_PROF])
			prof = Prof(first_name=prof_name[1], last_name=prof_name[0])
			db.session.add(prof)
			db.session.commit()
		
		abr = prof_course[KEY_DEPT].strip().upper()
		dept = Dept.query.filter_by(abr=abr).first()
		if dept is None:
			# print("Cannot find dept:", abr, ". Skipping...")
			continue

		# TODO: choosing topic 0 by default. Update when topic info available.
		course = Course.query.filter_by(dept_id=dept.id, num=prof_course[KEY_CNUM])
		if len(course.all()) < 1:
			# print('Adding new course:', abr, prof_course[KEY_CNUM], prof_course[KEY_TITLE])
			course = Course(dept_id=dept.id, num=prof_course[KEY_CNUM], title=prof_course[KEY_TITLE])
			db.session.add(course)
			db.session.commit()
		elif len(course.all()) > 1:
			for c in course:
				if c.topic_num <= 0:
					course = c
		else:
			course = course.first()

		prof_course_obj = ProfCourse.query.filter_by(prof_id=prof.id, course_id=course.id).first()
		if prof_course_obj is None:
			prof_course_obj = ProfCourse(prof_id=prof.id, course_id=course.id)
			db.session.add(prof_course_obj)
			db.session.commit()
		
		sem_lst = [s.strip() for s in prof_course[KEY_SEM].split(",")]
		if sem_lst[1] == __sem_spring:
			sem = 2
		elif sem_lst[1] == __sem_summer:
			sem = 6
		elif sem_lst[1] == __sem_fall:
			sem = 9
		else:
			# print("Invalid semester:", sem_lst[1], ". Skipping...")
			continue
		
		yr = int(sem_lst[0].strip())

		sem_obj = Semester.query.filter_by(year=yr, semester=sem).first()
		if sem_obj is None:
			sem_obj = Semester(year=yr, semester=sem)
			db.session.add(sem_obj)
			db.session.commit()

		prof_course_sem_obj = ProfCourseSemester.query.filter_by(
			unique_num=prof_course[KEY_UNIQUE], prof_course_id=prof_course_obj.id, 
			sem_id = sem_obj.id
		).first()

		if prof_course_sem_obj is None: 
			prof_course_sem_obj = ProfCourseSemester(
				unique_num=prof_course[KEY_UNIQUE], prof_course_id=prof_course_obj.id, 
				sem_id = sem_obj.id
			)
			db.session.add(prof_course_sem_obj)
			db.session.commit()
	


def populate_dept(dept_info, override=False):

	for abr, name in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:

			abr = abr.strip()
			name = name.strip()
			
			# print(f"Adding dept {name} ({abr}) to database")
			dept = Dept(abr=abr, name=name)
			db.session.add(dept)

		elif override:
			# print(f"Overriding dept {name} ({abr}) to database")
			cur_dept.abr = abr
			cur_dept.name = name

		# else:
			# print(f"Already exists: dept {name} ({abr})")
		
		db.session.commit()


def populate_dept_info(dept_info):
	
	# print('Populating departments with additional info')
	
	for abr, dept, college in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:
			# print(f"Cannot find dept {abr} --> adding as non-major")
			cur_dept = Dept(abr=abr, dept=dept, college=college, name='')
			db.session.add(cur_dept)

		else:
			# print(f"Updating dept: {abr}")
			cur_dept.dept = dept
			cur_dept.college = college
		
		db.session.commit()


def reset_scheduled_info():

	ScheduledCourse.query.delete()
	query_lst = (Course.query.all(), Prof.query.all())
	for queries in query_lst:
		for query in queries:
			query.current_sem = False
			query.next_sem = False
			query.future_sem = False
		db.session.commit()


def refresh_review_info():

	courses = Course.query.all()
	for course in courses:
		course.num_ratings = len(course.reviews)
		approval = 0
		difficulty = 0
		usefulness = 0
		workload = 0
		for review in course.reviews:
			approval += int(review.approval)
			difficulty += review.difficulty
			usefulness += review.usefulness
			workload += review.workload
		course.approval = approval / course.num_ratings if course.num_ratings > 0 else None
		course.difficulty = difficulty / course.num_ratings if course.num_ratings > 0 else None
		course.usefulness = usefulness / course.num_ratings if course.num_ratings > 0 else None
		course.workload = workload / course.num_ratings if course.num_ratings > 0 else None
		db.session.commit()

	profs = Prof.query.all()
	for prof in profs:
		prof.num_ratings = len(prof.reviews)
		approval = 0
		clear = 0
		engaging = 0
		grading = 0
		for review in prof.reviews:
			approval += int(review.approval)
			clear += review.clear
			engaging += review.engaging
			grading += review.grading
		prof.approval = approval / prof.num_ratings if prof.num_ratings > 0 else None
		prof.difficulty = clear / prof.num_ratings if prof.num_ratings > 0 else None
		prof.usefulness = engaging / prof.num_ratings if prof.num_ratings > 0 else None
		prof.workload = grading / prof.num_ratings if prof.num_ratings > 0 else None
		db.session.commit()

	db.session.commit()


def populate_scheduled_course(course_info):

	# print("Populate scheduled course: resetting professor and course semesters")
	# print("Populate scheduled course: finished resetting professor and course semesters")
	
	for s_course in course_info:

		try:
			scheduled = ScheduledCourseInfo(s_course)
		except ValueError as err:
			# print(f"Populate scheduled course error: {err}. Skipping...")
			continue


		# check to see if dept exists
		dept_obj = Dept.query.filter_by(abr=scheduled.dept).first()
		if dept_obj is None:
			# print(f"Populate scheduled course: cannot find department {scheduled.dept}. Skipping...")
			continue

		# check to see if course exists
		cur_courses = Course.query.filter_by(dept_id=dept_obj.id, num=scheduled.c_num)
		if len(cur_courses.all()) > 1:
			cur_courses = cur_courses.filter_by(topic_num=scheduled.topic)
		cur_course = cur_courses.first()

		if cur_course is None:
			# print(f"Populate scheduled course: cannot find course {scheduled.dept} {scheduled.c_num} w/ topic num {scheduled.topic}. Skipping...")
			continue

		# check to see if prof exists --> if not then add prof
		cur_prof = Prof.query.filter_by(eid=scheduled.prof_eid).first()
		
		if cur_prof is None and scheduled.prof_eid:
			# populate_prof(fetch_prof(scheduled.prof_eid))
			cur_prof = Prof.query.filter_by(eid=scheduled.prof_eid).first()
			# if cur_prof is None:
				# print("Failed to add professor. Leaving empty...")

		# check to see if semester exists else add semester
		semester = Semester.query.filter_by(year=scheduled.yr, semester=scheduled.sem).first()
		if semester is None:
			semester = Semester(year=scheduled.yr, semester=scheduled.sem)
			db.session.add(semester)
			db.session.commit()

		# check to see if scheduled course exists else create new
		cur_schedule = ScheduledCourse.query.filter_by(unique_no=scheduled.unique_no, sem_id=semester.id).first()
		
		# check to see if cross_listings exist else create new
		x_list = None
		for x_list_str in scheduled.x_listings:
			x_course = ScheduledCourse.query.filter_by(unique_no=x_list_str, sem_id=semester.id).first()
			if x_course is not None and x_course.xlist is not None:
				x_list = x_course.xlist

		if x_list is None:
			x_list = CrossListed()
			db.session.add(x_list)
			db.session.commit()

		if cur_schedule is None:
			
			# print(f"Adding new scheduled course ({scheduled.yr}{scheduled.sem}): {scheduled.dept} {scheduled.c_num} ", end="")
			# if cur_prof is not None:
			# 	print(f"by {cur_prof.first_name} {cur_prof.last_name}")
			# else:
			# 	print()

			cur_schedule = ScheduledCourse(
				unique_no=scheduled.unique_no, 
				session=scheduled.session, 
				days=scheduled.days, time_from=scheduled.time_from, time_to=scheduled.time_to, 
				location=scheduled.location, 
				max_enrollement=scheduled.max_enrollment, seats_taken=scheduled.seats_taken,
				sem_id=semester.id, 
				course_id=cur_course.id, 
				prof_id=cur_prof.id if cur_prof else None, 
				cross_listed=x_list.id)
			db.session.add(cur_schedule)
		else:
			# print(f"Updating scheduled course ({scheduled.yr}{scheduled.sem}): {scheduled.dept} {scheduled.c_num} ", end="")
			# if cur_prof is not None:
			# 	print(f"by {cur_prof.first_name} {cur_prof.last_name}")
			# else:
			# 	print()
			
			cur_schedule.session = scheduled.session
			cur_schedule.days = scheduled.days
			cur_schedule.time_from = scheduled.time_from
			cur_schedule.time_to = scheduled.time_to
			cur_schedule.location = scheduled.location
			cur_schedule.max_enrollment = scheduled.max_enrollment
			cur_schedule.seats_taken = scheduled.seats_taken
			cur_schedule.course_id = cur_course.id
			cur_schedule.prof_id=cur_prof.id if cur_prof else None
			cur_schedule.cross_listed=x_list.id


		# add prof course relationship if doesnt exist
		if cur_prof:
			prof_course = ProfCourse.query.filter_by(prof_id=cur_prof.id, course_id=cur_course.id).first()

			if prof_course is None:
				prof_course = ProfCourse(prof_id=cur_prof.id, course_id=cur_course.id)
				db.session.add(prof_course)

			prof_course_semester = ProfCourseSemester.query.filter_by(prof_course_id=prof_course.id, sem_id=semester.id).first()
			if prof_course_semester is None:
				prof_course_semester = ProfCourseSemester(prof_course_id=prof_course.id, sem_id=semester.id)
				db.session.add(prof_course_semester)

		full_semester = int(str(semester.year) + str(semester.semester))

		if full_semester == sem_current:
			if cur_course:
				cur_course.current_sem = True
			if cur_prof:
				cur_prof.current_sem = True
		elif full_semester == sem_next:
			if cur_course:
				cur_course.next_sem = True
			if cur_prof:
				cur_prof.next_sem = True
		elif full_semester == sem_future:
			if cur_course:
				cur_course.future_sem = True
			if cur_prof:
				cur_prof.future_sem = True
		db.session.commit()


def populate_prof(prof_info):
	
	if prof_info is not None and len(prof_info) > 1:
		
		first_name, last_name = __parse_prof_name(prof_info[0])
		eid = prof_info[1]

		cur_prof = Prof.query.filter_by(first_name=first_name, last_name=last_name, eid=eid).first()
		if cur_prof is None:
			# print(f"Adding professor {first_name} {last_name}")
			prof = Prof(first_name=first_name, last_name=last_name, eid=eid)
			db.session.add(prof)
			db.session.commit()
		# else:
		# 	print(f"Professor {first_name} {last_name} already exists")

	# else:
		# print("Invalid input to populate_prof")


def populate_course(course_info, cur_sem=None):

	__inherit = "(See Base Topic for inherited information.)"
	null_depts = set()

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

		# check to see if dept exists --> else cannot add
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
			# print("Creating new course", dept_obj.abr, new_course.num)
			db.session.add(new_course)
		elif cur_sem is None or semester==cur_sem:
			# course existed but replacing
			# print("Replacing previous", old_course.dept.abr, old_course.num)
			__replace_course(old_course, new_course)
		# else:
			# course existed and skipping
			# print("Already existed:", old_course.dept.abr, old_course.num)

		db.session.commit()

	null_depts = list(null_depts)
	null_depts.sort()
	# for dept in null_depts:
	# 	print("Unexpected Error: department", dept, "cannot be found in the database")


def __parse_title(cs_title):
	m = re.search(r"^\d+-(.*)", cs_title)

	if m is None:
		return None

	title_words = titlecase(m.group(1)).split()
	return ' '.join([word.upper() if __is_all_one_letter(word) else word for word in title_words])


def __is_all_one_letter(word):

	word = word.lower()
	for c in ascii_lowercase:
		if word == c * len(word):
			return True
	return False


def __populate_child_topics(parent_topic, child_topics, inherit_str):

	for topic in child_topics:

		topic.description = topic.description.replace(inherit_str, parent_topic.description).strip()
		topic.restrictions = topic.restrictions.replace(inherit_str, parent_topic.restrictions).strip()
		topic.pre_req = topic.pre_req.replace(inherit_str, parent_topic.pre_req).strip()


def __check_new_topic(topic_courses_flask):

	topic = None
	if len(topic_courses_flask.all()) > 0:
		topic = topic_courses_flask.first().topic
	else:
		topic = Topic()
		db.session.add(topic)
		db.session.commit()

	return topic.id


def __replace_course(old_course, new_course):

	old_course.title = new_course.title
	old_course.description = new_course.description
	old_course.restrictions = new_course.restrictions
	old_course.pre_req = new_course.pre_req
	old_course.topic_num = new_course.topic_num
	

def __get_topic_zero(topic_courses):

	for topic_course in topic_courses:
		if topic_course.topic_num == 0:
			return topic_course
	return None


def __parse_prof_name(name):

    name_parts = name.split(',')[0].split()
    if len(name_parts) > 1:
        return name_parts[0], ' '.join(name_parts[1:])
    return '', name

