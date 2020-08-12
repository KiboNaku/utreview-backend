
import json
import re

from ftplib import FTP
from os import chdir, getcwd
from os.path import join, isfile

from utreview import logger


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
	"""
	fetch semester values from the FTP data files from the given directory
	:param ftp_dir: the directory containing the ftp data files
	:param out_dir: the directory to output a file containing the semester data
	"""

	files = (filename_current, filename_next, filename_future)
	keys = (key_current, key_next, key_future)

	out_path = join(out_dir, sem_file)
	sem_dict = {}
	logger.info(f"Fetching semester values from dir={ftp_dir}, to file={out_path}")

	for i in range(len(files)):

		sem = None
		m_file = files[i]
		filepath = join(ftp_dir, m_file)

		if isfile(filepath):

			with open(filepath, 'r') as f:
				lines = f.readlines()				
				
			for line in lines:
				if __sem_label in line:
					m = re.search(r'[A-Za-z ]+(\d{5}) (.*)?', line)
					sem = m.group(1)
		# else:
			# print(f"Fetch Sem: cannot find file: {m_file} in {ftp_dir}")

		sem_dict[keys[i]] = sem

	with open(out_path, 'w') as f:
		json.dump(sem_dict, f)
	
	return out_path


def fetch_ftp_files(out_dir):
	"""Downloads ftp files from UT Austin FTP server

	Args:
		out_dir (str): directory to download files to
	"""
	__url = 'reg-it.austin.utexas.edu'
	__username = 'anonymous'

	logger.info(f"Downloading FTP data files to {out_dir}")

	cur_dir = getcwd()

	ftp = FTP(__url)
	ftp.login(user=__username)

	chdir(out_dir)
	for filename in (filename_current, filename_next, filename_future):

		logger.debug(f'FTP: downloading {filename}')
		local_file = open(filename, 'wb')
		ftp.retrbinary('RETR ' + filename, local_file.write, 1024)
		local_file.close()
	
	ftp.quit()

	chdir(cur_dir)


def parse_ftp(in_dir):
	"""Parse FTP files from the UT Austin FTP server

	Args:
		in_dir (str): directory containinig the ftp files
	"""

	logger.info(f"Parsing FTP files from {in_dir}")
	courses = []

	for filename in (filename_current, filename_next, filename_future):

		filepath = join(in_dir, filename)

		if isfile(filepath):

			logger.debug(f'FTP: parsing {filename}')
			with open(filepath) as f:

				lines = f.readlines()
				categories, lines = __parse_categories(lines)
				
				if categories is not None:

					for line in lines:
						# standardizing the lines
						line = line.lower()
						data = line.split("\t")
						data = [d.strip() for d in data]

						if len(line) > 0 and len(data) >= len(categories):
							# separating data by category list
							course = {categories[i]: data[i] for i in range(len(categories))}
							courses.append(course)
		else:
			logger.debug(f'FTP: {filename} does not exist in {in_dir}')

	return courses


def __parse_categories(ftp_lines):
	"""
	iterate through the lines and parse out a list of categories for an FTP file
	:param ftp_lines: list of lines from the ftp files
	:type ftp_lines: list[str]
	:return: a tuple containing (list of categories, the list of lines after the categories -> the entire list if None)
	:rtype: tuple(list(str) or None, list[str])
	"""
	line_num = 0

	for line in ftp_lines:

		line_num += 1

		if "year" in line.lower():

			categories = line.split("\t")
			categories = [category.strip() for category in categories if len(category.strip()) > 0]
			return categories, ftp_lines[line_num:]
	
	return None, ftp_lines
