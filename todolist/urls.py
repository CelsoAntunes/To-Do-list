from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from .views import IndexView, update_task, register, CustomLoginView
from django.shortcuts import redirect

def redirect_if_not_logged_in(request):
    if not request.user.is_authenticated:
        return redirect("todolist:login")
    return IndexView.as_view()(request)

app_name = "todolist"
urlpatterns = [
    path('admin/', admin.site.urls),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("", IndexView.as_view(), name="index"),
    path("update_task/", update_task, name="update_task"),
    path('accounts/', include('django.contrib.auth.urls')),
    path("register/", register, name="register"),
]