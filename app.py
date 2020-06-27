
from utreview import db, app
from utreview.models import *
from utreview.services import *

# def populate_depts():
#     depts = fetch_depts()
#     for dept in depts:
#         d = Dept(abr=dept[0], name=dept[1])
#         db.session.add(d)
#         db.session.commit()

if __name__ == '__main__':

    # populate_depts()

    courses_summer = import_file('Data Requests.xlsx', 0)
    courses_fall = import_file('Data Requests.xlsx', 1)
    courses_spring = import_file('Data Requests.xlsx', 2)

    fetch_courses(courses_summer, Topic.query.all())

    app.run(debug=True)
