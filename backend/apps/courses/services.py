from .models import Enrollment


def grant_access(user, course):
    enrollment, created = Enrollment.objects.get_or_create(
        user=user,
        course=course,
        defaults={'status': 'active'},
    )
    if not created and enrollment.status != 'active':
        enrollment.status = 'active'
        enrollment.save(update_fields=['status'])
    return enrollment


def revoke_access(user, course):
    Enrollment.objects.filter(user=user, course=course).update(status='revoked')


def user_has_access(user, course):
    if user is None or user.is_anonymous:
        return False
    return Enrollment.objects.filter(
        user=user, course=course, status='active'
    ).exists()


def lesson_unlocked(user, lesson):
    if lesson.is_free:
        return True
    return user_has_access(user, lesson.course)
