from django.contrib import admin

from .models import Course, Enrollment, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'price_cents', 'currency', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('slug', 'title')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'slug', 'title', 'order', 'is_free', 'is_published')
    list_filter = ('is_free', 'is_published', 'course')
    search_fields = ('slug', 'title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status', 'granted_at')
    list_filter = ('status', 'course')
    search_fields = ('user__email', 'course__slug')
