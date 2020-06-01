from utflow import app, db
from utflow.fetch import fetch_depts, fetch_course_info, fetch_prof_info
from utflow.models import *

if __name__ == '__main__':

    # db.drop_all()
    # db.create_all()

    # print("Fetching departments----------------------------------------")
    # depts = fetch_depts()

    # for abr, name in depts:
    #     dept = Dept(abr=abr, name=name)
    #     db.session.add(dept)

    # db.session.commit()

    # # TODO: after dept database created
    # depts = [dept.abr for dept in Dept.query.all()][0:9]
    # print("Fetching courses--------------------------------------------")
    # c_info = fetch_course_info(depts)

    # for course in c_info:

    #     dept_id = Dept.query.filter_by(abr=course.get("dept")).first().id

    #     ecis = course.get("ecis")
    #     c_obj = Course(num=course.get("num"), name=course.get("name"), dept_id=dept_id, description="")

    #     db.session.add(c_obj)
    #     db.session.commit()

    #     for dept, c_num, students, avg in ecis:
    #         c_score = ECIS_Course_Score(avg=avg, students=students, dept_id=dept_id, course_id=c_obj.id)
    #         db.session.add(c_score)

    #     db.session.commit()


    # print("Fetching profs---------------------------------------------")
    # p_info = fetch_prof_info(depts)
    # for prof in p_info:

    #     p = Prof(name=prof.get("name"))
    #     db.session.add(p)
    #     db.session.commit()

    #     ecis = prof.get("ecis")
    #     for dept, c_num, students, avg in ecis:
            

    #         dept_id = Dept.query.filter_by(abr=dept).first().id
    #         c = Course.query.filter_by(num=c_num, dept_id=dept_id).all()
            
    #         if len(c) > 0:

    #             c = c[0]

    #             if Prof_Course.query.filter_by(prof_id=p.id, course_id=c.id):
                    
    #                 p_score = ECIS_Prof_Score(c_num=c_num, avg=avg, students=students, dept_id=dept_id, prof_id=p.id)
    #                 db.session.add(p_score)
    #                 db.session.commit()

    #                 pc = Prof_Course(prof_id=p.id, course_id=c.id)
    #                 db.session.add(pc)
    #                 db.session.commit()


    app.run(debug=True)
