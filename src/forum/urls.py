from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.category_list, name="category_list"),
    path("category/<int:category_id>/", views.category_detail, name="category_detail"),
    path("post/<int:post_id>/", views.post_detail, name="post_detail"),
    path(
        "category/<int:category_id>/create_post/", views.create_post, name="create_post"
    ),
    path("post/<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("post/<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("comment/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path(
        "comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"
    ),
    path(
        "notifications/<int:notification_id>/mark-read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/count/",
        views.get_notifications_count,
        name="get_notifications_count",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
    path(
        "notifications/<int:notification_id>/delete/",
        views.delete_notification,
        name="delete_notification",
    ),
]
