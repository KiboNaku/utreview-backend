
from os import chdir
from os.path import join, isfile
from ftplib import FTP


__filename_current = 'Current_Semester_Report'
__filename_next = 'Next_Semester_Report'
__filename_future = 'Future_Semester_Report'


def fetch_ftp_files(out_dir):

	__url = 'reg-it.austin.utexas.edu'
	__username = 'anonymous'

	ftp = FTP(__url)
	ftp.login(user=__username)

	chdir(out_dir)
	for filename in (__filename_current, __filename_next, __filename_future):

		print(f'FTP: downloading {filename}')
		localfile = open(filename, 'wb')
		ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
		localfile.close()
	
	ftp.quit()


def parse_ftp(in_dir):

	for filename in (__filename_current, __filename_next, __filename_future):

		filename = join(in_dir, filename)

		if not isfile(filename):
			print(f'FTP: {filename} does not exist')
			continue

		print(f'FTP: parsing {filename}')
		with open(filename) as f:
			lines = f.readlines()

		parse_data = False

		categories = []
		courses = []

		for line in lines:


			if (not parse_data) and ("year" in line.lower()):
			
				parse_data = True

				categories = line.lower().split("\t")
				categories = [category.strip() for category in categories if len(category.strip()) > 0]
				
				continue

			if parse_data and len(line.strip()) > 0:

				data = line.lower().split("\t")
				data = [d.strip() for d in data]

				course = {categories[i]: data[i] for i in range(len(categories))}
				courses.append(course)