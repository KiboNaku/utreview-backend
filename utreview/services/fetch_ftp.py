
from os import chdir
from os.path import join, isfile
from ftplib import FTP


filename_current = 'Current_Semester_Report'
filename_next = 'Next_Semester_Report'
filename_future = 'Future_Semester_Report'


def fetch_ftp_files(out_dir):
	"""Downloads ftp files from UT Austin FTP server

	Args:
		out_dir (str): directory to download files to
	"""
	__url = 'reg-it.austin.utexas.edu'
	__username = 'anonymous'

	ftp = FTP(__url)
	ftp.login(user=__username)

	chdir(out_dir)
	for filename in (filename_current, filename_next, filename_future):

		print(f'FTP: downloading {filename}')
		localfile = open(filename, 'wb')
		ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
		localfile.close()
	
	ftp.quit()


def parse_ftp(in_dir):
	"""Parse FTP files from the UT Austin FTP server

	Args:
		in_dir (str): directory containinig the ftp files
	"""

	file_dict = {}

	for filename in (filename_current, filename_next, filename_future):

		filepath = join(in_dir, filename)
		courses = []

		if isfile(filepath):

			print(f'FTP: parsing {filename}')
			with open(filepath) as f:

				lines = f.readlines()
				categories, lines = __parse_categories(lines)
				
				if categories is not None:

					for line in lines:

						line = line.lower()
						data = line.split("\t")
						data = [d.strip() for d in data]

						if len(line) > 0 and len(data) >= len(categories):

							course = {categories[i]: data[i] for i in range(len(categories))}
							courses.append(course)
		else:
			print(f'FTP: {filename} does not exist in {in_dir}')

		file_dict[filename] = courses
	
	return file_dict


def __parse_categories(ftp_lines):

	line_num = 0

	for line in ftp_lines:

		line_num += 1

		line = line.lower()

		if "year" in line.lower():

			categories = line.lower().split("\t")
			categories = [category.strip() for category in categories if len(category.strip()) > 0]
			
			return categories, ftp_lines[line_num:]
	
	return None, ftp_lines
