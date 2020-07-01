import pandas as pd

# fetch_courses keys
KEY_DEPT = "dept"
KEY_NUM = "num"
KEY_TITLE = "title"
KEY_DESCRIPTION = "description"
KEY_RESTRICTION = "restriction"
KEY_TOPIC_NUM = "topic_num"
KEY_PRE_REQ = "pre_req"

def fetch_courses(file_name, sheet_lst):
	"""Parse the course info excel sheet 

	Args:
		df ([type]): [description]

	Returns:
		[type]: [description]
	"""
	courses = []

	for sheet_name in sheet_lst:
			
		df = pd.read_excel(
			file_name, sheet_name=sheet_name)
		df.reset_index()


		for index, row in df.iterrows():

			__field_of_study = "Field of Study"
			__course_num = "Course Number"
			__catalog_title = "Catalog Title"
			__description = "Subject Matter Description"
			__restriction = "Restrictive Statement"
			__topic_num = "Topic Number"
			__pre_req = "Prerequisites"

			course = {
				KEY_DEPT: row[__field_of_study].strip(),
				KEY_NUM: row[__course_num].strip(),
				KEY_TITLE: row[__catalog_title].strip()[:-1],
				KEY_DESCRIPTION: row[__description].strip(),
				KEY_RESTRICTION: row[__restriction].strip(),
				KEY_TOPIC_NUM: parse_topic(row[__topic_num]),
				KEY_PRE_REQ: row[__pre_req].strip()
			}
			courses.append(course)
	return courses


def fetch_dept_info(file_name, sheet_lst):

	depts = set()

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
			depts.add(dept)
	
	return sorted(list(depts))


def parse_topic(topic_num):

	try:
		return int(topic_num.strip())
	except ValueError:
		return -1
