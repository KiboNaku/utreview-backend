
import pandas as pd

from utreview.services.logger import logger


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
					KEY_COURSE_AVG: float,
					KEY_PROF_AVG: float,
					KEY_NUM_STUDENTS: int,
					KEY_YR: int,
					KEY_SEM: int,
				}, ...
			]
	"""

	__unique_num_digits = 5
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

			# check for valid year semester string. If invalid, skip
			yr_sem = str(row[__sem_key])
			if len(yr_sem) < 5:
				rows_skipped += 1
				continue

			yr_sem = yr_sem[0:5]
			yr = yr_sem[0:-1]
			sem = yr_sem[-1]

			# convert everything to int or float--> if N/A then fail and skip
			try:

				unique_str = str(row[__unique_key])
				unique_str = unique_str.split('.')[0] if '.' in unique_str else unique_str

				num_students_str = str(row[__num_students_key])
				num_students_str = num_students_str.split('.')[0] if '.' in num_students_str else num_students_str
		
				yr = int(yr)
				sem = int(sem)
				unique_num = int(unique_str)
				num_students = int(num_students_str)
				course_avg = float(row[__course_avg_key])
				prof_avg = float(row[__prof_avg_key])
			except (ValueError, IndexError):
				rows_skipped += 1
				continue

			# TODO: add course and prof relationship once available
			# create ecis dictionary
			ecis = {
				KEY_UNIQUE_NUM: unique_num,
				KEY_COURSE_AVG: course_avg, 
				KEY_PROF_AVG: prof_avg,
				KEY_NUM_STUDENTS: num_students, 
				KEY_YR: yr, 
				KEY_SEM: sem
			}

			ecis_lst.append(ecis)

		logger.info(f'Finished parsing {sheet} sheet: num_rows_skipped={rows_skipped}')

	return ecis_lst
