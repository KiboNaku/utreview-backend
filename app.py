
from utreview import db, app, update_sem_vals
from utreview.models import *
from utreview.routes import *
from utreview.services import *
from utreview.database.populate_database import *
import logging
import threading
import time


def thread_function(name):
    
    from utreview.services.fetch_ftp import fetch_ftp_files, fetch_sem_values, parse_ftp
    from utreview.database.populate_database import populate_scheduled_course
    
    fetch_ftp_files('input_data') 
    fetch_sem_values("input_data", "")

    # depts = fetch_depts()
    # populate_dept(depts, override=True) 
    # dept_info = fetch_dept_info('input_data/Data_Requests.xlsx', [0, 1, 2])
    # populate_dept_info(dept_info)

    # courses = fetch_courses('input_data/Data_Requests.xlsx', [0, 1, 2])
    # populate_course(courses, cur_sem = int(sem_current))

    ftp_info = parse_ftp("input_data")
    populate_scheduled_course(ftp_info)


if __name__ == '__main__':    

    # x = threading.Thread(target=thread_function, args=(1,))
    # x.start()
    app.run(debug=True)
    # x.join()
