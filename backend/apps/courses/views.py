from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny

from .models import Course, Lesson
from .serializers import CourseDetailSerializer, CourseSerializer, LessonSerializer
from .services import user_has_access


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class CourseLessonsView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course = Course.objects.get(slug=self.kwargs['slug'])
        return course.lessons.filter(is_published=True)


class LessonAccessView(generics.RetrieveAPIView):
    queryset = Lesson.objects.filter(is_published=True)
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_object(self):
        lesson = super().get_object()
        if not lesson.is_free and not user_has_access(self.request.user, lesson.course):
            raise PermissionDenied('Nu ai acces la această lecție.')
        return lesson
