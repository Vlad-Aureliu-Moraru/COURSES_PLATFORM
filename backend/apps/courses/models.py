from django.conf import settings
from django.db import models


class Course(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField(default=settings.COURSE_PRICE_CENTS)
    currency = models.CharField(max_length=3, default=settings.COURSE_CURRENCY)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['id']

    @property
    def price(self):
        return self.price_cents / 100

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='lessons'
    )
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    est_time = models.CharField(max_length=50, blank=True)
    is_free = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    content = models.TextField(blank=True)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']
        unique_together = [('course', 'slug')]
        indexes = [
            models.Index(fields=['course', 'is_published', 'order']),
        ]

    def __str__(self):
        return f'{self.course_id}:{self.slug}'


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='enrollments'
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = [('user', 'course')]
        ordering = ['-granted_at']

    def __str__(self):
        return f'{self.user_id} → {self.course_id} ({self.status})'
