from django import forms
from nice_types.semester import SemesterSplitFormField, Semester, current_semester

import datetime
THIS_YEAR = datetime.date.today().year
GRAD_SEASONS = (("sp", "Spring"), ("fa", "Fall"))
GRAD_YEARS = [(str(x), x) for x in range(THIS_YEAR+6, THIS_YEAR-10, -1)]
class GradSemesterForm(forms.Form):
    graduation_semester = SemesterSplitFormField(label="Grad Semester", seasons=GRAD_SEASONS, years=GRAD_YEARS, initial=Semester(season_name="Spring", year=THIS_YEAR+2))

    fieldsets = [
        ('Academic Information', ('graduation_semester', )),
        ]

    @staticmethod
    def for_member(member):
        return {'graduation_semester' : member.academic.graduation_semester }

    def save(self, member):
        member.academic.graduation_semester = self.cleaned_data['graduation_semester']
        member.academic.save()

from member_academic.models import MemberCourse, MemberSubject
from nice_types.semester import current_semester

from courses.models import Subject, Course
from courses.forms.fields import MajorsChoiceField, MinorsChoiceField, ManyCoursesField, ManySubjectsField 
from courses.forms.widgets import ElementList, DepartmentAutocomplete, CourseNumberAutocomplete, SubjectAutocomplete

            
class CoursesForm(forms.Form):
    department = forms.CharField(widget=DepartmentAutocomplete(list_series=1), required=False)
    coursenumber = forms.CharField(label='Course Number', help_text="Search for a department above <strong>first</strong> and then a course number below!", widget=CourseNumberAutocomplete(list_series=1, abbreviations=True), required=False)
    currentcourses = ManyCoursesField(label="Current Courses", widget=ElementList(list_series=1), required=False)

    fieldsets = [
        ("Your Courses", "Input your current courses below. First find the department, and then search for the course number within that department. Both inputs complete automatically, so wait for the suggestions to appear.", ("department", "coursenumber", "currentcourses")),
    ]

    @staticmethod
    def for_member(member):
         return {'currentcourses' : [mc.course for mc in MemberCourse.objects.all().for_current_semester().filter(member=member).select_related('course')]}

    def save(self, member):
        courses = self.cleaned_data['currentcourses']

        old_course_ids = set(member.academic.courses.values_list('id', flat=True))
        if old_course_ids == set(c.id for c in courses):
            return

        semester = current_semester()
        MemberCourse.objects.filter(member=member.academic).delete()
        for course in courses:
            MemberCourse.objects.create(member=member.academic, course=course, instructor=None, semester=semester)
            

class SubjectsForm(forms.Form):
    major = forms.CharField(label="Add Major/Minor", help_text="Search in the input below to add majors and minors", widget=SubjectAutocomplete(list_series=12), required=False)
    currentsubjects = ManySubjectsField(label="Current Majors/Minors", widget=ElementList(list_series=12), required=False)

    fieldsets = [
        ('Academic Information', ('major', 'currentsubjects')),
        ]

    @staticmethod
    def for_member(member):
         return {'currentsubjects' : [ms.subject for ms in MemberSubject.objects.all().filter(member=member).order_by('-subject__major', '-primary').select_related('subject')]}

    def save(self, member):
        data = self.cleaned_data
        seen = []

        MemberSubject.objects.filter(member=member.academic).delete()
        for subject in data['currentsubjects']:
            primary = False
            if subject.major not in seen:
                primary = True
            seen.append(subject.major)
            MemberSubject.objects.create(member=member.academic, subject=subject, primary=primary)
