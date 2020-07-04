
from utreview import db, app
from utreview.models import *
from utreview.services import *
from utreview.database.populate_database import *

# def populate_depts():
#     depts = fetch_depts()
#     for dept in depts:
#         d = Dept(abr=dept[0], name=dept[1])
#         db.session.add(d)
#         db.session.commit()

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


    from utreview.services.fetch_prof import fetch_prof
    print(fetch_prof("mlg92"))

    # app.run(debug=True)
