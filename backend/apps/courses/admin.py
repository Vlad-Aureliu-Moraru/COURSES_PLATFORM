from django.contrib import admin, messages

from .models import Course, Enrollment, Lesson
from .services import grant_access, revoke_access


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('slug', 'title', 'order', 'is_free', 'is_published')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'price_cents', 'currency', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('slug', 'title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LessonInline]


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
    readonly_fields = ('granted_at',)
    actions = ['grant_selected', 'revoke_selected']

    @admin.action(description='Acordă acces (status „active”)')
    def grant_selected(self, request, queryset):
        for enrollment in queryset:
            grant_access(enrollment.user, enrollment.course)
        self.message_user(
            request,
            f'{queryset.count()} acces(uri) acordat(e).',
            level=messages.SUCCESS,
        )

    @admin.action(description='Revocă acces (status „revoked”)')
    def revoke_selected(self, request, queryset):
        for enrollment in queryset:
            revoke_access(enrollment.user, enrollment.course)
        self.message_user(
            request,
            f'{queryset.count()} acces(uri) revocat(e).',
            level=messages.SUCCESS,
        )
