from rest_framework import serializers

from .models import Course, Lesson
from .services import lesson_unlocked


class CourseSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'slug', 'title', 'description', 'price', 'price_cents', 'currency']


class LessonSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'slug', 'title', 'order', 'est_time', 'is_free', 'is_unlocked']

    def get_is_unlocked(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        return lesson_unlocked(user, obj)


class CourseDetailSerializer(CourseSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['lessons']
