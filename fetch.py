from urllib.request import urlopen
from bs4 import BeautifulSoup as BSoup

c_url = 'https://utdirect.utexas.edu/apps/student/coursedocs/nlogon/?semester=20202&department=&course_number=&course_title=&unique=&instructor_first=&instructor_last=&course_type=In+Residence&search=Search'

# opening connection
c_client = urlopen(c_url)
c_html = c_client.read()
c_client.close()

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
depts = [dept["value"] for dept in depts]
print(depts)
