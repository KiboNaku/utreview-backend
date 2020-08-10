
import datetime
import os
import pytz
import time

from .fetch_course_info import fetch_courses, fetch_dept_info
from .fetch_ftp import fetch_ftp_files, fetch_sem_values, parse_ftp
from .fetch_web import fetch_depts
from utreview import logger, sem_current
from utreview.database.populate_database import (
    populate_course, populate_dept,  populate_dept_info, populate_ecis, populate_scheduled_course,
    reset_courses, reset_profs,
)


def automate_backend(name):

    while True:

        dt_today = datetime.datetime.now(pytz.timezone('America/Chicago'))
        dt_tmr = dt_today + datetime.timedelta(days=1)
        dt_tmr = dt_tmr.replace(hour=1, minute=0)

        until_start = int((dt_tmr - dt_today).total_seconds())
        logger.info(f"Waiting {until_start} seconds until start time")
        for _ in range(until_start):
            time.sleep(1)

        # task 1: fetch ftp files and update scheduled course info
        logger.info("Fetching new ftp files")
        fetch_ftp_files('input_data')
        fetch_sem_values("input_data", "")

        logger.info("Updating scheduled course database info")
        ftp_info = parse_ftp("input_data")
        reset_courses()
        reset_profs()
        populate_scheduled_course(ftp_info)

        # task 2: read maintenance.txt and perform task as necessary
        run_maintenance()

        # task 3: organize log files
        organize_log_files()


def run_maintenance():
    from utreview.services.fetch_web import fetch_profcourse_info, fetch_profcourse_semdepts
    from utreview.database.populate_database import populate_profcourse

    __maintenance_txt_file = "maintenance.txt"
    logger.info(f"Initiating {__maintenance_txt_file}")

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
                            populate_course(courses, cur_sem=int(sem_current))
                        elif cmd == 'ecis':
                            populate_ecis(path, pages)
                    else:
                        if cmd == 'prof_course':
                            sems, depts = fetch_profcourse_semdepts()
                            fetch_profcourse_info(path, sems, depts)
                            populate_profcourse(path)


def organize_log_files():
    from utreview import DEFAULT_LOG_FOLDER
    import shutil

    logger.info("Organizing log files")
    dt_today = datetime.datetime.now(pytz.timezone('America/Chicago'))
    files = [f for f in os.listdir(DEFAULT_LOG_FOLDER) if os.path.isfile(os.path.join(DEFAULT_LOG_FOLDER, f))]

    for f in files:
        log_path = get_log_file_path(f)
        if log_path is not None:
            dir_path = os.path.split(log_path)[0]
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            original_path = os.path.join(DEFAULT_LOG_FOLDER, f)
            shutil.move(original_path, log_path)


def get_log_file_path(file_name, check_date=True):
    from utreview import DEFAULT_LOG_FOLDER
    import re

    name_pts = file_name.split('.')
    date_pt = name_pts[-1]

    match = re.search(r'(\d{4})(\d{2})(\d{2})', date_pt)
    if match is None:
        return None

    year_str, month_str, day_str = match.group(1), match.group(2), match.group(3)
    year, month, day = int(year_str), int(month_str), int(day_str)

    dt_today = datetime.datetime.now(pytz.timezone('America/Chicago'))
    today_yr, today_month, today_day = dt_today.year, dt_today.month, dt_today.day

    if check_date and today_yr == year and today_month == month and today_day == day:
        return None

    date = datetime.datetime(year=year, month=month, day=day)

    start = date - datetime.timedelta(days=date.weekday())
    start = start if start.month == month else datetime.datetime(year, month, 1)
    end = date + datetime.timedelta(days=-date.weekday() - 1, weeks=1)
    end = end if end.month == month else datetime.datetime(year, month, 31)

    start_day_str = ('0' + str(start.day))[-2:]
    end_day_str = ('0' + str(end.day))[-2:]

    yr_dir = f'year_{year_str}'
    month_dir = f'month_{month_str}'
    week_dir = f'week_{start_day_str}_to_{end_day_str}'

    return os.path.join(DEFAULT_LOG_FOLDER, yr_dir, month_dir, week_dir, file_name)