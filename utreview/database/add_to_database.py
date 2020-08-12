
from utreview import logger
from utreview.models.course import *
from utreview.models.ecis import *
from utreview.models.others import *
from utreview.models.prof import *


def check_or_add_prof(first_name, last_name):
    """
    Checks if the provided professor exists in the database.
    If it does, nothing happens.
    If it doesn't, add the said professor
    :param first_name: first name of professor
    :type first_name: str
    :param last_name: last name of professor
    :type last_name: str
    :return: results of the search as a tuple(number of results, Prof object containing the info requested)
    :rtype: tuple(int, Prof)
    """

    prof = Prof.query.filter_by(first_name=first_name, last_name=last_name)
    num_results = len(prof.all())
    prof = prof.first()
    if prof is None:
        logger.debug(f"Adding new prof: {first_name} {last_name}")
        prof = Prof(first_name=first_name, last_name=last_name)
        db.session.add(prof)
        db.session.commit()
    return num_results, prof


def check_or_add_course(dept, num, title):
    """
    Checks if the provided course exists in the database.
    If it does, nothing happens.
    If it doesn't, add the said course
    :param dept: department of the course
    :type dept: Dept
    :param num: course number
    :type num: str
    :param title: title of the course
    :type title: str
    :return: results of the search as a tuple(number of results, Course object containing the info requested)
    :rtype: tuple(int, Course)
    """

    course = Course.query.filter_by(dept_id=dept.id, num=num)
    num_results = len(course.all())
    course = course.first()
    if course is None:
        logger.debug(f'Adding new course: {dept.abr} {num}')
        course = Course(dept_id=dept.id, num=num, title=title)
        db.session.add(course)
        db.session.commit()
    return num_results, course


def check_or_add_prof_course(prof, course):
    """
    Checks if the provided prof_course relationship exists in the database.
    If it does, nothing happens.
    If it doesn't, add the said prof_course
    :param prof: professor for the relationship
    :type prof: Prof
    :param course: course for the relationship
    :type course: Course
    :return: results of the search as a tuple(number of results, Prof_Course object containing the info requested)
    :rtype: tuple(int, ProfCourse)
    """
    prof_course_obj = ProfCourse.query.filter_by(prof_id=prof.id, course_id=course.id)
    num_results = len(prof_course_obj.all())
    prof_course_obj = prof_course_obj.first()
    if prof_course_obj is None:
        logger.debug(f'Adding new prof_course: {prof} {course}')
        prof_course_obj = ProfCourse(prof_id=prof.id, course_id=course.id)
        db.session.add(prof_course_obj)
        db.session.commit()
    return num_results, prof_course_obj


def check_or_add_semester(yr, sem):
    """
    Checks if the provided semester exists in the database.
    If it does, nothing happens.
    If it doesn't, add the said semester
    :param yr: semester year
    :type yr: int
    :param sem: semester integer (view utreview's __init__.py to view corresponding integers)
    :type sem: int
    :return: results of the search as a tuple(number of results, Semester object containing the info requested)
    :rtype: tuple(int, Semester)
    """
    sem_obj = Semester.query.filter_by(year=yr, semester=sem)
    num_results = len(sem_obj.all())
    sem_obj = sem_obj.first()
    if sem_obj is None:
        logger.debug(f'Adding new Semester: {yr} {sem}')
        sem_obj = Semester(year=yr, semester=sem)
        db.session.add(sem_obj)
        db.session.commit()
    return num_results, sem_obj


def check_or_add_prof_course_semester(unique_num, prof_course, semester):
    """
    Checks if the provided prof_course_semester exists in the database.
    If it does, nothing happens.
    If it doesn't, add the said prof_course_semester
    :param unique_num: unique number for the prof_course_semester
    :type unique_num: int
    :param prof_course: prof_course object for the given relationship
    :type prof_course: ProfCourse
    :param semester: semester object for the given relationship
    :type semester: Semester
    :return: results of the search as a tuple(number of results, ProfCourseSemester object containing the info requested)
    :rtype: tuple(int, ProfCourseSemester)
    """
    prof_course_sem_obj = ProfCourseSemester.query.filter_by(
        unique_num=unique_num, prof_course_id=prof_course.id, sem_id=semester.id
    )
    num_results = len(prof_course_sem_obj.all())
    prof_course_sem_obj = prof_course_sem_obj.first()
    if prof_course_sem_obj is None:
        logger.debug(
            f'Adding new prof_course_semester: unique={unique_num}, semester={semester.year} {semester.semester}'
        )
        prof_course_sem_obj = ProfCourseSemester(
            unique_num=unique_num, prof_course_id=prof_course.id, sem_id=semester.id
        )
        db.session.add(prof_course_sem_obj)
        db.session.commit()
    return num_results, prof_course_sem_obj
