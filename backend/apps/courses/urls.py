from django.urls import path

from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course-list'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('<slug:slug>/lessons/', views.CourseLessonsView.as_view(), name='course-lessons'),
]
