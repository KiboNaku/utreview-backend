
import json

from utreview import db, app
from utreview.models import *
from utreview.routes import *
from utreview.services import *
from utreview.database.populate_database import *
from utreview.services.fetch_ftp import key_current, key_next, key_future


sem_current = None
sem_next = None
sem_future = None


def update_sem_vals(sem_path):

    print("Updating global semester values")

    global sem_current
    global sem_next
    global sem_future

    with open(sem_path, 'r') as f:
        sem_dict = json.load(f) 
        sem_current = sem_dict[key_current]
        sem_next = sem_dict[key_next]
        sem_future = sem_dict[key_future]

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
    update_sem_vals("semester.txt")

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
