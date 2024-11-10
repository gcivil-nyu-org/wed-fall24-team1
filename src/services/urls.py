from django.urls import path
from . import views

app_name = "services"

urlpatterns = [
    path("", views.service_list, name="list"),
    path("create/", views.service_create, name="create"),
    path("<str:service_id>/edit/", views.service_edit, name="edit"),
    path("<str:service_id>/delete/", views.service_delete, name="delete"),
    path("<str:service_id>/details/", views.service_details, name="service_details"),
    path("<str:service_id>/reviews/", views.review_list, name="review_list"),
    path(
        "<str:service_id>/reviews/<str:review_id>/respond/",
        views.respond_to_review,
        name="respond_to_review",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "analytics/bookmarks_over_time/",
        views.bookmarks_over_time,
        name="bookmarks_over_time",
    ),
    path(
        "analytics/reviews_over_time/",
        views.reviews_over_time,
        name="reviews_over_time",
    ),
    path(
        "analytics/average_rating_over_time/",
        views.average_rating_over_time,
        name="average_rating_over_time",
    ),
    path(
        "analytics/rating_distribution/",
        views.rating_distribution,
        name="rating_distribution",
    ),
    path("analytics/recent_reviews/", views.recent_reviews, name="recent_reviews"),
    path("analytics/response_rate/", views.response_rate, name="response_rate"),
    path(
        "analytics/review_word_cloud/",
        views.review_word_cloud,
        name="review_word_cloud",
    ),
    path(
        "analytics/service_category_distribution/",
        views.service_category_distribution,
        name="service_category_distribution",
    ),
    path("analytics/user_analytics/", views.user_analytics, name="user_analytics"),
]
