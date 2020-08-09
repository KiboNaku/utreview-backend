
from utreview import db, app, update_sem_vals, logger
from utreview.models import *
from utreview.routes import *
from utreview.services import *
from utreview.database.populate_database import *
import logging
import sys
import os
import threading
import time
import datetime


def is_residence_or_extension(course):
        for string in course.values():
            string = str(string)
            if 'In residence' in string or 'Extension' in string:
                return True
        return False

def parse_academic_summary(pdf_path):

    from tabula import read_pdf
    import pandas as pd
    dfs = read_pdf(pdf_path, pages='all', area=(0, 0, 10000000, 1000000), pandas_options={'header': None})
    df = pd.DataFrame()

    for _df in dfs:
        df = pd.concat([df, _df])

    pdf_vals = df.values.tolist()
    
    sems = {}
    cur_sem = None
    search = False
    course_index = None
    unique_index = None

    for lst in pdf_vals:

        lst = list(lst)
        template = {
            'course': None,
            'unique': None,
            'all': None
        }

        if search:
            sem_courses = sems.get(cur_sem, [])
            template['course'] = lst[course_index] if course_index is not None else None
            template['unique'] = lst[unique_index] if unique_index is not None else None
            template['all'] = ' '.join([str(val) for val in lst])

            sem_courses.append(template)
            sems[cur_sem] = sem_courses

        for string in lst:

            string = str(string)
            m = re.search(r'^((Spring|Summer|Fall) \d+)', string)
            
            if m is not None:
                cur_sem = m.group(1)
                search = False
                break

            if 'Unique' in string or 'Course' in string:
                
                search = True
                
                course_index = [index for index, s in enumerate(lst) if 'Course' in str(s)]
                unique_index = [index for index, s in enumerate(lst) if 'Unique' in str(s)]

                course_index = course_index[0] if len(course_index) > 0 else None
                unique_index = unique_index[0] if len(unique_index) > 0 else None

                break

    depts = [dept.abr for dept in Dept.query.all()]
    depts_str = '|'.join(depts)

    # TODO: update to avoid arrays out of bound
    parsed_sem = {}
    
    for semester, courses in sems.items():

        parsed = []
    
        for i in range(len(courses)):

            template = {
                'course': None,
                'unique': None
            }

            course = courses[i]

            if is_residence_or_extension(course):
                
                course_num = str(course['course'])
                unique = str(course['unique'])

                if course_num is not None:
                    found_dept = False
                    dept_m = re.search(r'^(' + depts_str + r').*', course_num, re.DOTALL)

                    if dept_m is not None:
                        found_dept = True
                    
                    if found_dept:
                        m = re.search(r'^((' + depts_str + r') [0-9][a-zA-Z0-9]+).*', course_num, re.DOTALL)
                        if m is None:
                            i += 1
                            num_part = courses[i]['course']
                            num_m = re.search(r'([0-9][a-zA-Z0-9]+).*', str(num_part))
                            if num_m is None:
                                # failed to parse course
                                course_num = None
                            else:
                                course_num = dept_m.group(1) + " " + num_m.group(1)
                        else:
                            course_num = m.group(1)
                
                if unique is not None:
                    m = re.search(r'([0-9]{5})', unique)
                    unique = m.group(1) if m is not None else None

                    template['course'] = course_num
                    template['unique'] = unique

                parsed.append(template)
        parsed_sem[semester] = parsed

    return parsed_sem


def refresh_ecis():
    
    # update current ecis values
    for course in Course.query.all():
        course_ecis = 0
        course_students = 0
        for prof_course in course.prof_course:
            for prof_course_sem in prof_course.prof_course_sem:
                for ecis_child in prof_course_sem.ecis:
                    course_ecis += ecis_child.course_avg * ecis_child.num_students
                    course_students += ecis_child.num_students
        
        if course_students > 0:
            course.ecis_avg = course_ecis/course_students
        course.ecis_students = course_students
        db.session.commit()

    for prof in Prof.query.all():
        prof_ecis = 0
        prof_students = 0
        for prof_course in prof.prof_course:
            for prof_course_sem in prof_course.prof_course_sem:
                for ecis_child in prof_course_sem.ecis:
                    prof_ecis += ecis_child.prof_avg * ecis_child.num_students
                    prof_students += ecis_child.num_students

        if prof_students > 0:
            prof.ecis_avg = prof_ecis/prof_students
        prof.ecis_students = prof_students
        db.session.commit()


def populate_ecis(file_path, pages):
    from utreview.services.fetch_ecis import parse_ecis_excel, KEY_UNIQUE_NUM, KEY_COURSE_AVG, KEY_PROF_AVG, KEY_NUM_STUDENTS, KEY_YR, KEY_SEM
    ecis_lst = parse_ecis_excel(file_path, pages)

    # remember to update Course and Prof objects when inputting new ECIS scores

    for ecis in ecis_lst:
        
        unique, c_avg, p_avg, students, yr, sem = ecis[KEY_UNIQUE_NUM], ecis[KEY_COURSE_AVG], ecis[KEY_PROF_AVG], ecis[KEY_NUM_STUDENTS], ecis[KEY_YR], ecis[KEY_SEM]

        sem_obj = Semester.query.filter_by(year=yr, semester=sem).first()
        if sem_obj is None:
            # print("Cannot find semester for:", yr, sem, "Skipping...")
            continue
    
        pcs_obj = ProfCourseSemester.query.filter_by(unique_num=unique, sem_id=sem_obj.id).first()
        if pcs_obj is None:
            # print("Failed to find ProfCourseSemester for: unique=", unique, "semester=", yr, sem, "Skipping...")
            continue
        
        # assumption: only one ecis score per prof_course_semester instance
        ecis_lst = pcs_obj.ecis
        if len(ecis_lst) >= 1:
            continue
        
        ecis_obj = EcisScore(course_avg=c_avg, prof_avg=p_avg, num_students=students, prof_course_sem_id=pcs_obj.id)
        db.session.add(ecis_obj)
        db.session.commit()

        # updating prof and course ecis avgs
        pc_obj = pcs_obj.prof_course
        prof_obj = pc_obj.prof
        course_obj = pc_obj.course

        total_students = prof_obj.ecis_students + students
        total_avg = ((prof_obj.ecis_avg * prof_obj.ecis_students) if prof_obj.ecis_avg is not None else 0) + ((p_avg * students) if p_avg is not None else 0)
        prof_obj.ecis_avg = (total_avg / total_students) if total_students > 0 else None
        prof_obj.ecis_students = total_students

        total_students = course_obj.ecis_students + students
        total_avg = ((course_obj.ecis_avg * course_obj.ecis_students) if course_obj.ecis_avg is not None else 0) + ((c_avg * students) if c_avg is not None else 0)
        course_obj.ecis_avg = (total_avg / total_students) if total_students > 0 else None
        course_obj.ecis_students = total_students

        db.session.commit()


def automate_backend(name):
    
    from utreview.services.fetch_ftp import fetch_ftp_files, fetch_sem_values, parse_ftp
    from utreview.database.populate_database import populate_scheduled_course
    from utreview.services.fetch_web import fetch_profcourse_info, fetch_profcourse_semdepts
    from utreview.database.populate_database import populate_profcourse
    import pytz

    __maintenance_txt_file = "maintenance.txt"
    
    while True:
        
        dt_today = datetime.datetime.now(pytz.timezone('America/Chicago'))
        dt_tmr = dt_today + datetime.timedelta(days=1)
        dt_tmr = dt_tmr.replace(hour=1, minute=0)
        
        until_start = (dt_today-dt_tmr).total_seconds()
        logger.info(f"Waiting {until_start} seconds until start time")
        time.sleep(until_start)

        # task 1: fetch ftp files and update scheduled course info
        logger.info("Fetching new ftp files")
        fetch_ftp_files('input_data') 
        fetch_sem_values("input_data", "")

        logger.info("Updating scheduled course database info")
        ftp_info = parse_ftp("input_data")
        populate_scheduled_course(ftp_info)

        # task 2: read maintenance.txt and perform task as necessary
        logger.info("Initiating maintenance.txt")
        if os.path.isfile(__maintenance_txt_file):
            with open(__maintenance_txt_file, 'r') as f:

                commands = f.readlines()
                for command in commands:
                    command_parts = command.split(' ')

                    if len(command_parts) >= 2:
                        cmd, path = command_parts[0], command_parts[1]
                        logger.info(f"Executing {cmd} {path}")

                        if len(command_parts) >= 3:
                            pages = [int(page) for page in command_parts[2].split(',')]
                            
                            if cmd == 'course':
                                logger.info("Updating department info")
                                depts = fetch_depts()
                                populate_dept(depts, override=True)

                                dept_info = fetch_dept_info(path, pages)
                                populate_dept_info(dept_info)

                                courses = fetch_courses(path, pages)
                                populate_course(courses, cur_sem = int(sem_current))
                            elif cmd == 'ecis':
                                populate_ecis(path, pages)
                        else:
                            if cmd == 'prof_course':
                                sems, depts = fetch_profcourse_semdepts()
                                fetch_profcourse_info(path, sems, depts)
                                populate_profcourse(path)

        # task 3: organize log files
        organize_log_files()

       
def organize_log_files():

    # from utreview import DEFAULT_LOG_FOLDER

    pass


def get_log_file_path():

    from utreview import DEFAULT_LOG_FOLDER

    today = datetime.date.today()
    year, month = today.year, today.month
    date = today.strftime("%b_%d_%Y")

    start = today - datetime.timedelta(days=today.weekday())
    start = start if start.month == month else datetime.datetime(year, month, 1)
    end = today + datetime.timedelta(days=-today.weekday()-1, weeks=1)
    end = end if end.month == month else datetime.datetime(year, month, 31)

    month_str = ('0' + str(month))[-2:]
    start_day_str = ('0' + str(start.day))[-2:]
    end_day_str = ('0' + str(end.day))[-2:]

    yr_dir = f'year_{year}'
    month_dir = f'month_{month_str}'
    week_dir = f'week_{start_day_str}_to_{end_day_str}'

    return os.path.join(DEFAULT_LOG_FOLDER, yr_dir, month_dir, week_dir, file_name)


automate_thread = threading.Thread(target=automate_backend, args=(1,))
automate_thread.start()


# if __name__ == '__main__':    
    
    # app.run(debug=True)
