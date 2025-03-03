import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    task_text = models.CharField(max_length=255)
    pub_date = models.DateTimeField("date published")
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.task_text

    def is_from_today(self):
        now = timezone.now()
        return self.pub_date.date() == now.date()