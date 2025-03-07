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

class TaskDeleteTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser', password='testpass')
        cls.task = Task.objects.create(task_text="Test task", pub_date=timezone.now(), user=cls.user)

    def setUp(self):    
        self.client.login(username='testuser', password='testpass')

    def test_delete_task(self):
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': self.task.id, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success", "message": "Task deleted successfully."})
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
    
    def test_unauthorized_user_cannot_delete(self):
        user2 = User.objects.create_user(username='testuser1', password='testpass')
        task2 = Task.objects.create(task_text='New test task', pub_date=timezone.now(), user=user2)
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': task2.id, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(id=task2.id).exists())
    
    def test_delete_unexistent_task(self):
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': 999, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_post_twice(self):
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': self.task.id, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': self.task.id, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_unauthenticated_user(self):
        self.client.logout()
        response = self.client.post(
            reverse('todolist:update_task'),
            {'task_id': self.task.id, 'delete': 'true'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code,302)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())