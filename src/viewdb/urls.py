from django.urls import path
from . import views

urlpatterns = [
    path('dynamodb-table/', views.fetch_dynamodb_data, name='dynamodb_table'),
]
