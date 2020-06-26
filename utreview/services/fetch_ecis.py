
import pandas as pd

from utreview import db
from utreview.models.ecis import EcisCourseScore, EcisProfScore


def parse_ecis_excel(file_path, sheet_lst):

	__sem_key = 'SEMESTER_CCYYS'
	__num_students_key = 'NBR_SURVEY_FORMS_RETURNED'
	__course_avg_key = 'AVG_COURSE_RATING'
	__prof_avg_key = 'AVG_INSTRUCTOR_RATING'

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

			num_students = 0
			course_avg = 0
			prof_avg = 0
			
			try:
				num_students = int(row[__num_students_key])
				course_avg = int(row[__course_avg_key])
				prof_avg = int(row[__prof_avg_key])
			except ValueError:
				rows_skipped += 1
				continue

			# add course and prof relationship once available
			course_ecis = EcisCourseScore(
				avg=course_avg, 
				num_students=num_students, 
				year=yr, 
				semester=sem
				)
			prof_ecis = EcisProfScore(
				avg=course_avg, 
				num_students=num_students, 
				year=yr, 
				semester=sem,
				)

			db.session.add(course_ecis)
			db.session.add(prof_ecis)
			db.session.commit()

		print(f'Finished parsing {sheet} sheet: num_rows_skipped={rows_skipped}')				
