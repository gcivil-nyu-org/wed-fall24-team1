# home/urls.py

from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path("", login_required(views.home_view), name="home"),
    path(
        "submit_review/", login_required(views.submit_review), name="submit_review"
    ),  # New URL
    path(
        "get_reviews/<str:service_id>/", views.get_reviews, name="get_reviews"
    ),  # Fix this path
    path("delete_review/<str:review_id>/", views.delete_review, name="delete_review"),
    path("edit_review/<str:review_id>/", views.edit_review, name="delete_review"),
    path("toggle_bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
]
