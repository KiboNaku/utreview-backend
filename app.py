
import json

from utreview import db, app
from utreview.models import *
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


if __name__ == '__main__':



    # app.run(debug=True)
    # from utreview.services.fetch_ftp import fetch_ftp_files, parse_ftp
    # fetch_ftp_files('input_data')
    # print(parse_ftp('input_data'))

    # depts = fetch_depts()
    # populate_dept(depts, override=True)

    # courses = fetch_courses('input_data/Data Requests.xlsx', [0])
    # populate_course(courses)

    # dept_info = fetch_dept_info('input_data/Data Requests.xlsx', [0])
    # populate_dept_info(dept_info)


    # from utreview.services.fetch_prof import fetch_prof
    # print(fetch_prof("mlg92"))


    from utreview.services.fetch_ftp import fetch_sem_values
    fetch_sem_values("input_data", "")
    update_sem_vals("semester.txt")

    from utreview.services.fetch_ftp import parse_ftp
    ftp_info = parse_ftp("input_data")
    from utreview.database.populate_database import populate_scheduled_course
    populate_scheduled_course(ftp_info)

    # app.run(debug=True)
