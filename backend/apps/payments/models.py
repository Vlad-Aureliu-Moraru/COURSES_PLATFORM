from django.conf import settings
from django.db import models


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='payments'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.SET_NULL, null=True,
        related_name='payments'
    )
    stripe_session_id = models.CharField(max_length=200, unique=True, blank=True)
    amount_cents = models.PositiveIntegerField(default=settings.COURSE_PRICE_CENTS)
    tax_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default=settings.COURSE_CURRENCY)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
        ]

    @property
    def amount(self):
        return self.amount_cents / 100

    @property
    def total(self):
        return (self.amount_cents + self.tax_cents) / 100

    def __str__(self):
        return f'Payment {self.id} — {self.user_id} ({self.status})'
