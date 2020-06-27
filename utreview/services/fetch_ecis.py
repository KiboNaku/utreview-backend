
import pandas as pd


KEY_UNIQUE_NUM = "unique_num"
KEY_COURSE_AVG = "course_avg"
KEY_PROF_AVG = "prof_avg"
KEY_NUM_STUDENTS = "num_students"
KEY_YR = "year"
KEY_SEM = "semester"


def parse_ecis_excel(file_path, sheet_lst):
	"""Parse the ecis excel document for ecis information on courses and professors

	Args:
		file_path (str): file path to ecis excel documents
		sheet_lst (list[str]): list of sheet names to parse

	Returns:
		list[dict[str, int]]: dictionary containing course and prof ecis information
			Structure: [
				{
					KEY_UNIQUE_NUM: int,
					KEY_COURSE_AVG: int,
					KEY_PROF_AVG: int,
					KEY_NUM_STUDENTS: int,
					KEY_YR: int,
					KEY_SEM: int,
				}, ...
			]
	"""

	__sem_key = 'SEMESTER_CCYYS'
	__unique_key = 'UNIQUE'
	__num_students_key = 'NBR_SURVEY_FORMS_RETURNED'
	__course_avg_key = 'AVG_COURSE_RATING'
	__prof_avg_key = 'AVG_INSTRUCTOR_RATING'

	ecis_lst = []

	for sheet in sheet_lst:

		rows_skipped = 0

		ecis_df = pd.read_excel(file_path, sheet_name=sheet)
		for index, row in ecis_df.iterrows():
			
			yr_sem = str(row[__sem_key])
			if len(yr_sem) < 5:
				rows_skipped += 1
				continue

			yr = yr_sem[0:4]
			sem = yr_sem[5]

			unique_num = 0
			num_students = 0
			course_avg = 0
			prof_avg = 0
			
			# convert everything to int --> if N/A then fail and skip
			try:
				yr = int(yr)
				sem = int(sem)
				unique_num = int(row[__unique_key])
				num_students = int(row[__num_students_key])
				course_avg = int(row[__course_avg_key])
				prof_avg = int(row[__prof_avg_key])
			except ValueError:
				rows_skipped += 1
				continue

			# TODO: add course and prof relationship once available
			ecis = {
				KEY_UNIQUE_NUM: unique_num,
				KEY_COURSE_AVG: course_avg, 
				KEY_PROF_AVG: course_avg, 
				KEY_NUM_STUDENTS: num_students, 
				KEY_YR: yr, 
				KEY_SEM: sem
			}

			ecis_lst.append(ecis)

		print(f'Finished parsing {sheet} sheet: num_rows_skipped={rows_skipped}')	

	return ecis_lst
