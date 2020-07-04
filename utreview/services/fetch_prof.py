from .fetch_web import fetch_html
from bs4 import BeautifulSoup as BSoup

def fetch_prof(query):

    __name_tag = "Name"
    __eid_tag = "UT EID"

    name = None
    eid = None

    html = fetch_html('https://directory.utexas.edu/index.php?q='
                        f'{query}'
                        '&scope=faculty%2Fstaff&submit=Search')

    if html is None:
        return None

    soup = BSoup(html, "html.parser")

    prof_info_table = soup.find("table", {"class": "dir_info"}).findAll("tr")
    prof_info_table = [tr.findAll("td") for tr in prof_info_table]

    for tr in prof_info_table:
        if len(tr) < 2: 
            continue
        tag = tr[0].text.strip()
        val = tr[1].text.strip()

        if __name_tag in tag:
            name = val
            name.split(",")[0].strip()
        elif __eid_tag in tag:
            eid = val

    return name, eid
    