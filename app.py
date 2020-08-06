
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

    # from utreview.database.populate_database import populate_sem
    # populate_sem()

    # x = threading.Thread(target=thread_function, args=(1,))
    # x.start()
    # app.run(debug=True)
    # x.join()

    # finished fetch for sem 0
    # from utreview.services.fetch_web import fetch_profcourse_info, fetch_profcourse_semdepts
    # sems, depts = fetch_profcourse_semdepts()
    # fetch_profcourse_info("prof_course.txt", sems[2:], depts)
    # from utreview.database.populate_database import populate_profcourse
    # populate_profcourse("prof_course.txt")
    
    from tabula import read_pdf
    import pandas as pd
    dfs = read_pdf("University_of_Texas_Academic_Summary.pdf", pages='all', pandas_options={'header': None})
    df = pd.DataFrame()

    for _df in dfs:
        df = pd.concat([df, _df])

    pdf_vals = df.values.tolist()
    
    sems = {}
    cur_sem = None
    search = False

    for lst in pdf_vals:

        lst = list(lst)

        data = {
            'keys': {
                'course': None,
                'unique': None,
            },
            'data': []
        }

        for string in lst:

            string = str(string)
            m = re.search(r'^((Spring|Summer|Fall) \d+)', string)
            
            if m is not None:
                cur_sem = m.group(1)
                search = False
                break

            if 'Unique' in string or 'Course' in string:
                
                search = True
                sem_courses = sems.get(cur_sem, data)
                
                keys = sem_courses['keys']
                keys['course'] = [index for index, s in enumerate(lst) if 'Course' in str(s)][0]
                keys['unique'] = [index for index, s in enumerate(lst) if 'Unique' in str(s)][0]

                sem_courses['keys'] = keys

                break
        
        if search:
            sem_courses = sems.get(cur_sem, data)
            sem_courses['data'].append(lst)
            sems[cur_sem] = sem_courses

    print("----------------------printing courses------------------------------------------")
    depts = [dept.abr for dept in Dept.query.all()]
    depts_str = '|'.join(depts)

    # TODO: update to avoid arrays out of bound
    parsed_sem = {}
    print(sems)
    
    for semester, data in sems.items():

        keys = data['keys']
        courses = data['data']
        parsed = []
    
        for i in range(len(courses)):

            template = {
                'course': None,
                'unique': None
            }

            course = courses[i]

            if 'In residence' in course or 'Extension' in course:
                
                course_num = course[keys['course']] if keys['course'] is not None else None
                unique = course[keys['unique']] if keys['unique'] is not None else None

                # TODO: bad assumption: assuming the keys are not None
                found_dept = False
                dept_m = re.search(r'^(' + depts_str + r').*', course_num, re.DOTALL)

                if dept_m is not None:
                    found_dept = True
                
                if found_dept:
                    m = re.search(r'^((' + depts_str + r') [0-9][a-zA-Z0-9]+).*', course_num, re.DOTALL)
                    if m is None:
                        i += 1
                        num_part = courses[i][keys['course']]
                        num_m = re.search(r'(^[0-9][a-zA-Z0-9]+).*', str(num_part))
                        if num_m is None:
                            print("Failed to parse course")
                            course_num = None
                        else:
                            course_num = dept_m.group(1) + " " + num_m.group(1)
                    else:
                        course_num = m.group(1)

                m = re.search(r'([0-9]+)', unique)
                unique = m.group(1) if m is not None else None

                template['course'] = course_num
                template['unique'] = unique

                # found_dept = False
                # part = str(course[0])
                # dept_m = re.search(r'^(' + depts_str + r').*', part, re.DOTALL)
                # if dept_m is not None:
                #     found_dept = True
                
                # if found_dept:
                #     m = re.search(r'^((' + depts_str + r') [0-9][a-zA-Z0-9]+).*', part, re.DOTALL)
                #     if m is None:
                #         i += 1
                #         num_part = courses[i][0]
                #         num_m = re.search(r'(^[0-9][a-zA-Z0-9]+).*', str(num_part))
                #         if num_m is None:
                #             print("Failed to parse course")
                #         else:
                #             print(dept_m.group(1), num_m.group(1))
                #     else:
                #         print(m.group(1))
                parsed.append(template)
        parsed_sem[semester] = parsed

    for sem, courses in parsed_sem.items():
        print("Course in", sem, ":")
        for course in courses:
            print(course)


