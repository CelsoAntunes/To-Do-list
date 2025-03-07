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