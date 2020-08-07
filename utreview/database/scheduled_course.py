
class ScheduledCourseInfo:

	def __init__(self, s_course):

		# sem info                                                                                                                                                                                                                                                                              
		self.yr = int(s_course["Year"].strip())
		self.sem = int(s_course["Semester"].strip())

		# course info
		self.dept = s_course["Dept-Abbr"].strip().upper()
		c_num_raw = s_course["Course Nbr"].strip().upper()
		self.title = s_course["Title"].strip()
		self.topic = s_course["Topic"].strip()

		try:
			self.topic = int(self.topic)
		except ValueError:
			self.topic = -1

		if not c_num_raw:
			# print("Populate scheduled course: no course number. Skipping...")
			raise ValueError("No course number.")
		
		self.c_num = c_num_raw[1:] if c_num_raw[0].isalpha() else c_num_raw

		# prof info
		self.prof_eid = s_course["Instructor EID"].strip().lower()

		# scheduled info
		self.session = c_num_raw[0] if c_num_raw[0].isalpha() else None
		self.unique_no = s_course["Unique"].strip()
		try:
			self.unique_no = int(self.unique_no)
		except ValueError:
			raise ValueError("No unique number.")
			
		self.days = s_course["Days"].strip().upper()
		self.time_from = int_or_none(s_course["From"].strip())

		self.time_to = int_or_none(s_course["To"].strip())
		building = s_course["Building"].strip().upper()
		room = s_course["Room"].strip().upper()
		self.location = parse_location(self.title, building, room)
		self.max_enrollment = int_or_none(s_course["Max Enrollment"].strip())
		self.seats_taken = int_or_none(s_course["Seats Taken"].strip())
		self.x_listings = [listing.strip() for listing in s_course["X-Listings"].strip().split(",")]


def int_or_none(obj):
	try:
		return int(obj)
	except (ValueError, TypeError):
		return None

def parse_location(title, building, room):

	__default = "N/A"
	__web_tag = "-w"

	if not building or not room:
		return 'WEB' if __web_tag in title.lower() else 'N/A'
	
	return f'{building} {room}'
