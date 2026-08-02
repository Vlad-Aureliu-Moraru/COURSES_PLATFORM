from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Course, Enrollment, Lesson


def make_course():
    return Course.objects.create(
        slug='bani-online',
        title='Curs de test',
        price_cents=799,
        currency='eur',
    )


def make_lesson(course, slug, order, is_free=False):
    return Lesson.objects.create(
        course=course, slug=slug, title=slug, order=order, is_free=is_free
    )


def make_user(email='buyer@test.com', password='StrongPass1'):
    user = User.objects.create_user(email=email, password=password, username=email)
    return user


def test_course_list_public(db):
    make_course()
    client = APIClient()
    response = client.get('/api/v1/courses/')
    assert response.status_code == 200
    results = response.data['results']
    assert len(results) == 1
    assert results[0]['price'] == '7.99'


def test_course_detail_includes_lessons(db):
    course = make_course()
    make_lesson(course, '00-ghid-rapid', 0, is_free=True)
    make_lesson(course, '02-micro-taskuri', 2, is_free=False)

    client = APIClient()
    response = client.get('/api/v1/courses/bani-online/')
    assert response.status_code == 200
    lessons = response.data['lessons']
    assert len(lessons) == 2
    assert lessons[0]['slug'] == '00-ghid-rapid'
    # anon: free unlocked, paid locked
    assert lessons[0]['is_unlocked'] is True
    assert lessons[1]['is_unlocked'] is False


def test_free_lesson_unlocked_for_anon(db):
    course = make_course()
    make_lesson(course, '00-ghid-rapid', 0, is_free=True)

    client = APIClient()
    response = client.get('/api/v1/courses/bani-online/lessons/')
    assert response.status_code == 200
    assert response.data['results'][0]['is_unlocked'] is True


def test_paid_lesson_requires_auth_for_access(db):
    course = make_course()
    make_lesson(course, '02-micro-taskuri', 2, is_free=False)

    client = APIClient()
    response = client.get('/api/v1/lessons/02-micro-taskuri/')
    assert response.status_code == 403


def test_free_lesson_accessible_anon(db):
    course = make_course()
    make_lesson(course, '00-ghid-rapid', 0, is_free=True)

    client = APIClient()
    response = client.get('/api/v1/lessons/00-ghid-rapid/')
    assert response.status_code == 200
    assert response.data['is_unlocked'] is True


def test_lesson_unlocked_after_grant(db):
    course = make_course()
    lesson = make_lesson(course, '02-micro-taskuri', 2, is_free=False)
    user = make_user()

    client = APIClient()
    client.force_authenticate(user=user)
    assert client.get('/api/v1/lessons/02-micro-taskuri/').status_code == 403

    Enrollment.objects.create(user=user, course=course, status='active')
    response = client.get('/api/v1/lessons/02-micro-taskuri/')
    assert response.status_code == 200
    assert response.data['slug'] == lesson.slug


def test_lesson_access_returns_unlocked_flag(db):
    course = make_course()
    make_lesson(course, '02-micro-taskuri', 2, is_free=False)
    user = make_user()
    Enrollment.objects.create(user=user, course=course, status='active')

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get('/api/v1/lessons/02-micro-taskuri/')
    assert response.data['is_unlocked'] is True
