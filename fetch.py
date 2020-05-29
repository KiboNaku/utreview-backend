
from urllib.request import urlopen
from bs4 import BeautifulSoup as BSoup


def fetch_html(url):

    client = urlopen(url)
    html = client.read()
    client.close()

    return html


def get_course_url(sem="spring", year=2020, dept="", c_num="", c_title="", u_num="", inst_first="", inst_last=""):

    sem_num = 2
    if sem == "summer":
        sem_num = 6
    elif sem == "fall":
        sem_num = 9

    return ('https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/?'
            f'semester={year}{sem_num}'
            f'&department={dept}'
            f'&course_number={c_num}'
            f'&course_title={c_title}'
            f'&unique={u_num}'
            f'&instructor_first={inst_first}'
            f'&instructor_last={inst_last}'
            '&course_type=In+Residence&search=Search')


def fetch_depts():

    c_html = fetch_html(get_course_url())
    c_soup = BSoup(c_html, "html.parser")

    depts = c_soup.find("select", {"id": "id_department"}).findAll("option")[1::]
    depts = [dept["value"].strip() for dept in depts]
    
    return depts


def fetch_course_info(sem="spring", year=2020):

    f_courses = []
    depts = fetch_depts()

    # fetching courses for each department
    for dept in depts:

        c_html = fetch_html(get_course_url(sem=sem, year=year, dept=dept))
        c_soup = BSoup(c_html, "html.parser")
        
        courses = c_soup.findAll("tr", {"class": ["tboff", "tbon"]})

        # fetching information for each course in the department
        for course in courses:

            prev = None
            info = course.findAll("td")
            


def collapse_course_info(info):

    dept = info[1].text
    c_num = info[2].text
    c_name = info[3].text
    ecis_url = info[7].a["href"]
    
    ecis = fetch_ecis_score(ecis_url)

    return {
        "dept": dept,
        "c_num": c_num,
        "c_name": c_name,
        "ecis": ecis
    }



def fetch_ecis_score(url):
    
    html = fetch_html(url)
    soup = BSoup(html, {"html.parser"})

    


fetch_course_info()
