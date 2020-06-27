import pandas as pd


# sheet_name and index_col should be default to 0
def import_file(file_name, sheet_name):
	courses = pd.read_excel(
		file_name, sheet_name=sheet_name)
	courses.reset_index()
	return courses


def fetch_courses(df, topics):
	courses = []
	count = 0
	for index, row in df.iterrows():
		# for testing
		if count > 10:
			break
		else:
			count = count+1
			# end of testing

			topic_num = row["Topic Number"]
			if topic_num == ' N/A ':
				topic_num = -1
			elif topic_num == ' 000 ':
				topic_num = 0 
			else: 
				topic_num = 3

			course = {
				"dept": row["Field of Study"],
				"num": row["Course Number"],
				"title": row["Catalog Title"],
				"description": row["Subject Matter Description"],
				"restriction": row["Restrictive Statement"],
				"topic_num": topic_num,
				"pre_req": row["Prerequisites"]
			}
			courses.append(course)
			print(course["topic_num"])
