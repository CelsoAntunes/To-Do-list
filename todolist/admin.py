from django.contrib import admin

from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_text', 'user', 'pub_date')
    search_fields = ('task_text',)
    list_filter = ('user',)
    def get_queryset(self, request):
        """Return tasks based on the logged-in user."""
        queryset = super().get_queryset(request)
        queryset = queryset.filter(user=request.user)
        return queryset

admin.site.register(Task, TaskAdmin)
