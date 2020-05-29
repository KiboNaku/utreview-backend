
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
            f'&department={dept.replace(" ", "+")}'
            f'&course_number={c_num}'
            f'&course_title={c_title.replace(" ", "+")}'
            f'&unique={u_num}'
            f'&instructor_first={inst_first.replace(" ", "+")}'
            f'&instructor_last={inst_last.replace(" ", "+")}'
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
            c_info = collapse_course_info(info, courses=f_courses)

            if c_info is not None:
                f_courses.append(c_info)

    return f_courses

            


def collapse_course_info(info, courses=[]):

    dept = info[1].text
    c_num = info[2].text
    c_name = info[3].text

    for course in courses:
        if course.get("dept") == dept and course.get("c_num") == c_num:
            return None
    
    ecis_search = ("http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?s_in_action_sw=S&s_in_search_type_sw=C&s_in_max_nbr_return=10&"
                f"s_in_search_course_dept={dept.replace(' ', '+')}&s_in_search_course_num={c_num}")
    ecis = fetch_ecis_scores(ecis_search)
    
    return {
        "dept": dept,
        "c_num": c_num,
        "c_name": c_name,
        "ecis": ecis
    }


def fetch_ecis_scores(url, scores=[]):
    
    print(url)
    html = fetch_html(url)
    soup = BSoup(html, "html.parser")

    ecis_links = soup.findAll("tr")[1::]
    ecis_links = [ecis_link.find("a")["href"] for ecis_link in ecis_links]

    for ecis_link in ecis_links:

        ecis_html = fetch_html(f"http://utdirect.utexas.edu/ctl/ecis/results/{ecis_link}")
        ecis_soup = BSoup(ecis_html, "html.parser")
        ecis_info = ecis_soup.findAll("tr")[2].findAll("td")

        scores.append(((int(ecis_info[1].text)), float(ecis_info[2].text)))

    next_page = soup.find("div", {"class": "page-forward"})
    
    if next_page is None: 
        return scores
    
    np_info = next_page.findAll("input", {"type":"hidden"})
    np_link = "http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?" + "&".join(i["name"].replace(" ", "+") + "=" + i["value"].replace(" ", "+") for i in np_info)
    return fetch_ecis_scores(np_link)


def print_all_courses():
    courses = fetch_course_info()
    for course in courses:

        ecis = course.get("ecis")
        score = 0
        num_students = 0

        for s, n in ecis:
            score += s
            num_students += n

        print(course.get("dept"), course.get("c_num"), course.get("c_name"), str(score/num_students), str(num_students), sep="\t")
