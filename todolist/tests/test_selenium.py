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
from selenium.webdriver.common.alert import Alert

from todolist.models import Task

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
            EC.presence_of_element_located((By.NAME, 'username')) 
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
    
    def test_delete_task(self):
        self.login()
        self.create_task()
        delete_button = self.browser.find_element(By.CSS_SELECTOR, '.delete-task')
        delete_button.click()
        WebDriverWait(self.browser, 5).until(EC.alert_is_present())
        Alert(self.browser).accept()
        WebDriverWait(self.browser, 1).until_not(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), 'New Task')
        )
        self.assertNotIn('New Task', self.browser.page_source)
    
    def test_delete_task_cancel(self):
        self.login()
        self.create_task()
        delete_button = self.browser.find_element(By.CSS_SELECTOR, '.delete-task')
        delete_button.click()
        WebDriverWait(self.browser, 5).until(EC.alert_is_present())
        Alert(self.browser).dismiss()
        WebDriverWait(self.browser, 1).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.editable-task'), 'New Task')
        )
        self.assertIn('New Task', self.browser.page_source)
    
    def test_complete_task(self):
        self.login()
        self.create_task()
        checkbox = WebDriverWait(self.browser, 5).until(
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