from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import generic
from django.utils import timezone
from .models import Task

class IndexView(generic.ListView):
    template_name = "todolist/index.html"
    context_object_name = 'task_list_today'

    def get_queryset(self):
        """Return the Tasks of today."""
        today = timezone.now().date()
        return Task.objects.filter(pub_date__date=today).order_by("pub_date")
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