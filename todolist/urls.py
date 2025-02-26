from django.urls import path
from .views import IndexView, update_task

app_name = "todolist"
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("update_task/", update_task, name="update_task"),
]