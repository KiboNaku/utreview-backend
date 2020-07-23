
from utreview import db, app, update_sem_vals
from utreview.models import *
from utreview.routes import *
from utreview.services import *
from utreview.database.populate_database import *


def __get_topic_zero(topic_courses):

	for topic_course in topic_courses:
		if topic_course.topic_num == 0:
			return topic_course
	return None

if __name__ == '__main__':

    # from utreview.services.fetch_ftp import fetch_ftp_files, parse_ftp
    # fetch_ftp_files('input_data')

    # fetch semester values 
    # from utreview.services.fetch_ftp import fetch_sem_values
    # fetch_sem_values("input_data", "")

    # fetch dept info----------------------
    # depts = fetch_depts()
    # populate_dept(depts, override=True)

    # dept_info = fetch_dept_info('input_data/Data Requests.xlsx', [0, 1, 2])
    # populate_dept_info(dept_info)

    # ----------finish fetch dept info---------------

    # fetch course info---------------------

    # courses = fetch_courses('input_data/Data Requests.xlsx', [0, 1, 2])
    # populate_course(courses, cur_sem = int(sem_current))

    # --------------finish fetch course info---------------------

    # fetch schedule info ----------------------
    # from utreview.services.fetch_ftp import parse_ftp, fetch_ftp_files
    # ftp_info = parse_ftp("input_data")
    # from utreview.database.populate_database import populate_scheduled_course
    # populate_scheduled_course(ftp_info)

    app.run(debug=True)
