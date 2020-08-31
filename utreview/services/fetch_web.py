
import json

from bs4 import BeautifulSoup as BSoup
from titlecase import titlecase
from urllib.request import urlopen, http

from utreview.services.logger import logger

# ProfCourse dictionary keys
KEY_SEM = 'sem'
KEY_DEPT = 'dept'
KEY_TITLE = 'title'
KEY_CNUM = 'cnum'
KEY_UNIQUE = 'unique'
KEY_PROF = 'prof'

# contains a list of failed requests
failed_requests = []

"""
Old file used to scrape data from UT sites (not recommended).
"""


def fetch_html(url, attempt=1):
    """
    Fetch html from the provided url
    :param url: link to site to fetch
    :type url: str
    :param attempt: attempt number for the url
    :type attempt: int
    :return: html object pertaining to the url
    """

    logger.debug("fetching: ", url)
    __max_attempts = 10

    try:
        client = urlopen(url)
        html = client.read()
        client.close()
    except http.client.HTTPException:

        logger.debug(f"URL Failed: {url}, Attempt Number: {attempt}")
        if attempt >= __max_attempts:
            failed_requests.append(url)
            return None
        return fetch_html(url, attempt+1)
    return html


def get_course_url(sem="spring", year=2020, dept="", c_num="", c_title="", u_num="", inst_first="", inst_last=""):
    """
    Generate url to site with syllabi/cvs data
    Also contains data for professor, course, and unique number, separated by semester
    :param sem: semester to search. Valid values: 'spring', 'summer', 'fall'
    :type sem: str
    :param year: year to search
    :type year: int
    :param dept: department to search
    :type dept: str
    :param c_num: course number to search
    :type c_num: str
    :param c_title: course title to search
    :type c_title: str
    :param u_num: unique number to search
    :type u_num: str
    :param inst_first: instructor first name to search
    :type inst_first: str
    :param inst_last: instructor last name to search
    :type inst_last: str
    :return: url to site
    :rtype: str
    """

    if sem == "spring":
        sem_num = 2
    elif sem == "summer":
        sem_num = 6
    elif sem == "fall":
        sem_num = 9
    else:
        logger.debug(f"Cannot parse semester: {sem}. Defaulting to spring...")
        sem_num = 2

    return ('https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/?'
            f'semester={year}{sem_num}'
            f'&department={dept.replace(" ", "+")}'
            f'&course_number={c_num}'
            f'&course_title={c_title.replace(" ", "+")}'
            f'&unique={u_num}'
            f'&instructor_first={inst_first.replace(" ", "+")}'
            f'&instructor_last={inst_last.replace(" ", "+")}'
            '&course_type=In+Residence&search=Search')


def get_prof_course_url(semester="20202", department="E E"):
    """
    Generate url to site containing prof course mapping
    :param semester: semester to search
    :type semester: str
    :param department: department to seatch
    :type department: str
    :return: url to the site
    :rtype: str
    """
    department = department.replace(" ", "+")
    return ("https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/?"
            f"semester={semester}&department={department}&course_number=&course_title=&"
            "unique=&instructor_first=&instructor_last=&course_type=In+Residence&course_type=Extension&search=Search")


def fetch_prof_course_info(out_file, sems, depts):
    """
    Parse prof course info from the site -> for the relationship
    :param out_file: file to output the relationships/data
    :type out_file: str
    :param sems: semesters to fetch data for
    :type sems: list[str]
    :param depts: departments to fetch data for
    :type depts: list[str]
    """
    __sem_header = 'SEMESTER'
    __dept_header = 'DEPT'
    __title_header = 'TITLE'
    __course_num_header = 'COURSENUMBER'
    __unique_header = 'UNIQUE'
    __instr_header = 'INSTRUCTOR(S)*'

    logger.info(f"Fetching prof_course info. Output={out_file}. Semesters={sems}. Departments={depts}")

    for sem in sems:
        for dept in depts:

            # get BeautifulSoup object for the parameters
            html = fetch_html(get_prof_course_url(sem, dept))
            html_soup = BSoup(html, "html.parser")

            # look for headers on page -> headers for the table
            headers = html_soup.find("tr", {"class": "tbh header"})
            if headers is None:
                logger.debug("Cannot find headers for prof_course search: "
                             f"Semester={sem}, Department={dept}. Skipping...")
                continue
            headers = [header.text.replace("\n", "").strip() for header in headers.findAll("th")]
            logger.debug(f"Fetched headers from profcourse site with headers: {headers}")

            # parse out indices for each of the headers
            sem_index, dept_index, title_index, cnum_index, unique_index, instr_index = get_header_indices(
                headers,
                __sem_header,
                __dept_header,
                __title_header,
                __course_num_header,
                __unique_header,
                __instr_header
            )

            # iterate through each row in the web table and parse out data
            rows = html_soup.findAll("tr", {"class": ["tboff", "tbon"]})
            for row in rows:
                cols = row.findAll("td")
                cols = [col.text.replace("\n", "").strip() for col in cols]

                # get data via the indices for the headers
                for i in range(len(cols)):
                    if 'CV' in cols[i]:
                        cols[i] = cols[i].split('CV')[0].strip()

                # create dictionary containing the data
                prof_course = {
                    KEY_SEM: cols[sem_index] if sem_index is not None else None,
                    KEY_DEPT: cols[dept_index] if dept_index is not None else None,
                    KEY_TITLE: cols[title_index].strip()[:-1] if title_index is not None else None,
                    KEY_CNUM: cols[cnum_index] if cnum_index is not None else None,
                    KEY_UNIQUE: cols[unique_index] if unique_index is not None else None,
                    KEY_PROF: cols[instr_index] if instr_index is not None else None
                }

                # write dictionary to file
                with open(out_file, "a") as f:
                    json.dump(prof_course, f)
                    f.write("\n")
    

def fetch_prof_course_sem_depts():
    """
    From the professor course site, fetch lists of the semesters and departments available
    :return: list of semesters and departments (semesters, departments)
    :rtype: tuple(list[str], list[str])
    """
    
    base_html = fetch_html("https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/")
    if base_html is None:
        logger.debug("Failed to fetch prof_course semester and department lists")
        return None
    
    base_soup = BSoup(base_html, "html.parser")
    sems = parse_prof_course_sems(base_soup)[1:]
    depts = parse_prof_course_depts(base_soup)[1:]

    return sems, depts


def get_header_indices(headers, *header_vals):
    """
    Provided a list of headers and some headers, find the indices for each of the second set of headers
    :param headers: list of headers to search through
    :type headers: list[str]
    :param header_vals: list of headers to find indices for
    :return: a tuple of indices for the headers
    :rtype: list[int]
    """
    indices = []
    for header in header_vals:
        try:
            index = headers.index(header)
            indices.append(index)
        except ValueError:
            logger.debug(f"Cannot find index for: {header}")
            indices.append(None)
    return tuple(indices)


def parse_prof_course_depts(base_soup):
    """
    Parse out a list of departments from the beautiful soup object
    :param base_soup: object containing department list
    :type base_soup: BeautifulSoup
    :return: list of departments
    :rtype: list[str]
    """
    return [option['value']
            for option in base_soup.find("select", {"id": "id_department"}).findAll("option", value=True)]


def parse_prof_course_sems(base_soup):
    """
    Parse out a list of semesters from the beautiful soup object
    :param base_soup: object containing semester list
    :type base_soup: BeautifulSoup
    :return: list of semesters
    :rtype: list[str]
    """
    return [option['value']
            for option in base_soup.find("select", {"id": "id_semester"}).findAll("option", value=True)]


def fetch_depts():
    """
    Fetch list of departments from the site
    :return: list of departments at UT Austin
    :rtype: list[str]
    """
    c_html = fetch_html('https://registrar.utexas.edu/staff/fos')

    if c_html is None:
        return []

    c_soup = BSoup(c_html, "html.parser")

    dept_dl_group = c_soup.find("div", {"class": "field body"}).findAll("dl")
    dept_abrs = [dt.text.strip() for dl in dept_dl_group for dt in dl.findAll("dt")]
    dept_names = [
        dd.text.strip().replace('-', ' ') 
        for dl in dept_dl_group 
        for dd in dl.findAll("dd")
        ]
    dept_names = [titlecase(name) for name in dept_names]

    if len(dept_abrs) != len(dept_names):
        # print("Unexpected Error for Dept: number of abr does not equal number of names. Failed fetch")
        return None
    
    depts = [(dept_abrs[i], dept_names[i]) for i in range(len(dept_abrs))]

    return depts


# -------------Below contains functions no longer in use---------------
# Initial use: fetching course and professor data from UT website
# Problem: too many requests causes warnings to go off for their security
def fetch_course_info(depts, sem="spring", year=2020):

    f_courses = []

    # fetching courses for each department
    for dept in depts:

        c_html = fetch_html(get_course_url(sem=sem, year=year, dept=dept))

        if c_html is not None:

            c_soup = BSoup(c_html, "html.parser")

            courses = c_soup.findAll("tr", {"class": ["tboff", "tbon"]})

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

            # fetching information for each course in the department
            for course in courses:

                info = course.findAll("td")

                my_info = collapse_prof_info(info, profs=f_profs)

                if my_info is not None:
                    f_profs.append(my_info)

    return f_profs


def collapse_prof_info(info, profs=None):

    p_name = info[5]

    for child in p_name.findAll("span"):
        child.decompose()
    p_name = p_name.text.strip()

    if profs is not None:
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


def collapse_course_info(dept, info, courses=None):

    c_num = info[2].text
    c_name = info[3].text

    if courses is not None:
        for course in courses:
            if course.get("dept") == dept and course.get("num") == c_num:
                return None

    ecis_search = ("http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?"
                   "s_in_action_sw=S&s_in_search_type_sw=C&s_in_max_nbr_return=10&"
                   f"s_in_search_course_dept={dept.replace(' ', '+')}&s_in_search_course_num={c_num}")
    ecis = fetch_ecis_scores(ecis_search, scores=[])

    return {
        "dept": dept,
        "num": c_num,
        "name": c_name,
        "ecis": ecis
    }


def fetch_ecis_scores(url, scores=None, c_mode=True):

    if scores is None:
        scores = []

    html = fetch_html(url)
    if html is None:
        return scores

    soup = BSoup(html, "html.parser")

    ecis_links = soup.findAll("tr")[1::]
    ecis_links = [(ecis_link.find("a")["href"], ecis_link.findAll(
        "td")[1].text) for ecis_link in ecis_links]

    for ecis_link, name in ecis_links:

        ecis_html = fetch_html(
            f"http://utdirect.utexas.edu/ctl/ecis/results/{ecis_link}")

        if ecis_html is not None:
            ecis_soup = BSoup(ecis_html, "html.parser")
            ecis_info = ecis_soup.findAll(
                "tr")[2 if c_mode else 1].findAll("td")

            score = (name[0:3:], name[3::], int(
                ecis_info[1].text), float(ecis_info[2].text))
            scores.append(score)

    next_page = soup.find("div", {"class": "page-forward"})

    if next_page is None:
        return scores

    np_info = next_page.findAll("input", {"type": "hidden"})
    np_link = "http://utdirect.utexas.edu/ctl/ecis/results/index.WBX?" + \
        "&".join(i["name"].replace(" ", "+") + "=" +
                 i["value"].replace(" ", "+") for i in np_info)
    return fetch_ecis_scores(np_link, scores=scores)
