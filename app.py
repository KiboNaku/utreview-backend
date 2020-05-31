from utflow import app, db
from utflow.fetch import fetch_depts, fetch_course_info
from utflow.models import *

if __name__ == '__main__':

    db.create_all()
    depts = fetch_depts()

    for abr, name in depts:
        dept = Dept(abr=abr, name=name)
        db.session.add(dept)

    db.session.commit()

    # TODO: after dept database created

    depts = [dept.abr for dept in Dept.query.all()]
    c_info = fetch_course_info(depts)

    for course in c_info:

        dept_id = Dept.query.filter_by(abr=course.get("dept")).first().id

        ecis = course.get("ecis")
        c_obj = Course(num=course.get("num"), name=course.get("name"), dept_id=dept_id, description="")

        db.session.add(c_obj)
        db.session.commit()

        for students, avg in ecis:
            c_score = ECIS_Course_Score(avg=avg, students=students, dept_id=dept_id, course_id=c_obj.id)
            db.session.add(c_score)

        db.session.commit()

    # app.run(debug=True)
