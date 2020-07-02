from fetch import fetch_html
from bs4 import BeautifulSoup as BSoup

def get_prof_name(eid):

    html = fetch_html('https://directory.utexas.edu/index.php?q='
                        f'{eid}'
                        '&scope=faculty%2Fstaff&submit=Search')

    if html is None:
        return []

    soup = BSoup(html, "html.parser")

    name = soup.select("td:nth-of-type(2)", limit=1)

    return name