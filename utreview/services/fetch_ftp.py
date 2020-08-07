
from os import chdir, getcwd
from os.path import join, isfile
from ftplib import FTP
import re
import json


filename_current = 'Current_Semester_Report'
filename_next = 'Next_Semester_Report'
filename_future = 'Future_Semester_Report'

# sem file name
sem_file = "semester.txt"

# keys for sem values
key_current = "current"
key_next = "next"
key_future = "future"

# determine which line contains semester info
__sem_label = "Report of all active classes for"


def fetch_sem_values(ftp_dir, out_dir):

	files = (filename_current, filename_next, filename_future)
	keys = (key_current, key_next, key_future)

	outpath = join(out_dir, sem_file)
	sem_dict = {}

	for i in range(len(files)):

		sem = None
		m_file = files[i]
		filepath = join(ftp_dir, m_file)

		if isfile(filepath):

			lines = []

			with open(filepath, 'r') as f:
				lines = f.readlines()				
				
			for line in lines:
				if __sem_label in line:
					m = re.search('[A-Za-z ]+(\d{5}) (.*)?', line)
					sem = m.group(1)
		else:
			# print(f"Fetch Sem: cannot find file: {m_file} in {ftp_dir}")

		sem_dict[keys[i]] = sem

	with open(outpath, 'w') as f:
		json.dump(sem_dict, f)
	
	return outpath


def fetch_ftp_files(out_dir):
	"""Downloads ftp files from UT Austin FTP server

	Args:
		out_dir (str): directory to download files to
	"""
	__url = 'reg-it.austin.utexas.edu'
	__username = 'anonymous'

	cur_dir = getcwd()

	ftp = FTP(__url)
	ftp.login(user=__username)

	chdir(out_dir)
	for filename in (filename_current, filename_next, filename_future):

		# print(f'FTP: downloading {filename}')
		localfile = open(filename, 'wb')
		ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
		localfile.close()
	
	ftp.quit()

	chdir(cur_dir)


def parse_ftp(in_dir):
	"""Parse FTP files from the UT Austin FTP server

	Args:
		in_dir (str): directory containinig the ftp files
	"""
	
	courses = []

	for filename in (filename_current, filename_next, filename_future):

		filepath = join(in_dir, filename)

		if isfile(filepath):

			# print(f'FTP: parsing {filename}')
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
		# else:
		# 	print(f'FTP: {filename} does not exist in {in_dir}')

	return courses


def __parse_categories(ftp_lines):

	line_num = 0

	for line in ftp_lines:

		line_num += 1

		if "year" in line.lower():

			categories = line.split("\t")
			categories = [category.strip() for category in categories if len(category.strip()) > 0]
			return categories, ftp_lines[line_num:]
	
	return None, ftp_lines
