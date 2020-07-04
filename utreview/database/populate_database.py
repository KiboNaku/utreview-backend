
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
			print(f"Cannot find dept {dept}")

		else:
			print(f"Updating dept: {abr}")
			cur_dept.dept = dept
			cur_dept.college = college
		
		db.session.commit()


def populate_scheduled_course(course_info):
	
	for s_course in course_info:
		
		# extract variable info 
		# sem info                                                                                                                                                                                                                                                                              
		yr = s_course["Year"].strip()
		sem = s_course["Semester"].strip()

		# course info
		dept = s_course["Dept-Abbr"].strip()
		c_num_raw = s_course["Course Nbr"].strip()
		c_num = c_num_raw[1:] if c_num_raw[0].isalpha() else c_num_raw
		topic = s_course["Topic"].strip()
		title = s_course["Title"].strip()
		
		# prof info
		prof_eid = s_course["Instructor EID"].strip()

		# scheduled info
		session = c_num_raw[0] if c_num_raw[0].isalpha() else None
		unique_num = s_course["Unique"].strip()
		days = s_course["Days"].strip()
		t_from = s_course["From"].strip()
		t_to = s_course["To"].strip()
		building = s_course["Building"].strip()
		room = s_course["Room"].strip()
		m_enrollment = s_course["Max Enrollment"].strip()
		seats_taken = s_course["Seats Taken"].strip()
		x_listings = [listing.strip() for listing in s_course["X-Listings"].strip().split(",")]

		# check to see if course exists
		topic = -1 if topic.empty() else int(topic)
		dept_obj = Dept.query.filter_by(abr=dept).first()
		cur_course = Course.query.filter_by(dept_id=dept_obj.id, num=c_num, topic_num=topic).first()

		if cur_course is None:
			print(f"Populate scheduled course: cannot find course {dept} {c_num}")
			continue

		# check to see if prof exists --> if not then add prof
		cur_prof = Prof.query.filter_by(eid=prof_eid).first()
		
		if cur_prof is None:
			populate_prof(fetch_prof(prof_eid))
			cur_prof = Prof.query.filter_by(eid=prof_eid).first()

		# check to see if scheduled course exists

		unique_no = db.Column(db.Integer, nullable=False)
		session = db.Column(db.String(1), nullable=True)

		days = db.Column(db.String(10))
		time_from = db.Column(db.String(8))
		time_to = db.Column(db.String(8))
		location = db.Column(db.String(20))
		max_enrollement = db.Column(db.Integer)
		seats_taken = db.Column(db.Integer)

		sem_id = db.Column(db.Integer, db.ForeignKey("semester.id"), nullable=False)
		course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
		prof_id = db.Column(db.Integer, db.ForeignKey('prof.id'), nullable=False)
		cross_listed = db.Column(db.Integer, db.ForeignKey('cross_listed.id'), nullable=True)
		
		



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


def populate_course(course_info):

	__inherit = "(See Base Topic for inherited information.)"
	null_depts = set()

	for course in course_info:

		# fetch values from dictionary
		dept = course[KEY_DEPT]
		num = course[KEY_NUM]
		title = course[KEY_TITLE]
		description = course[KEY_DESCRIPTION]
		restrictions = course[KEY_RESTRICTION]
		t_num = course[KEY_TOPIC_NUM]
		pre_req = course[KEY_PRE_REQ]

		# check to see if dept exists --> else cannot add
		dept_obj = Dept.query.filter_by(abr=dept).first()

		if dept_obj is None:
			null_depts.add(dept)
			continue
		
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
			
			# all courses with same name --> should be unique topics
			# if len 0 --> new topic
			topic_courses_flask = Course.query.filter_by(dept_id=dept_obj.id, num=num)
			topic_courses = topic_courses_flask.all()

			# set topic number --> will create new topic if doesnt exist
			new_course.topic_id = __check_new_topic(topic_courses_flask)
			
			# assumption: unique based on title
			if t_num == 0:

				t_zero_course_flask = topic_courses_flask.filter_by(title=title)
				if len(t_zero_course_flask.all()) > 0:
					old_course = t_zero_course_flask.first()

				__populate_child_topics(new_course, topic_courses, __inherit)
			else:

				t_course_flask = topic_courses_flask.filter_by(title=title)
				topic_zero = __get_topic_zero(topic_courses)

				if len(t_course_flask.all()) > 0:
					new_course.topic_num = t_course_flask.first().topic_num
					old_course = t_course_flask.first()

				else:
					new_course.topic_num = len(topic_courses) + (1 if topic_zero is None else 0)
				
				__populate_child_topics(topic_zero, [new_course], __inherit)
				
		else:
			# course doesn't have topic number
			old_course = Course.query.filter_by(dept_id=dept_obj.id, num=num).first()
		
		# create new or replace old
		if old_course is None:
			# new course
			print("Creating new course", dept_obj.abr, new_course.num)
			db.session.add(new_course)
		else:
			# course existed
			print("Replacing previous", old_course.dept.abr, old_course.num)
			__replace_course(old_course, new_course)

		db.session.commit()

	null_depts = list(null_depts)
	null_depts.sort()
	for dept in null_depts:
		print("Unexpected Error: department", dept, "cannot be found in the database")


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

    name_parts = name.split()
    if len(name_parts) > 1:
        return name_parts[0], ' '.join(name_parts[1:])
    return '', name

