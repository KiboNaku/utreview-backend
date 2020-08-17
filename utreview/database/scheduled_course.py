
from utreview import int_or_none
from utreview.models.others import ScheduledCourse


class ScheduledCourseInfo:
	"""
	Class used to parse and filter information from dictionary containing ScheduledCourse data
	"""
	def __init__(self, s_course):
		"""
		initialize ScheduledCourseInfo with dictionary info
		:param s_course: dictionary containing ScheduledCourse data.
		:type s_course: dict{
			"Year": str,
			"Semester": str,
			"Dept-Abbr": str,
			"Course Nbr": str,
			"Title": str,
			"Topic": str,
			"Instructor EID": str,
			"Unique": str,
			"Days": str,
			"From": str,
			"To": str,
			"Building": str,
			"Room": str,
			"Max Enrollment": str,
			"Seats Taken": str,
			"X-Listings": str
		}
		"""
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

	def to_scheduled_course(self, scheduled_course, semester, course, prof, x_list):
		"""
		Populate a ScheduledCourse with data from this class
		:param scheduled_course: object to populate data
		:type scheduled_course: ScheduledCourse
		:param course: course object related to scheduled_course
		:type course: Course
		:param semester: model object containing semester id related to scheduled course
		:type semester: Semester
		:param prof: prof object related to scheduled_course
		:type prof: Prof
		:param x_list: cross_listed object related to scheduled_course
		:type x_list: CrossListed
		:return: reference back to scheduled_course parameter
		:rtype: ScheduledCourse
		"""
		scheduled_course.unique_no = self.unique_no
		scheduled_course.session = self.session
		scheduled_course.days = self.days
		scheduled_course.time_from = self.time_from
		scheduled_course.time_to = self.time_to
		scheduled_course.location = self.location
		scheduled_course.max_enrollment = self.max_enrollment
		scheduled_course.seats_taken = self.seats_taken
		scheduled_course.sem_id = semester.id
		scheduled_course.course_id = course.id
		scheduled_course.prof_id = prof.id if prof else None
		scheduled_course.cross_listed = x_list.id
		return scheduled_course

	def build_scheduled_course(self, semester, course, prof, x_list):
		"""
		Populate a new ScheduledCourse with data from this class
		:param semester: model object containing semester id related to scheduled course
		:type semester: Semester
		:param course: course object related to scheduled_course
		:type course: Course
		:param prof: prof object related to scheduled_course
		:type prof: Prof
		:param x_list: cross_listed object related to scheduled_course
		:type x_list: CrossListed
		:return: reference to scheduled_course containing data
		:rtype: ScheduledCourse
		"""
		scheduled_course = ScheduledCourse()
		return self.to_scheduled_course(scheduled_course, semester, course, prof, x_list)


def parse_location(title, building, room):
	"""
	Parse location from parameters with default being WEB
	:param title: title of course
	:type title: str
	:param building: building for scheduled_course
	:type building: str
	:param room: room number for building for scheduled_course
	:type room: str
	:return: location of course
	:rtype: str
	"""
	__default = "N/A"
	__web_tag = "-w"

	if not building or not room:
		return 'WEB' if __web_tag in title.lower() else 'N/A'
	
	return f'{building} {room}'
