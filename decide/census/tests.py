from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from django.core.files.uploadedfile import SimpleUploadedFile

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import json

from .models import Census
from voting.models import Voting, Question
from base.tests import BaseTestCase
from datetime import datetime
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.urls import reverse
from .admin import VotingIdFilter
from .views import all_census, delete_census, export_census, validate_ids, validate_and_read_csv, import_census
from .forms import NewCensusForm

from unittest.mock import patch
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO





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
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        Census.objects.all().delete()  # Clear the database before each test

    def test_census_form_view(self):
        url = reverse('new_census')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'new_census_form.html')
        self.assertContains(response, "voting_id")

    def test_census_form_no_admin(self):
        # Create a non-admin user and log in as that user
        non_admin_user = get_user_model().objects.create_user(username='nonadmin', password='nonadmin')
        self.client.force_login(non_admin_user)

        url = reverse('new_census')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Log back in as the admin user for the other tests
        self.client.force_login(self.user)

    def test_census_create(self):
        # Arrange
        question = Question.objects.create(desc='test question', cattegory='YES/NO')
        Voting.objects.create(id=20, name='test', question=question)
        User.objects.create(id=3, username='test', password='test')

        url = reverse('new_census')
        form_data = {
            'voting_id': 20,
            'voter_id': 3,
        }

        # Act: Post the form data and create a census
        response_post = self.client.post(url, data=form_data)

        # Assert: Check the response status code and the created census
        self.assertEqual(response_post.status_code, 302)
        census = Census.objects.get(voting_id=20)
        self.assertEqual(census.voter_id, 3)

        # Act: Try to create another census with the same voting_id and voter_id
        response_post = self.client.post(url, data=form_data)

        # Assert: Check the response status code
        self.assertEqual(response_post.status_code, 200)

    def test_census_create_with_errors(self):
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

class CensusActionsTest(TestCase):
    def setUp(self):
        Census.objects.all().delete()

        self.factory = RequestFactory()
        self.user1 = User.objects.create_user(username='test1', password='test')
        self.user2 = User.objects.create_user(username='test2', password='test')
        question = Question.objects.create(desc='test question', cattegory='YES/NO')
        self.voting = Voting.objects.create(name='test', question=question)

        self.census1 = Census.objects.create(voting_id=self.voting.id, voter_id=self.user1.id)
        self.census2 = Census.objects.create(voting_id=self.voting.id, voter_id=self.user2.id)

        self.factory = RequestFactory()
        self.middleware = SessionMiddleware(lambda req: HttpResponse())

    def test_all_census(self):
        request = self.factory.get('/census/all_census/')
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        response = all_census(request)

        self.assertEqual(response.status_code, 200)

    @patch('census.views.messages')
    def test_delete_census(self, mock_messages):
        # Verificar si ya existe un censo con la misma combinación de voting_id y voter_id
        census = Census.objects.filter(voting_id=self.voting.id, voter_id=self.user1.id).first()
        if not census:
            # Si no existe, crear un nuevo censo
            census = Census.objects.create(voting_id=self.voting.id, voter_id=self.user1.id)

        # Crear una solicitud POST falsa
        request = self.factory.post('/census/delete_census/', {'selected_censuses': str(census.id)})
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        delete_census(request)

        self.assertFalse(Census.objects.filter(id=census.id).exists())

    @patch('census.views.messages')
    def test_delete_all_census(self, mock_messages):
        # Crear una solicitud POST falsa sin censos seleccionados
        request = self.factory.post('/census/delete_census/', {})
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        delete_census(request)

        # Verificar que todos los censos han sido eliminados
        self.assertFalse(Census.objects.all().exists())

    @patch('census.views.messages')
    def test_delete_nonexistent_census(self, mock_messages):
        # Crear una solicitud POST falsa con un ID de censo inexistente
        request = self.factory.post('/census/delete_census/', {'selected_censuses': '999'})
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        delete_census(request)

        # Verificar que se llamó a messages.error con el mensaje correcto
        mock_messages.error.assert_called_once_with(request, 'No existen censos con los IDs proporcionados.')

    def test_export_census(self):
        # Crear una solicitud GET falsa
        request = self.factory.get('/census/export_census/')
        request.user = self.user1

        response = export_census(request)

        self.assertEqual(response['Content-Type'], 'text/csv')

        expected_content = f'voting_id,voter_id\r\n{self.voting.id},{self.user1.id}\r\n{self.voting.id},{self.user2.id}\r\n'
        self.assertEqual(response.content.decode(), expected_content)

    def test_export_census_selected_ids(self):
        # Crear una solicitud GET falsa con ids seleccionados
        request = self.factory.get('/census/export_census/', {'ids': f'{self.census1.id},{self.census2.id}'})
        request.user = self.user1

        response = export_census(request)

        self.assertEqual(response['Content-Type'], 'text/csv')

        expected_content = f'voting_id,voter_id\r\n{self.census1.voting_id},{self.census1.voter_id}\r\n{self.census2.voting_id},{self.census2.voter_id}\r\n'
        self.assertEqual(response.content.decode(), expected_content)

    def test_export_census_invalid_selected_ids(self):
        # Crear una solicitud GET falsa con ids inválidos
        request = self.factory.get('/census/export_census/', {'ids': 'invalid_id'})
        request.user = self.user1

        response = export_census(request)

        # Verificar que la respuesta es un error 400
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), json.dumps({'error': 'Invalid IDs provided'}))

    def test_validate_ids(self):
        self.assertTrue(validate_ids(self.voting.id, self.user1.id))

        self.assertFalse(validate_ids(999, self.user1.id))

        self.assertFalse(validate_ids(self.voting.id, 999))

    def test_validate_and_read_csv(self):
        # Crear un archivo CSV falso
        csv_content = f'voting_id,voter_id\n{self.voting.id},{self.user1.id}\n'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode())

        census_list, error = validate_and_read_csv(csv_file)

        if census_list is not None:
            self.assertEqual(len(census_list), 1)
            self.assertEqual(census_list[0].voting_id, self.voting.id)
            self.assertEqual(census_list[0].voter_id, self.user1.id)
        else:
            self.assertEqual(error, 'El archivo contiene censos ya existentes.')

    def test_validate_and_read_csv_invalid_headers(self):
        # Crear un archivo CSV falso con encabezados inválidos
        csv_content = 'invalid_header1,invalid_header2\n1,1\n'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode())

        census_list, error = validate_and_read_csv(csv_file)

        self.assertIsNone(census_list)
        self.assertEqual(error, 'El archivo CSV debe tener dos columnas: voting_id y voter_id.')

    def test_validate_and_read_csv_non_integer_values(self):
        # Crear un archivo CSV falso con valores no enteros
        csv_content = 'voting_id,voter_id\n1,non_integer_value\n'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode())

        census_list, error = validate_and_read_csv(csv_file)

        self.assertIsNone(census_list)
        self.assertEqual(error, 'Todos los valores deben ser enteros.')

    def test_validate_and_read_csv_non_existent_data(self):
        # Crear un archivo CSV falso con datos inexistentes
        csv_content = 'voting_id,voter_id\n999,999\n'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode())

        census_list, error = validate_and_read_csv(csv_file)

        self.assertIsNone(census_list)
        self.assertEqual(error, 'El archivo contiene datos no existentes en la base de datos.')

    @patch('census.views.validate_and_read_csv')
    @patch('census.views.messages')
    def test_import_census(self, mock_messages, mock_validate_and_read_csv):
        csv_content = f'voting_id,voter_id\n{self.voting.id},{self.user1.id}\n'
        csv_file = InMemoryUploadedFile(BytesIO(csv_content.encode()), 'file', 'test.csv', 'text/csv', len(csv_content), None)
        csv_file_content = csv_file.read()  # Guardar el contenido del archivo en una variable

        # Crear una copia del archivo csv_file
        csv_file_copy = InMemoryUploadedFile(BytesIO(csv_file_content), 'file', 'test.csv', 'text/csv', len(csv_file_content), None)

        # Crear una solicitud POST falsa
        request = self.factory.post('/census/import_census/', {'csv_file': csv_file_copy})
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        # Configurar validate_and_read_csv para devolver un objeto Census
        mock_validate_and_read_csv.return_value = ([Census(voting_id=self.voting.id, voter_id=self.user1.id)], None)

        # Llamar a la función import_census
        import_census(request)

        # Verificar que se llamó a validate_and_read_csv y que se creó un censo
        mock_validate_and_read_csv.assert_called_once()
        called_with = mock_validate_and_read_csv.call_args[0][0]
        self.assertEqual(called_with.read(), csv_file_content)
        self.assertTrue(Census.objects.filter(voting_id=self.voting.id, voter_id=self.user1.id).exists())
    
    @patch('census.views.messages')
    def test_import_census_no_file_uploaded(self, mock_messages):
        # Crear una solicitud POST falsa sin archivo
        request = self.factory.post('/census/import_census/')
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        # Llamar a la función import_census
        response = import_census(request)

        # Verificar que se mostró un mensaje de error
        mock_messages.error.assert_called_once_with(request, 'No se ha subido ningún archivo CSV')

        # Verificar que la respuesta es una redirección
        self.assertEqual(response.status_code, 302)

    @patch('census.views.messages')
    def test_import_census_non_csv_file(self, mock_messages):
        # Crear un archivo falso que no es un archivo CSV
        non_csv_file = SimpleUploadedFile('test.txt', b'This is not a CSV file.')

        # Crear una solicitud POST falsa con el archivo no CSV
        request = self.factory.post('/census/import_census/', {'csv_file': non_csv_file})
        self.middleware.process_request(request)
        request.session.save()

        request.user = self.user1

        # Llamar a la función import_census
        response = import_census(request)

        # Verificar que se mostró un mensaje de error
        mock_messages.error.assert_called_once_with(request, 'El archivo debe ser un archivo CSV.')

        # Verificar que la respuesta es una redirección
        self.assertEqual(response.status_code, 302)