
import pandas as pd

from bs4 import BeautifulSoup as BSoup

from .fetch_web import fetch_html
from utreview.services.logger import logger


def fetch_prof(query):
    """
    Fetch professor name and eid from UT directory website
    :param query: professor query to search on site
    :type query: str
    :return: name and eid of professor in format: (name, eid)
    :rtype: tuple(str, str)
    """
    logger.debug(f"Fetching Prof: {query}")

    __name_tag = "Name"
    __eid_tag = "UT EID"

    name = None
    eid = None

    # fetch html from link, if None, cannot continue
    html = fetch_html('https://directory.utexas.edu/index.php?q='
                      f'{query}'
                      '&scope=faculty%2Fstaff&submit=Search')

    if html is None:
        logger.debug("Failed to fetch professor data: html is None")
        return None, None

    soup = BSoup(html, "html.parser")

    # search for data using the html elements surrounding ti
    prof_info_table = soup.find("table", {"class": "dir_info"})
    if prof_info_table is None:
        logger.debug("Failed to fetch professor data: professor info table does not exist")
        return None, None
    prof_info_table = prof_info_table.findAll("tr")
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


def parse_prof_csv(file_path):
    """
    Parse .csv file containing prof data
    :param file_path: path to prof file
    :type file_path: str
    :return: sorted list of prof data
    :rtype: list(tuple(str, str, str))
    """

    __key_sem = 'CCYYS'
    __key_prof_name = 'INSTR_NAME'
    __key_prof_eid = 'INSTR_EID'

    logger.info(f'Parsing prof csv file: {file_path}')
    df = pd.read_csv(file_path)
    profs = set()
    for index, row in df.iterrows():
        
        semester, name, eid = row[__key_sem], row[__key_prof_name], row[__key_prof_eid]
        try:
            semester = int(semester)
        except ValueError:
            logger.debug(f'Unable to parse semester {semester}. Defaulting to 0...')
            semester = 0

        profs.add((semester, name.lower(), eid.lower()))
    
    profs = sorted(list(profs), key=lambda x: x[0])
    return profs
