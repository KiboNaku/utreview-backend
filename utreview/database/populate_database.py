
import re
from titlecase import titlecase

from utreview import db
from utreview.services.fetch_course_info import *
from utreview.models import *
from utreview.services.fetch_prof import fetch_prof


def populate_dept(dept_info, override=False):

	print('Populating departments')
	
	for abr, name in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:

			abr = abr.strip()
			name = name.strip()
			
			print(f"Adding dept {name} ({abr}) to database")
			dept = Dept(abr=abr, name=name)
			db.session.add(dept)

		elif override:
			print(f"Overriding dept {name} ({abr}) to database")
			cur_dept.abr = abr
			cur_dept.name = name

		else:
			print(f"Already exists: dept {name} ({abr})")
		
		db.session.commit()


def populate_dept_info(dept_info):
	
	print('Populating departments with additional info')
	
	for abr, dept, college in dept_info:

		cur_dept = Dept.query.filter_by(abr=abr).first()
		if cur_dept is None:
			print(f"Cannot find dept {abr} --> adding as non-major")
			cur_dept = Dept(abr=abr, dept=dept, college=college, name='')
			db.session.add(cur_dept)

		else:
			print(f"Updating dept: {abr}")
			cur_dept.dept = dept
			cur_dept.college = college
		
		db.session.commit()


def populate_scheduled_course(course_info):
	# problem: topic number inconsistencies
	
	for s_course in course_info:
		
		# extract variable info 
		# sem info                                                                                                                                                                                                                                                                              
		yr = int(s_course["Year"].strip())
		sem = int(s_course["Semester"].strip())

		# course info
		dept = s_course["Dept-Abbr"].strip().upper()
		c_num_raw = s_course["Course Nbr"].strip().upper()
		topic = s_course["Topic"].strip()

		try:
			topic = int(topic)
		except ValueError:
			topic = -1

		title = s_course["Title"].strip()

		if not c_num_raw:
			print("Populate scheduled course: no course number. Skipping...")
			continue
		
		c_num = c_num_raw[1:] if c_num_raw[0].isalpha() else c_num_raw

		# prof info
		prof_eid = s_course["Instructor EID"].strip()

		# scheduled info
		session = c_num_raw[0] if c_num_raw[0].isalpha() else None
		unique_no = s_course["Unique"].strip()
		try:
			unique_no = int(unique_no)
		except ValueError:
			print("Populate scheduled course: no unique number. Skipping...")
			continue

		days = s_course["Days"].strip().upper()
		time_from = int_or_none(s_course["From"].strip())

		time_to = int_or_none(s_course["To"].strip())
		building = s_course["Building"].strip().upper()
		room = s_course["Room"].strip().upper()
		max_enrollment = int_or_none(s_course["Max Enrollment"].strip())
		seats_taken = int_or_none(s_course["Seats Taken"].strip())
		x_listings = [listing.strip() for listing in s_course["X-Listings"].strip().split(",")]

		# check to see if course exists
		dept_obj = Dept.query.filter_by(abr=dept).first()
		if dept_obj is None:
			print(f"Populate scheduled course: cannot find department {dept}. Skipping...")
			continue

		cur_courses = Course.query.filter_by(dept_id=dept_obj.id, num=c_num)
		if len(cur_courses.all()) > 1:
			cur_courses = cur_courses.filter_by(topic_num=topic)
		cur_course = cur_courses.first()

		if cur_course is None:
			print(f"Populate scheduled course: cannot find course {dept} {c_num} w/ topic num {topic}. Skipping...")
			continue

		# check to see if prof exists --> if not then add prof
		cur_prof = Prof.query.filter_by(eid=prof_eid).first()
		
		if cur_prof is None and prof_eid:
			populate_prof(fetch_prof(prof_eid))
			cur_prof = Prof.query.filter_by(eid=prof_eid).first()

		# check to see if semester exists else add semester
		semester = Semester.query.filter_by(year=yr, semester=sem).first()
		if semester is None:
			semester = Semester(year=yr, semester=sem)
			db.session.add(semester)
			db.session.commit()

		# check to see if scheduled course exists else create new
		cur_schedule = ScheduledCourse.query.filter_by(unique_no=unique_no, sem_id=semester.id).first()
		location = __parse_location(title, building, room)
		if cur_schedule is None:
			
			print(f"Adding new scheduled course ({yr}{sem}): {dept} {c_num} ", end="")
			if cur_prof is not None:
				print(f"by {cur_prof.first_name} {cur_prof.last_name}")

			# check to see if cross_listings exist else create new
			x_list = None
			for x_list_str in x_listings:
				x_course = ScheduledCourse.query.filter_by(unique_no=x_list_str, sem_id=semester.id).first()
				if x_course is not None and x_course.xlist is not None:
					x_list = x_course.xlist

			if x_list is None:
				x_list = CrossListed()

			cur_schedule = ScheduledCourse(
				unique_no=unique_no, session=session, 
				days=days, time_from=time_from, time_to=time_to, 
				location=location, 
				max_enrollement=max_enrollment, seats_taken=seats_taken,
				sem_id=semester.id, 
				course_id=cur_course.id, 
				prof_id=cur_prof.id if cur_prof else None, 
				cross_listed=x_list.id)
		else:
			print(f"Updating scheduled course ({yr}{sem}): {dept} {c_num} ", end="")
			if cur_prof is not None:
				print(f"by {cur_prof.first_name} {cur_prof.last_name}")
			
			cur_schedule.session = session
			cur_schedule.days = days
			cur_schedule.time_from = time_from
			cur_schedule.time_to = time_to
			cur_schedule.location = location
			cur_schedule.max_enrollment = max_enrollment
			cur_schedule.seats_taken = seats_taken
			cur_schedule.course_id = cur_course.id
			if cur_prof is not None: cur_schedule.prof_id = cur_prof.id

		db.session.add(cur_schedule)
		db.session.commit()

		# add prof course relationship if doesnt exist
		if cur_prof:
			prof_course = ProfCourse.query.filter_by(prof_id=cur_prof.id, course_id=cur_course.id).first()

			if prof_course is None:
				prof_course = ProfCourse(prof_id=cur_prof.id, course_id=cur_course.id)
				db.session.add(prof_course)
				db.session.commit()

			prof_course_semester = ProfCourseSemester.query.filter_by(prof_course_id=prof_course.id, sem_id=semester.id).first()
			if prof_course_semester is None:
				prof_course_semester = ProfCourseSemester(prof_course_id=prof_course.id, sem_id=semester.id)
				db.session.add(prof_course_semester)
				db.session.commit()


def populate_prof(prof_info):

	if len(prof_info) > 1:

		first_name, last_name = __parse_prof_name(prof_info[0])
		eid = prof_info[1]

		cur_prof = Prof.query.filter_by(first_name=first_name, last_name=last_name, eid=eid).first()
		if cur_prof is None:
			print(f"Adding professor {first_name} {last_name}")
			prof = Prof(first_name=first_name, last_name=last_name, eid=eid)
			db.session.add(prof)
			db.session.commit()
		else:
			print(f"Professor {first_name} {last_name} already exists")

	else:
		print("Invalid input to populate_prof")


def int_or_none(string):
	try:
		return int(string)
	except ValueError:
		return None


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
			print("Creating new course", dept_obj.abr, new_course.num)
			db.session.add(new_course)
		elif cur_sem is None or semester==cur_sem:
			# course existed but replacing
			print("Replacing previous", old_course.dept.abr, old_course.num)
			__replace_course(old_course, new_course)
		else:
			# course existed and skipping
			print("Already existed:", old_course.dept.abr, old_course.num)

		db.session.commit()

	null_depts = list(null_depts)
	null_depts.sort()
	for dept in null_depts:
		print("Unexpected Error: department", dept, "cannot be found in the database")


def __parse_title(cs_title):
	m = re.search(r"^\d+-(.*)", cs_title)
	return None if m is None else titlecase(m.group(1))


def __parse_location(title, building, room):

	__default = "N/A"
	__web_tag = "-W"

	if not building or not room:
		return 'WEB' if __web_tag in title else 'N/A'
	
	return f'{building} {room}'


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

