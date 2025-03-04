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
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .models import Task

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

class UserRegistrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up data that will be shared across all tests in this class.
        """
        cls.user = get_user_model().objects.create_user(username='testuser', password='testpass')

    def test_user_registration(self):
        """
        Test that a user can register successfully via the website
        """
        username = 'testuser1'
        password = 'testpass1'
        response = self.client.post(reverse('todolist:register'), {
            'username': username,
            'password1': password,
            'password2': password 
        })

        self.assertRedirects(response, reverse('todolist:index'))

        user = User.objects.get(username=username)
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(password))

    def test_user_login(self):
        """
        Log in proceeded correctly
        """
        login_successful = self.client.login(username=self.__class__.user.username, password='testpass')
        self.assertTrue(login_successful)

    def test_right_user_after_login(self):
        """ 
        Right user is logged in
        """
        username = 'testuser1'
        password = 'testpass'
        user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)
        user_after_login = self.client.session['_auth_user_id']
        self.assertEqual(int(user_after_login), user.id)

    def test_user_registration_db(self):
        """
        Test that a user can register successfully in the db
        """
        username = 'testuser1'
        password = 'testpass'
        user = User.objects.create_user(username=username, password=password)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))

    def test_user_login_with_wrong_password(self):
        """
        Test that a user cannot login with the wrong password
        """
        login_successful = self.client.login(username=self.__class__.user.username, password='wrongpass')
        self.assertFalse(login_successful)

    def test_user_login_with_non_existent_user(self):
        """
        Test that login fails with a non-existent user
        """
        login_successful = self.client.login(username='nonuser', password='testpass')
        self.assertFalse(login_successful)

    def test_user_registration_with_duplicate_username_db(self):
        """
        Test that a user cannot register with an existing username in the db
        """
        username = 'testuser'
        password = 'testpass'
        with self.assertRaises(IntegrityError): 
            User.objects.create_user(username=username, password=password)

    def test_user_registration_with_duplicate_username(self):
        """
        Test that a user cannot register with an existing username
        """
        response = self.client.post(reverse('todolist:register'), {
            'username': 'testuser',
            'password1': 'testpass',
            'password2': 'testpass' 
        })
        self.assertEqual(response.status_code, 200)     
        form = response.context.get('form')
        self.assertTrue(form.errors)
        self.assertIn('username', form.errors)
        self.assertIn('A user with that username already exists.', form.errors['username'])

    def test_user_logout(self):
        """
        Test that a user can logout successfully and not access previous data
        """
        self.client.login(username=self.__class__.user.username, password='testpass')
        user_id = self.client.session['_auth_user_id']
        user = User.objects.get(id=user_id)
        task = Task.objects.create(task_text="Test Task", pub_date=timezone.now(), user=user)
        response = self.client.get(reverse("todolist:index"))
        self.assertContains(response, task.task_text)
        self.client.logout()
        response = self.client.get(reverse("todolist:index"))
        self.assertRedirects(response,reverse("todolist:login")+"?next=/")

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

class TaskSeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Chrome()
        cls.browser.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.browser.delete_all_cookies()
        cls.browser.quit()
        super().tearDownClass()
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='MoreDifficult7628413!')
        self.login_url = self.live_server_url + reverse('todolist:login')
        self.index_url = self.live_server_url + reverse('todolist:index')
        Task.objects.all().delete()
    
    def login(self):
        """Helper function to log in the user."""
        self.browser.get(self.login_url)
        self.browser.find_element(By.NAME, 'username').send_keys('testuser')
        self.browser.find_element(By.NAME, 'password').send_keys('MoreDifficult7628413!')
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form[action$="logout/"] button[type="submit"]'))
        )
    
    def create_task(self, text="New Task"):
        """Helper function to create tasks."""
        self.login()
        task_input=self.browser.find_element(By.NAME, 'task_text')
        task_input.send_keys(text)
        task_input.send_keys(Keys.RETURN)
        WebDriverWait(self.browser, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), text)
        )
        return text
    
    def test_login_with_valid_credentials(self):
        self.login()
        self.assertEqual(self.browser.current_url, self.index_url)
    
    def test_login_with_invalid_credentials(self):
        self.browser.get(self.login_url)
        self.browser.find_element(By.NAME, 'username').send_keys('wronguser')
        self.browser.find_element(By.NAME, 'password').send_keys('wrongpass')
        self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(1)
        self.assertIn('Please enter a correct username and password.', self.browser.page_source) 
    
    def test_logout_functionality(self):
        self.login()
        self.browser.find_element(By.CSS_SELECTOR, 'form[action$="logout/"] button[type="submit"]').click()
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.NAME, 'username'))  # Login form should be visible again
        )
        self.assertIn('Login', self.browser.page_source)
    
    def test_create_new_task(self):
        self.login()
        task_input = self.browser.find_element(By.NAME, 'task_text')
        task_input.send_keys('New Task')
        task_input.send_keys(Keys.RETURN)
        WebDriverWait(self.browser, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), 'New Task')
        )
        self.assertIn('New Task', self.browser.page_source)
    
    def test_edit_task_inline(self):
        self.login()
        self.create_task()
        task_element=self.browser.find_element(By.CSS_SELECTOR, '.editable-task')
        task_element.click()
        self.browser.execute_script("arguments[0].innerText = 'Updated task text';", task_element)
        task_element.send_keys(Keys.TAB)
        updated_task_element = self.browser.find_element(By.CSS_SELECTOR, '.editable-task')
        self.assertEqual(updated_task_element.text, 'Updated task text')
    
    """def test_delete_task(self):
        self.login()
        self.test_create_new_task()
        delete_button = self.browser.find_element(By.CSS_SELECTOR, '.delete-btn')
        delete_button.click()
        time.sleep(1)
        self.assertNotIn('New Task', self.browser.page_source)"""
    
    def test_complete_task(self):
        self.login()
        self.create_task()
        checkbox = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.task-checkbox'))
        )
        checkbox.click()
        WebDriverWait(self.browser, 5).until(lambda driver: checkbox.is_selected())
        self.assertTrue(checkbox.is_selected())
    
    def test_page_load_performance(self):
        self.login()
        start_time = time.time()
        self.browser.get(self.index_url)
        load_time = time.time() - start_time
        self.assertLess(load_time, 3) 
    
    def test_no_javascript_errors(self):
        self.login()
        self.browser.get(self.index_url)
        logs = self.browser.get_log('browser')
        js_errors = [
            log for log in logs
            if 'SEVERE' in log['level'] and 'favicon.ico' not in log['message']
        ]
        self.assertEqual(len(js_errors), 0, f'JavaScript errors found: {js_errors}')
    
    def test_multiple_users_cannot_edit_same_task(self):
        self.login()
        self.create_task()
        self.browser.execute_script("window.open('about:blank', 'newtab');")
        first_window = self.browser.window_handles[0]
        new_window = self.browser.window_handles[1]
        self.browser.switch_to.window(new_window)
        self.browser.get(self.index_url)
        self.assertIn('New Task', self.browser.page_source)
        self.browser.switch_to.window(first_window)
        editable_task=self.browser.find_element(By.CSS_SELECTOR, '.editable-task')  
        editable_task.click()
        editable_task.send_keys(' - Edited')
        editable_task.send_keys(Keys.TAB)
        WebDriverWait(self.browser, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), ' - Edited')
        )
        self.browser.switch_to.window(new_window)
        self.browser.refresh()
        WebDriverWait(self.browser, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), ' - Edited')
        )
        self.assertIn(' - Edited', self.browser.page_source)
    
    def test_session_persistence(self):
        self.login()
        self.browser.get(self.index_url)
        self.browser.refresh()
        self.assertEqual(self.browser.current_url, self.index_url) 
