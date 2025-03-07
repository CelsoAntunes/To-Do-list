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

def create_task(task_text,days,user=None):
    if user is None:
        user = get_user_model().objects.get(username="testuser")
    time = timezone.now() + datetime.timedelta(days = days)
    return Task.objects.create(task_text=task_text,pub_date = time,user=user)

class TaskIndexViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data that will be shared across all tests in this class.
        """
        cls.username="testuser"
        cls.password="testpass"
        cls.user = get_user_model().objects.create_user(username=cls.username, password=cls.password)

    def setUp(self):
        """
        Log in the test user before each test.
        """
        self.client.login(
            username=self.__class__.username,
            password=self.__class__.password
        )

    def test_no_tasks(self):
        """
        If no tasks exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("todolist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for today.")
        self.assertQuerySetEqual(response.context["task_list_today"], [])

    def test_past_tasks(self):
        """
        If all the tasks are in the past, no tasks should be displayed.
        """
        task=[create_task(task_text="Past tasks",days = -25+5*i) for i in range(5)]
        response = self.client.get(reverse("todolist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for today.")
        self.assertQuerySetEqual(response.context["task_list_today"], [])

    def test_future_tasks(self):
        """
        If all the tasks are in the future, no tasks should be displayed.
        """
        task=[create_task(task_text="Future task", days=1 + 5 * i) for i in range(5)] 
        response = self.client.get(reverse("todolist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for today.")
        self.assertQuerySetEqual(response.context["task_list_today"], [])

    def test_past_and_present_tasks(self):
        """
        If there is one task today and more tasks in the past, only the task from today should be displayed.
        """
        task=[create_task(task_text="Some task",days = -20+5*i) for i in range(5)]
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[4]],
        )

    def test_present_and_future_tasks(self):
        """
        If there is one task today and more tasks in the future, only the task from today should be displayed.
        """
        task=[create_task(task_text="Some tasks",days = 5*i) for i in range(5)]
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[0]],
        )

    def test_past_present_and_future_tasks(self):
        """
        If there is one task today and more tasks in the past and future, only the task from today should be displayed.
        """
        task=[create_task(task_text="Some tasks",days = -2+i) for i in range(5)]
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[2]],
        )

    def test_many_tasks_today(self):
        """
        If there are many tasks today, all of them should be displayed.
        """
        task=[create_task(task_text="Today's task", days=0) for i in range(9)]
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            task,
        )