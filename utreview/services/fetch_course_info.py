import pandas as pd

# fetch_courses keys
KEY_SEM = "sem"
KEY_DEPT = "dept"
KEY_NUM = "num"
KEY_TITLE = "title"
KEY_CS_TITLE = "cs_title"
KEY_DESCRIPTION = "description"
KEY_RESTRICTION = "restriction"
KEY_TOPIC_NUM = "topic_num"
KEY_PRE_REQ = "pre_req"


def fetch_courses(file_name, sheet_lst):
	"""
	Parse the course info from the excel sheet
	:param file_name: name of the excel sheet
	:type file_name: str
	:param sheet_lst: list of page sheets
	:type sheet_lst: list[int] or list[str]
	:return: list of dictionaries containing the course info
	:rtype: list[
		dict[
			KEY_SEM: int,
			KEY_DEPT: str,
			KEY_NUM: str,
			KEY_TITLE: str,
			KEY_CS_TITLE: str,
			KEY_DESCRIPTION: str,
			KEY_RESTRICTION: str,
			KEY_TOPIC_NUM: int,
			KEY_PRE_REQ: str
		]
	]
	"""

	courses = []

	for sheet_name in sheet_lst:
			
		df = pd.read_excel(
			file_name, sheet_name=sheet_name)
		df.reset_index()

		for index, row in df.iterrows():
			
			__sem = "Report CCYYS"
			__field_of_study = "Field of Study"
			__course_num = "Course Number"
			__catalog_title = "Catalog Title"
			__cs_title = "CS Title"
			__description = "Subject Matter Description"
			__restriction = "Restrictive Statement"
			__topic_num = "Topic Number"
			__pre_req = "Prerequisites"

			course = {
				KEY_SEM: int(row[__sem]),
				KEY_DEPT: row[__field_of_study].strip(),
				KEY_NUM: row[__course_num].strip(),
				KEY_TITLE: row[__catalog_title].strip()[:-1],
				KEY_CS_TITLE: row[__cs_title].strip(),
				KEY_DESCRIPTION: row[__description].strip(),
				KEY_RESTRICTION: row[__restriction].strip(),
				KEY_TOPIC_NUM: parse_topic(row[__topic_num]),
				KEY_PRE_REQ: row[__pre_req].strip()
			}
			courses.append(course)
	return courses


def fetch_dept_info(file_name, sheet_lst):
	"""
	Parse department info from the excel sheet provided
	:param file_name: path to excel file
	:type file_name: str
	:param sheet_lst: list of sheet names / page numbers
	:type sheet_lst: list[str] or list[int]
	:return: list of tuples containing the parsed data in order: (abbreviation, department name, college name)
	:rtype: list[tuple(str, str, str)]
	"""

	dept_set = set()
	for sheet_name in sheet_lst:
			
		df = pd.read_excel(
			file_name, sheet_name=sheet_name)
		df.reset_index()

		for index, row in df.iterrows():

			__abr = "Field of Study"
			__dept = "Department"
			__college = "College"

			dept = (
				row[__abr].strip(),
				row[__dept].strip(),
				row[__college].strip(),
			)
			dept_set.add(dept)
	
	return sorted(list(dept_set))


def parse_topic(topic_num):
	"""
	Parse topic number from the given string
	:param topic_num: topic number from excel file
	:type topic_num: str
	:return: parsed topic number (-1 by default)
	:rtype: int
	"""

	try:
		return int(topic_num.strip())
	except ValueError:
		return -1
