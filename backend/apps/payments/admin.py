from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Payment
from .services import refund_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'course', 'status', 'display_amount', 'currency',
        'stripe_session_id', 'created_at',
    )
    list_filter = ('status', 'currency', 'course')
    search_fields = ('user__email', 'stripe_session_id')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['refund_payments']

    @admin.display(description='Amount')
    def display_amount(self, obj):
        return f'{obj.amount:.2f} {obj.currency.upper()}'

    @admin.action(description='Rambursează plățile selectate')
    def refund_payments(self, request, queryset):
        refundable = queryset.filter(status='paid')
        refunded_count = 0
        for payment in refundable:
            refund_payment(payment)
            refunded_count += 1

        skipped = queryset.count() - refunded_count
        self.message_user(
            request,
            f'{refunded_count} plată/i rambursată/e + acces revocat + email trimis.',
            level=messages.SUCCESS,
        )
        if skipped:
            self.message_user(
                request,
                f'{skipped} plată/i sărită/e (doar cele cu status „paid” pot fi rambursate).',
                level=messages.WARNING,
            )
