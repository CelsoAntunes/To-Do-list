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

class TaskModelsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data that will be shared across all tests in this class.
        """
        cls.user = get_user_model().objects.create_user(username="testuser", password="testpass")

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

class ModelsCreationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data that will be shared across all tests in this class.
        """
        cls.username="testuser"
        cls.password="testpass"
        cls.user = get_user_model().objects.create_user(username=cls.username, password=cls.password)
    
    def test_create_normal_task(self):
        """
        Normal conditions for a task.
        """
        task = Task(task_text="Valid task", pub_date=timezone.now(), user=self.__class__.user)
        task.save()
        self.client.login(
            username=self.__class__.username,
            password=self.__class__.password
        )
        response = self.client.get(reverse("todolist:index"))
        self.assertQuerySetEqual(
            response.context["task_list_today"],
            [task],
        )

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

    def test_create_new_task_today(self):
        """
        Check if the new created task is correctly saved to the db.
        """
        login_successful = self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        task_text = "New task"
        response = self.client.post(
            reverse('todolist:index'), 
            {
                'task_text': task_text,
                'user_id': session_user_id
            }
        )
        task_db = Task.objects.filter(task_text=task_text).first()
        self.assertIsNotNone(task_db, "Does not fetch task from db")
        self.assertEqual(task_db.task_text,task_text)
        self.assertEqual(task_db.user, self.__class__.user)

    def test_create_task_not_logged_in(self):
        """
        Check if an unauthenticated user cannot create a task.
        """
        task_text = "New task"
        time = timezone.now()

        response = self.client.post(reverse('todolist:index'), {
            'task_text': task_text,
            'pub_date': time,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{reverse("todolist:login")}?next={reverse("todolist:index")}')

    def test_create_task_empty_text(self):
        """
        Check if a task with empty task_text cannot be created.
        """
        login_successful = self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        response = self.client.post(reverse('todolist:index'), {
            'task_text': '', 
            'pub_date': timezone.now(),
            'user_id': session_user_id
        }, follow=True)

        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(messages_list)
        self.assertIn('Task must contain at least one letter or number.', messages_list)

    def test_create_task_missing_required_fields(self):
        """
        Check if missing required fields (e.g., task_text) results in a validation error.
        """
        self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        response = self.client.post(reverse('todolist:index'), {
            'pub_date': timezone.now(), 
            'user_id': session_user_id
        })
        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(messages_list)
        self.assertIn('Task must contain at least one letter or number.', messages_list)

    def test_create_task_missing_pub_date(self):
        """
        Check if missing pub_date tasks can be uploaded.
        """
        self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        task_text='hello world'
        response = self.client.post(reverse('todolist:index'), {
            'task_text': task_text,
            'user_id': session_user_id
        })
        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(task_text=task_text)
        self.assertEqual(task.pub_date.date(), timezone.now().date())

    def test_create_task_too_long_task_text(self):
        """
        Check if task creation fails when task_text exceeds the character limit.
        """
        self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        long_task_text = 'A' * 1000 
        response = self.client.post(reverse('todolist:index'), {
            'task_text': long_task_text,
            'pub_date': timezone.now(),
            'user_id': session_user_id
        })
        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(messages_list)
        self.assertIn('Task is too long!', messages_list)

    '''def test_create_task_with_incorrect_user(self):
        """
        Check if an incorrect user ID is rejected during task creation.
        """
        self.client.login(username=self.__class__.user.username, password='testpass')

        invalid_user_id = 99999 
        response = self.client.post(reverse('todolist:index'), {
            'task_text': 'Task with invalid user',
            'pub_date': timezone.now(),
            'user': invalid_user_id
        })
        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(messages_list)
        self.assertIn('You cannot create tasks for other users!', messages_list)
    
    def test_create_task_for_another_user(self):
        """
        Check if an incorrect user ID is rejected during task creation.
        """
        self.client.login(username=self.__class__.user.username, password='testpass')
        user = User.objects.create_user(username='testuser1', password='testpass')
        
        response = self.client.post(reverse('todolist:index'), {
            'task_text': 'Task with invalid user',
            'pub_date': timezone.now(),
            'user': user.id
        })
        messages_list = [msg.message for msg in messages.get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(messages_list)
        self.assertIn('You cannot create tasks for other users!', messages_list)'''

    def test_create_task_without_being_logged_in(self):
        """
        Check if a user can post a task without being logged in.
        """
        self.client.logout()
        user_id = 1
        initial_task_count = Task.objects.count()
        response = self.client.post(
            reverse('todolist:index'), 
            {
                'task_text': 'Task without being logged in',
                'pub_date': timezone.now(),
                'user_id': user_id
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("todolist:login")+'?next=/')
        self.assertEqual(Task.objects.count(), initial_task_count)

    def test_unicode_task_text(self):
        self.client.login(username=self.__class__.user.username, password='testpass')
        session_user_id = self.client.session.get('_auth_user_id')
        self.assertTrue(self.client.session.get('_auth_user_id'))
        task_text = '🔥🚀 a你好'
        response = self.client.post(
            reverse('todolist:index'), 
            {
                'task_text': task_text,
                'pub_date':timezone.now(), 
                'user_id': session_user_id
            }
        )
        self.assertEqual(response.status_code, 302)  
        self.assertEqual(Task.objects.filter(task_text=task_text).count(), 1)
        task_db = Task.objects.get(task_text=task_text)
        self.assertEqual(task_text,task_db.task_text)