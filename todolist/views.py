from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.contrib import messages
from .models import Task
import re

class CustomLoginView(LoginView):
    template_name = 'todolist/login.html'

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after registration
            return redirect("todolist:index")  # Redirect to main page
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = "todolist/index.html"
    login_url = "todolist:login"
    redirect_field_name = "next"
    context_object_name = 'task_list_today'

    def get_queryset(self):
        """Return the Tasks of the specified user today."""
        today = timezone.now().date()
        return Task.objects.filter(user=self.request.user, pub_date__date=today).order_by("pub_date")

    def post(self, request, *args, **kwargs):
        """Handle the creation of the task."""
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to create a task.')
            return redirect("todolist:login")

        task_text = request.POST.get('task_text', '').strip()
        if not task_text or not re.search(r"[a-zA-Z0-9]", task_text): 
            messages.error(request, 'Task must contain at least one letter or number!')
            return render(request, self.template_name, {'task_list_today': self.get_queryset()})
        if len(task_text) > 255:
            messages.error(request, 'Task is too long!')
            return render(request, self.template_name, {'task_list_today': self.get_queryset()})
        if str(request.user.id) != str(request.POST.get('user_id', '')):
            messages.error(request, 'You cannot create tasks for other users!')
            return render(request, self.template_name, {'task_list_today': self.get_queryset()})
        Task.objects.create(
            user=request.user,
            task_text=task_text,
            pub_date=timezone.now() 
        )
        return redirect('todolist:index')

@csrf_exempt  # You may need a better CSRF solution in production
def update_task(request):
    """Handle AJAX request to update task status."""
    if request.method == "POST":
        task_id = request.POST.get("task_id")
        done = request.POST.get("done") == "true" 

        try:
            task = Task.objects.get(id=task_id)
            task.done = done
            task.save()
            return JsonResponse({"status": "success", "task_id": task.id, "done": task.done})
        except Task.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Task not found"}, status=404)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)