
import os
import threading
import time
import datetime
import pytz

from utreview import db, app, update_sem_vals, logger
from utreview.routes import *
from utreview.database.populate_database import *


def is_residence_or_extension(course_obj):
    """

    :param course_obj:
    :return:
    """
    for string in course_obj.values():
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


automate_thread = threading.Thread(target=automate_backend, args=(1,))
automate_thread.daemon = True
if not automate_thread.is_alive():
    automate_thread.start()


if __name__ == '__main__':    
    app.run(debug=True)
