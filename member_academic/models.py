from nice_types.db import QuerySetManager
from nice_types.semester import SemesterField, current_semester, Semester, InvalidSemester
from courses.models import Course, Instructor, Subject

from django.db import models
from django.db.models.query import QuerySet

from members.extensions import MemberExtension

class MemberCourseManager(QuerySetManager):
    pass

class MemberAcademic(MemberExtension):
    graduation_semester = SemesterField(null=True, default=None)
    subjects = models.ManyToManyField(Subject, through='MemberSubject')
    courses = models.ManyToManyField(Course, through='MemberCourse')

    def import_member(self, data):
        try:
            self.graduation_semester = Semester(data['academic']['graduation_semester'])
        except InvalidSemester:
            self.graduation_semester = None

        MemberCourse.objects.filter(member=self).delete()
        for course_name, semester in data['academic']['courses']:
            MemberCourse.objects.get_or_create(member=self, course=Course.objects.get_canonical(course_name), semester=Semester(semester))

        MemberSubject.objects.filter(member=self).delete()
        for subject_name, major, primary in data['academic']['subjects']:
            MemberSubject.objects.get_or_create(member=self, subject=Subject.objects.get(name=subject_name, major=major), primary=primary)

        self.save()

    def export_member(self):
        data = {'graduation_semester' : self.graduation_semester.abbr() if self.graduation_semester else ''}

        tmp = []
        for mc in MemberCourse.objects.filter(member=self).select_related('course', 'semester'):
            tmp.append((mc.course.canonical_name(), mc.semester.abbr()))
        data['courses'] = tmp

        tmp = []
        for ms in MemberSubject.objects.filter(member=self).select_related('subject'):
            tmp.append((ms.subject.name, ms.primary))

        data['subjects'] = tmp
        return {'academic' : data}

    @staticmethod
    def create_extension(member, **kwargs):
        me = MemberAcademic(member=member, graduation_semester=None)
        me.save()


    def describe_courses(self):
        courses = MemberCourse.objects.filter(member=self, semester=current_semester()).select_related('course')
        return ", ".join([course.course.short_name(space=True) for course in courses])
    def describe_courses_iter(self):
        return (mc.course.short_name(space=True) for mc in MemberCourse.objects.filter(member=self, semester=current_semester()).select_related('course'))

    def describe_subjects(self, major, join_str="; "):
        majors = MemberSubject.objects.filter(member=self, subject__major=major).order_by('-primary').values_list('subject__name', flat=True)
        return join_str.join(majors)
    describe_majors_br = lambda self: self.describe_subjects(True, "<br/>")
    describe_minors_br = lambda self: self.describe_subjects(False, "<br/>")

    def describe_subjects_iter(self, major):
        return iter(MemberSubject.objects.filter(member=self, subject__major=major).order_by('-primary').values_list('subject__name', flat=True).select_related('subject'))
    describe_majors_iter = lambda self: self.describe_subjects_iter(True)
    describe_minors_iter = lambda self: self.describe_subjects_iter(False)

    def describe_graduation(self):
        return self.graduation_semester.verbose_description()


class MemberCourse(models.Model):
    objects = MemberCourseManager()

    member = models.ForeignKey('member_academic.MemberAcademic')
    course = models.ForeignKey(Course)
    instructor = models.ForeignKey(Instructor, null=True)
    semester = SemesterField(null=True)

    class QuerySet(QuerySet):
        def for_current_semester(self):
            return self.filter(semester=current_semester())


class MemberSubject(models.Model):
    member = models.ForeignKey('member_academic.MemberAcademic')
    subject = models.ForeignKey(Subject)
    primary = models.BooleanField()

    class Meta:
        unique_together = (('member', 'subject'))

