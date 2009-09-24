from django.utils.safestring import mark_safe, mark_for_escaping
from courses.models import Course, Department
from members.filters import register_member_filter, member_filter

def _filter_member_subjects(major):
    type_name = "major" if major else "minor"
    def _filter_member_inner(val, members):
        subjects = Subject.objects.filter(major=major, name__icontains=val)
        subject_names = [s.name for s in subjects]
        if len(subject_names) == 0:
            raise FilterValueError("Couldn't find any %ss containing '%s'" % (type_name, val))
        if len(subject_names) == 1:
            subject_names = "who are %sing in %s" % (type_name, subject_names[0])
        else:
            subject_names = "who are %sing in %s; or %s" % (type_name, "; ".join(subject_names[:-1]), subject_names[-1])
        return members.filter(subjects__in=subjects), subject_names
    return _filter_member_inner
register_member_filter(40, "member_major", _filter_member_subjects(True))
register_member_filter(50, "member_minor", _filter_member_subjects(False))

@member_filter(60, 'member_course')
def _filter_member_course(course, members):
    dept_abbr, coursenumber = Course.objects.parse_query(course)
    if not coursenumber:
        raise FilterValueError("Invalid course '%s'" % course)
    department = Department.objects.ft_query(dept_abbr)
    if len(department) == 0:
        raise FilterValueError(mark_safe(u"Couldn't find department with abbreviation '%s'; try %s for department abbreviations" % (mark_for_escaping(unicode(dept_abbr)),u'<a href="%s">here</a>' % urlresolvers.reverse('course-department-abbreviations'))))
    department = department[0]
    courses = Course.objects.query_exact(dept_abbr, coursenumber)
    if len(courses) == 0:
        raise FilterValueError("Couldn't find course '%s' in department %s" % (course, department.name))
    if len(courses) == 1:
        return members.filter(courses__in=courses), "who are taking %s" % courses[0].short_name(space=True)
    return members.filter(courses__in=courses), "who are taking one of: %s" % ", ".join(course.short_name(space=True) for course in courses)
    


