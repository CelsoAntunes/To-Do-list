import datetime
import time

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib import messages
from todolist.models import Task

class TaskUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data that will be shared across all tests in this class.
        """
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.task = Task.objects.create(task_text="Test task", pub_date=timezone.now(), user=cls.user)

    def test_update_task(self):
        self.client.login(username='testuser', password='testpass')
        new_task_text = "New task text"
        response = self.client.post(
            reverse('todolist:update_task'), 
            {
                'task_id': self.task.id,
                'task_text': new_task_text,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.task_text, new_task_text)
        self.assertEqual(response.status_code, 200)

    def test_update_task_as_unauthenticated_user(self):
        response = self.client.post(reverse('todolist:update_task'), {
            'task_id': self.task.id,
            'task_text': 'Updated task text'
        })

        self.assertRedirects(response, reverse('todolist:login'))
        self.task.refresh_from_db()
        self.assertEqual(self.task.task_text, 'Test task')

    def test_update_task_with_long_text(self):
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(reverse('todolist:update_task'), {
            'task_id': self.task.id,
            'task_text': 'a' * 256  
        })
        
        self.assertContains(response, "Task too long!")
        self.task.refresh_from_db()
        self.assertEqual(self.task.task_text, 'Test task')

    def test_update_task_with_empty_text(self):
        self.client.login(username='testuser', password='testpass')

        response = self.client.post(reverse('todolist:update_task'), {
            'task_id': self.task.id,
            'task_text': ''
        })

        self.assertContains(response, "Task cannot be empty!")
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.task_text, 'Test task')

    def test_unauthorized_user_cannot_update(self):
        self.client.login(username='testuser', password='testpass')
        user2 = User.objects.create_user(username='testuser1', password='testpass')
        task2 = Task.objects.create(task_text='New test task', pub_date=timezone.now(), user=user2)
        response = self.client.post(
            reverse('todolist:update_task'), {  
                'task_id': task2.id,
                'task_text': 'Updated test task'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)     
        self.assertEqual(Task.objects.filter(id=task2.id).first().task_text, 'New test task')