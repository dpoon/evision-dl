from collections import namedtuple

class ApplicantContext(namedtuple('ApplicantContext', 'student_number surname preferred_name')):
    def __str__(self):
        return "Applicant {}, {} ({})".format(self.surname, self.preferred_name, self.student_number)
