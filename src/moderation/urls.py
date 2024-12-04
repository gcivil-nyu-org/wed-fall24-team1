from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('flag/create/', views.create_flag, name='create_flag'),
    path('flag/<int:flag_id>/review/', views.review_flag, name='review_flag'),
]