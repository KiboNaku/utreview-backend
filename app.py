
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

    fetch_courses('Data Requests.xlsx', 0)

    app.run(debug=True)

    # from utreview.services.fetch_ftp import fetch_ftp_files
    # fetch_ftp_files('input_data')

    # app.run(debug=True)
