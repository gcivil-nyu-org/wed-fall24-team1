# Register your models here.

from django.contrib import admin
from .models import Category, Post, Comment, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "description")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "created_at", "is_closed")
    list_filter = ("category", "is_closed", "created_at")
    search_fields = ("title", "content", "author__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username", "post__title")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "sender", "post", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = (
        "recipient__username",
        "sender__username",
        "post__title",
        "message",
    )
