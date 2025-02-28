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
from .models import Task

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