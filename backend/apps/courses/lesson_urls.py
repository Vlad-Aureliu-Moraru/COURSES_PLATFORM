from django.urls import path

from . import views

urlpatterns = [
    path('', views.LessonAccessView.as_view(), name='lesson-access'),
    path('content/', views.LessonContentView.as_view(), name='lesson-content'),
]
