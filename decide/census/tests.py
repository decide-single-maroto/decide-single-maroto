from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from django.http import HttpResponseBadRequest

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import json

from .models import Census
from base.tests import BaseTestCase
from datetime import datetime
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from .admin import CensusAdmin, VotingIdFilter
from .views import export_census

from .forms import NewCensusForm

class CensusTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def test_check_vote_permissions(self):
        response = self.client.get('/census/{}/?voter_id={}'.format(1, 2), format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), 'Invalid voter')

        response = self.client.get('/census/{}/?voter_id={}'.format(1, 1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Valid voter')

    def test_list_voting(self):
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'voters': [1]})

    def test_add_new_voters_conflict(self):
        data = {'voting_id': 1, 'voters': [1]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_add_new_voters(self):
        data = {'voting_id': 2, 'voters': [1,2,3,4]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data.get('voters')), Census.objects.count() - 1)

    def test_destroy_voter(self):
        data = {'voters': [1]}
        response = self.client.delete('/census/{}/'.format(1), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, Census.objects.count())


class CensusTest(StaticLiveServerTestCase):
    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()
    
    def createCensusSuccess(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys(now.strftime("%m%d%M%S"))
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census")

    def createCensusEmptyError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")

        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

    def createCensusValueError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/census/census/add")
        now = datetime.now()
        self.cleaner.find_element(By.ID, "id_voting_id").click()
        self.cleaner.find_element(By.ID, "id_voting_id").send_keys('64654654654654')
        self.cleaner.find_element(By.ID, "id_voter_id").click()
        self.cleaner.find_element(By.ID, "id_voter_id").send_keys('64654654654654')
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/census/census/add")

class CensusFormTest(TestCase):
    
    def test_census_form_view(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        url = reverse('new_census')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response,'form.html')
        self.assertContains(response,"voting_id")
        
    def test_census_form_no_admin(self):
        url = reverse('new_census')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code,403)
        
    def test_census_create(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        url = reverse('new_census')
        form_data = {
            'voting_id': 1,
            'voter_id':1,
        }
        response_post = self.client.post(url, data=form_data)
        self.assertEqual(response_post.status_code, 302)
        
        question = Census.objects.get(voting_id = 1)
        self.assertEqual(question.voter_id,1)
        
    def test_census_create_with_errors(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        form_data = {
            'voter_id': 1,
        }
        form = NewCensusForm(form_data)

        self.assertFalse(form.is_valid())
        self.assertTrue('voting_id' in form.errors)
class VotingIdFilterTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.census1 = Census.objects.create(voting_id=1, voter_id=1)
        self.census2 = Census.objects.create(voting_id=2, voter_id=2)

    def test_lookups(self):
        filter_instance = VotingIdFilter(
            request=self.factory.get('/admin/census/census/'),
            params={'voting_id': '1'},
            model=Census,
            model_admin=None
        )
        lookups = filter_instance.lookups(None, None)
        # Verificar igualdad sin importar el orden
        self.assertCountEqual(lookups, [(1, '1'), (2, '2')])

    def test_queryset(self):
        filter_instance = VotingIdFilter(
            request=self.factory.get('/admin/census/census/'),
            params={'voting_id': '1'},
            model=Census,
            model_admin=None
        )
        queryset = filter_instance.queryset(None, Census.objects.all())
        # Verificar si el elemento está presente en el conjunto de resultados
        self.assertIn(repr(self.census1), [repr(item) for item in queryset])

    def test_queryset_with_no_value(self):
        filter_instance = VotingIdFilter(
            request=self.factory.get('/admin/census/census/'),
            params={'voting_id': None},  # Asegúrate de pasar None como valor
            model=Census,
            model_admin=None
        )
        queryset = filter_instance.queryset(None, Census.objects.all())
        # Verificar si el queryset no es None y luego verificar la presencia de elementos
        self.assertIsNotNone(queryset)
        if queryset is not None:
            self.assertIn(repr(self.census1), [repr(item) for item in queryset])
            self.assertIn(repr(self.census2), [repr(item) for item in queryset])

class CensusAdminExportSelectedTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='admin', password='admin')
        self.census_admin = CensusAdmin(Census, admin_site=None)

        # Create some Census objects for testing
        self.census1 = Census.objects.create(voting_id=1, voter_id=1)
        self.census2 = Census.objects.create(voting_id=2, voter_id=2)

    def test_export_selected(self):
        request = self.factory.post('/admin/census/census/', {'action': 'export_selected', '_selected_action': [self.census1.id, self.census2.id]})
        request.user = self.user

        queryset = Census.objects.filter(id__in=[self.census1.id, self.census2.id])

        response = CensusAdmin.export_selected(modeladmin=None, request=request, queryset=queryset)

        self.assertIsInstance(response, HttpResponse)

        lines = response.getvalue().decode().split('\n')
        self.assertEqual(lines[0].strip(), 'Voting ID,Voter ID')
        self.assertEqual(lines[1].strip(), '1,1')
        self.assertEqual(lines[2].strip(), '2,2')

class CensusExportTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.census1 = Census.objects.create(voting_id=1, voter_id=1)
        self.census2 = Census.objects.create(voting_id=2, voter_id=2)

    def test_export_census(self):
        request = self.factory.get('/export_census/', {'ids': f'{self.census1.id},{self.census2.id}'})
        request.user = self.user

        response = export_census(request)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.get('Content-Type'), 'text/csv')
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="census_export.csv"')

        lines = response.getvalue().decode().split('\n')
        self.assertEqual(lines[0].strip(), 'Voting ID,Voter ID')
        self.assertEqual(lines[1].strip(), '1,1')
        self.assertEqual(lines[2].strip(), '2,2')

    def test_export_census_empty(self):
        request = self.factory.get('/export_census/', {'ids': ''})
        request.user = self.user

        response = export_census(request)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.get('Content-Type'), 'text/csv')
        self.assertEqual(response.get('Content-Disposition'), 'attachment; filename="census_export.csv"')

        # Verify that the CSV file is empty
        self.assertEqual(response.getvalue().decode().strip(), 'Voting ID,Voter ID')

    def test_export_census_invalid_id(self):
        request = self.factory.get('/export_census/', {'ids': 'invalid_id'})
        request.user = self.user

        response = export_census(request)

        self.assertIsInstance(response, HttpResponseBadRequest)
        self.assertEqual(response.get('Content-Type'), 'application/json')

        # Verificar el contenido JSON
        content = json.loads(response.content.decode())
        self.assertEqual(content['error'], 'Invalid IDs provided')
