from django.contrib import admin

from apps.courses.models import Enrollment
from apps.payments.models import Payment

from .models import PasswordResetToken, User


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('course', 'status', 'granted_at')
    readonly_fields = ('granted_at',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('course', 'amount_cents', 'currency', 'status', 'stripe_session_id', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Security', {'fields': ('failed_login_attempts', 'locked_until')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    inlines = [EnrollmentInline, PaymentInline]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    search_fields = ('user__email',)
