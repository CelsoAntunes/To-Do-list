from django.test import TestCase
import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError

from .models import Task

class TaskModelsTests(TestCase):
    def test_is_from_today_with_just_before_midnight_yesterday_task(self):
        """
        Tests whether a question from yesterday at 23:59:59 yesterday can appear.
        """
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1) 
        just_before_midnight = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
        task = Task(task_text="Yesterday's task.", pub_date=just_before_midnight)
        self.assertIs(task.is_from_today(),False)

    def test_is_from_today_with_1_day_prior_task(self):
        """
        Tests whether a question from exactly 1 day before can appear.
        """
        now = timezone.now()
        yesterday = now-datetime.timedelta(days=1)
        task = Task(task_text="Yesterday's task.", pub_date=yesterday)
        self.assertIs(task.is_from_today(),False)
    
    def test_is_from_today_with_middle_of_the_day_task(self):
        """
        Tests whether a question from today at 12:00:00 appears.
        """
        now = timezone.now()
        noon = now.replace(hour=12,minute=0,second=0,microsecond=0)
        task = Task(task_text="Task at noon.", pub_date=noon)
        self.assertIs(task.is_from_today(),True)
    
    def test_is_from_today_with_just_before_midnight_today_task(self):
        """
        Tests whether a question from today at 23:59:59 today appears.
        """
        now = timezone.now()
        just_before_midnight = now.replace(hour=23, minute=59, second=59, microsecond=0)
        task = Task(task_text="Task at noon.", pub_date=just_before_midnight)
        self.assertIs(task.is_from_today(),True)

    def test_is_from_today_with_at_midnight_today_task(self):
        """
        Tests whether a question from today at midnight appears.
        """
        now = timezone.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        task = Task(task_text="Task at noon.", pub_date=midnight)
        self.assertIs(task.is_from_today(),True)
    
    def test_is_from_today_with_tomorrow_midnight_task(self):
        """
        Tests whether a question from tomorrow at midnight appears.
        """
        now = timezone.now()
        tomorrow = now+datetime.timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        task = Task(task_text="Task at noon.", pub_date=midnight)
        self.assertIs(task.is_from_today(),False)

    def test_is_from_today_with_tomorrow_task(self):
        """
        Tests whether a question from tomorrow at midnight appears.
        """
        now = timezone.now()
        tomorrow = now+datetime.timedelta(days=1)
        task = Task(task_text="Task at noon.", pub_date=tomorrow)
        self.assertIs(task.is_from_today(),False)

def create_task(task_text,days):
    time = timezone.now() + datetime.timedelta(days = days)
    task = Task(task_text=task_text,pub_date = time)
    task.save()
    return task

class TaskIndexViewTests(TestCase):
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
        task=[None]*5
        for i in range(5):
            task[i] = create_task(task_text="Past tasks",days = -25+5*i)
        response = self.client.get(reverse("todolist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for today.")
        self.assertQuerySetEqual(response.context["task_list_today"], [])

    def test_future_tasks(self):
        """
        If all the tasks are in the future, no tasks should be displayed.
        """
        task=[None]*5
        for i in range(5):
            task[i] = create_task(task_text="Future tasks",days = 1+5*i)
        response = self.client.get(reverse("todolist:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No tasks for today.")
        self.assertQuerySetEqual(response.context["task_list_today"], [])

    def test_past_and_present_tasks(self):
        """
        If there is one task today and more tasks in the past, only the task from today should be displayed.
        """
        task=[None]*5
        for i in range(5):
            task[i] = create_task(task_text="Some task",days = -20+5*i)
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[4]],
        )

    def test_present_and_future_tasks(self):
        """
        If there is one task today and more tasks in the future, only the task from today should be displayed.
        """
        task=[None]*5
        for i in range(5):
            task[i] = create_task(task_text="Some tasks",days = 5*i)
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[0]],
        )

    def test_past_present_and_future_tasks(self):
        """
        If there is one task today and more tasks in the past and future, only the task from today should be displayed.
        """
        task=[None]*5
        for i in range(5):
            task[i] = create_task(task_text="Some tasks",days = -2+i)
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task[2]],
        )

    def test_many_tasks_today(self):
        """
        If there are many tasks today, all of them should be displayed.
        """
        task=[None]*9
        for i in range(9):
            task[i]=create_task(task_text="Today's tasks", days =0)
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            task,
        )

class ModelsCreationTests(TestCase):
    def test_task_with_invalid_pub_date(self):
        """
        If pub_date is not a string corresponding to a date, there should be an error.
        """
        invalid_task1 = Task(task_text="Invalid task None", pub_date=None)
        with self.assertRaises(ValidationError):
            invalid_task1.full_clean()
        invalid_task2 = Task(task_text="Invalid task list", pub_date=[])
        with self.assertRaises(ValidationError):
            invalid_task1.full_clean()
        invalid_task3 = Task(task_text="Invalid task int", pub_date=1)
        with self.assertRaises(ValidationError):
            invalid_task1.full_clean()
        invalid_task4 = Task(task_text="Invalid task string not date", pub_date="roller coaster")
        with self.assertRaises(ValidationError):
            invalid_task1.full_clean()
    
    def test_task_with_empty_task_text(self):
        """
        If task_text is empty, there should be an error.
        """
        invalid_task = Task(task_text='', pub_date=timezone.now())
        with self.assertRaises(ValidationError):
            invalid_task.full_clean()