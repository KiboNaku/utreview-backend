import pandas as pd

KEY_DEPT = "dept"
KEY_NUM = "num"
KEY_TITLE = "title"
KEY_DESCRIPTION = "description"
KEY_RESTRICTION = "restriction"
KEY_TOPIC_NUM = "topic_num"
KEY_PRE_REQ = "pre_req"


def fetch_courses(file_name, sheet_name):
	"""Parse the course info excel sheet 

	Args:
		df ([type]): [description]

	Returns:
		[type]: [description]
	"""
	df = pd.read_excel(
		file_name, sheet_name=sheet_name)
	df.reset_index()

	courses = []
	count = 0
	topic_counter = [0]

	for index, row in df.iloc[70:100].iterrows():

		__field_of_study = "Field of Study"
		__course_num = "Course Number"
		__catalog_title = "Catalog Title"
		__description = "Subject Matter Description"
		__restriction = "Restrictive Statement"
		__topic_num = "Topic Number"
		__pre_req = "Prerequisites"

		course = {
			KEY_DEPT: row[__field_of_study],
			KEY_NUM: row[__course_num],
			KEY_TITLE: row[__catalog_title],
			KEY_DESCRIPTION: row[__description],
			KEY_RESTRICTION: row[__restriction],
			KEY_TOPIC_NUM: parse_topic(row[__topic_num], topic_counter),
			KEY_PRE_REQ: row[__pre_req]
		}
		courses.append(course)
	return courses


def parse_topic(topic_num, topic_counter):

	__none = ' N/A '
	__parent = ' 000 '

	if topic_num == __none:
		topic_num = -1
	elif topic_num == __parent:
		topic_num = 0
		topic_counter[0] = 0
	else:
		topic_counter[0] += 1
		topic_num = topic_counter[0]

	return topic_num
