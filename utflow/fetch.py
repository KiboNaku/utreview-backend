
from urllib.request import urlopen, http
from bs4 import BeautifulSoup as BSoup

failed_requests = []


def fetch_html(url, attempt=1):

    print("fetching: ", url)

    MAX_ATTEMPTS = 10

    try:
        client = urlopen(url)
        html = client.read()
        client.close()
    except http.client.HTTPException as e:

        print("URL Failed:", url, "Attempt:", attempt)
        return fetch_html(url, attempt+1)

        if attempt >= MAX_ATTEMPTS:
            failed_requests.append(url)
            return None

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

    if c_html is None:
        return []

    c_soup = BSoup(c_html, "html.parser")

    depts = c_soup.find(
        "select", {"id": "id_department"}).findAll("option")[1::]
    depts = [(dept["value"], dept.text[4::].strip()) for dept in depts]

    return depts


def fetch_course_info(depts, sem="spring", year=2020):

    f_courses = []

    # fetching courses for each department
    for dept in depts:

        c_html = fetch_html(get_course_url(sem=sem, year=year, dept=dept))

        if c_html is not None:

            c_soup = BSoup(c_html, "html.parser")

            courses = c_soup.findAll("tr", {"class": ["tboff", "tbon"]})
            if len(courses) > 3:
                courses = courses[0:3:]

            # fetching information for each course in the department
            for course in courses:

                info = course.findAll("td")

                my_info = collapse_course_info(dept, info, courses=f_courses)

                if my_info is not None:
                    f_courses.append(my_info)

    return f_courses


def fetch_prof_info(depts, sem="spring", year=2020):

    f_profs = []

    # fetching courses for each department
    for dept in depts:

        c_html = fetch_html(get_course_url(sem=sem, year=year, dept=dept))

        if c_html is not None:

            c_soup = BSoup(c_html, "html.parser")

            courses = c_soup.findAll("tr", {"class": ["tboff", "tbon"]})
            if len(courses) > 3:
                courses = courses[0:3:]

            # fetching information for each course in the department
            for course in courses:

                info = course.findAll("td")

                my_info = collapse_prof_info(info, profs=f_profs)

                if my_info is not None:
                    f_profs.append(my_info)

    return f_profs


def collapse_prof_info(info, profs=[]):

    p_name = info[5]

    for child in p_name.findAll("span"):
        child.decompose()
    p_name = p_name.text.strip()

    for prof in profs:
        if prof.get("name") == p_name:
            return None

    ecis_search = ("http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?&s_in_action_sw=S&s_in_search_type_sw=N&"
                   f"s_in_search_name={p_name.replace(' ', '+').replace(',', '%2C')}")
    ecis = fetch_ecis_scores(ecis_search, scores=[], c_mode=False)

    return {
        "name": p_name,
        "ecis": ecis
    }


def collapse_course_info(dept, info, courses=[]):

    c_num = info[2].text
    c_name = info[3].text

    for course in courses:
        if course.get("dept") == dept and course.get("num") == c_num:
            return None

    ecis_search = ("http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?s_in_action_sw=S&s_in_search_type_sw=C&s_in_max_nbr_return=10&"
                   f"s_in_search_course_dept={dept.replace(' ', '+')}&s_in_search_course_num={c_num}")
    ecis = fetch_ecis_scores(ecis_search, scores=[])

    return {
        "dept": dept,
        "num": c_num,
        "name": c_name,
        "ecis": ecis
    }


def fetch_ecis_scores(url, scores=[], c_mode=True):

    html = fetch_html(url)
    if html is None:
        return scores

    soup = BSoup(html, "html.parser")

    ecis_links = soup.findAll("tr")[1::]
    ecis_links = [(ecis_link.find("a")["href"], ecis_link.findAll("td")[1].text) for ecis_link in ecis_links]

    for ecis_link, name in ecis_links:

        ecis_html = fetch_html(
            f"http://utdirect.utexas.edu/ctl/ecis/results/{ecis_link}")

        if ecis_html is not None:
            ecis_soup = BSoup(ecis_html, "html.parser")
            ecis_info = ecis_soup.findAll("tr")[2 if c_mode else 1].findAll("td")

            score = (name[0:3:], name[3::], int(ecis_info[1].text), float(ecis_info[2].text))
            scores.append(score)

    next_page = soup.find("div", {"class": "page-forward"})

    if next_page is None:
        return scores

    np_info = next_page.findAll("input", {"type": "hidden"})
    np_link = "http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?" + "&".join(i["name"].replace(" ", "+") + "=" + i["value"].replace(" ", "+") for i in np_info)
    return fetch_ecis_scores(np_link, scores=scores)


# # temporary debugging function
# def print_all_courses():

#     courses = fetch_course_info()
#     for course in courses:

#         ecis = course.get("ecis")
#         score = 0
#         num_students = 0
#         for n, s in ecis:
#             num_students += n
#             score += n*s

#         avg = "N/A"
#         if num_students > 0:
#             avg = str(score/num_students)

#         print(course.get("dept"), course.get("num"), course.get(
#             "name"), avg, str(num_students), sep="\t")

#     print("-----------Failed URLS---------")
#     for url in failed_requests:
#         print(url)


# # temporary debugging function
# def print_all_profs():
#     profs = fetch_prof_info()
#     for prof in profs:

#         ecis = prof.get("ecis")
#         score = 0
#         num_students = 0
#         for dept, c_num, n, s in ecis:
#             score += s*n
#             num_students += n

#         avg = "N/A"
#         if num_students > 0:
#             avg = str(score/num_students)

#         print(prof.get("name"), avg, str(num_students), sep="\t")

#     print("-----------Failed URLS---------")
#     for url in failed_requests:
#         print(url)

