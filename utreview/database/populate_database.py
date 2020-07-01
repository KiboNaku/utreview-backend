
from utreview import db
from utreview.services.fetch_course_info import *
from utreview.models import *


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


def populate_course(course_info):

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

		if num == '327R':
			print("for 327R", t_num)

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

			# set topic number --> will create new topic if doesnt exist
			new_course.topic_id = __check_new_topic(topic_courses_flask)
			
			# assumption: unique based on title
			if t_num == 0:

				t_zero_course_flask = topic_courses_flask.filter_by(title=title)
				if len(t_zero_course_flask.all()) > 0:
					old_course = t_zero_course_flask.first()

			else:
				t_course_flask = topic_courses_flask.filter_by(title=title)

				if len(t_course_flask.all()) > 0:
					new_course.topic_num = t_course_flask.first().topic_num
					old_course = t_course_flask.first()

				else:

					topic_courses = topic_courses_flask.all()
					has_topic_zero = __has_topic_zero(topic_courses)
					new_course.topic_num = len(topic_courses) + (0 if has_topic_zero else 1)
				
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
	

def __has_topic_zero(topic_courses):

	for topic_course in topic_courses:
		if topic_course.topic_num == 0:
			return True
	return False
