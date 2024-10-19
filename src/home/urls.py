# home/urls.py

from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path("", login_required(views.home_view), name="home"),
    path("submit_review/", login_required(views.submit_review), name="submit_review"),  # New URL
    path('get_reviews/<str:service_id>/', views.get_reviews, name='get_reviews'),  # Fix this path

]
