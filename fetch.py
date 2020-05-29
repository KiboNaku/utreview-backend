
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
    # courses = c_soup.findAll("tr", {"class": ["tboff", "tbon"]})

    # for i in range(3):

    #     info = course.findAll("td")
    #     sem = info[0].text
    #     dept = info[1].text
    #     c_num = info[2].text
    #     c_name = info[3].text
    #     ecis = info[7].a["href"]
    #     print(sem, dept, c_num, c_name, ecis)

    depts = c_soup.find("select", {"id": "id_department"}).findAll("option")[1::]
    depts = [dept["value"].strip() for dept in depts]
    print(depts)

fetch_depts()
