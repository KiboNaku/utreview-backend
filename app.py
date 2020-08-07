
from utreview import db, app, update_sem_vals
from utreview.models import *
from utreview.routes import *
from utreview.services import *
from utreview.database.populate_database import *
import logging
import threading
import time


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

    print("----------------------printing courses------------------------------------------")
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
                                print("Failed to parse course")
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

    # from utreview.services.fetch_web import fetch_profcourse_info, fetch_profcourse_semdepts
    # sems, depts = fetch_profcourse_semdepts()
    # fetch_profcourse_info("prof_course.txt", sems, depts)
    # from utreview.database.populate_database import populate_profcourse
    # populate_profcourse("prof_course.txt")
    # from utreview.services.fetch_ftp import fetch_ftp_files, fetch_sem_values, parse_ftp
    # from utreview.database.populate_database import populate_scheduled_course
    # ftp_info = parse_ftp("input_data")
    # populate_scheduled_course(ftp_info)
    # -----------------------------------------

    # from utreview.database.populate_database import populate_sem
    # populate_sem()

    # x = threading.Thread(target=thread_function, args=(1,))
    # x.start()
    # app.run(debug=True)
    # x.join()

    # finished fetch for sem 0
    # import io
    # import pdfminer
    # from pdfminer.converter import TextConverter
    # from pdfminer.pdfinterp import PDFPageInterpreter
    # from pdfminer.pdfinterp import PDFResourceManager
    # from pdfminer.pdfpage import PDFPage

    
    # laparams = pdfminer.layout.LAParams()
    # setattr(laparams, 'all_texts', True)

    # def extract_text_from_pdf(pdf_path):

    #     resource_manager = PDFResourceManager()
    #     fake_file_handle = io.StringIO()
    #     converter = TextConverter(resource_manager, fake_file_handle, laparams=laparams)
    #     page_interpreter = PDFPageInterpreter(resource_manager, converter)
        
    #     with open(pdf_path, 'rb') as fh:
    #         for page in PDFPage.get_pages(fh, 
    #                                     caching=True,
    #                                     check_extractable=True):
    #             page_interpreter.process_page(page)
    #             text = fake_file_handle.getvalue()
                
    #         text = fake_file_handle.getvalue()
        
    #     # close open handles
    #     converter.close()
    #     fake_file_handle.close()
        
    #     if text:
    #         return text

    # text = extract_text_from_pdf('University_of_Texas_Academic_Summary (1).pdf')

    # for line in text:
    #     depts = [dept.abr for dept in Dept.query.all()]
    #     depts_str = '|'.join(depts)
    #     dept_m = re.search(r'^((' + depts_str + r') [0-9][a-zA-Z0-9]+).*', line, re.DOTALL)
    #     # if dept_m is not None:
    #         # print(dept_m.group(1))
    # print(repr(text))
    
    

    


