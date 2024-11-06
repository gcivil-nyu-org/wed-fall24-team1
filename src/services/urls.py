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
]
