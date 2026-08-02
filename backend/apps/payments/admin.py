from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'course', 'status', 'display_amount', 'currency',
        'stripe_session_id', 'created_at',
    )
    list_filter = ('status', 'currency', 'course')
    search_fields = ('user__email', 'stripe_session_id')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Amount')
    def display_amount(self, obj):
        return f'{obj.amount:.2f} {obj.currency.upper()}'
