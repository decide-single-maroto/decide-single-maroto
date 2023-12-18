from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.urls import reverse

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authtoken.models import Token

from base import mods


class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        u = User(username='voter1')
        u.set_password('123')
        u.save()

        u2 = User(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

        try:
            existing_site = Site.objects.get(id=3)
            existing_site.delete()
        except ObjectDoesNotExist:
            pass

        site = Site.objects.create(
            id=3,
            domain="127.0.0.1:8000",
            name="127.0.0.1:8000"
        )

        social_app = SocialApp.objects.create(
            id=1,
            provider='google',
            name='decide-single-maroto',
            client_id='558970792437-0rlcb3qqajt40khtrd2goilcja5s6jh5.apps.googleusercontent.com',
            secret='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',
        )

        social_app.sites.add(site)
        social_app.save()

    def tearDown(self):
        self.client = None

    def test_login_google_auth(self):
        signin_url = reverse('signin')

        response = self.client.get(signin_url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Login with Google')

        response = self.client.get('/authentication/google/login/?next=http://127.0.0.1:8000/base/')

        # Verifica que la respuesta sea una redirección a Google OAuth
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('https://accounts.google.com/o/oauth2'))


    def test_logout(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 302)

    def assert_errors_in_response(self, response, expected_errors):

        # Verifica que existe la lista de errores
        self.assertContains(response, '<ul>', status_code=200)

        # Verifica que cada mensaje de error está presente en la lista
        for error in expected_errors:
            self.assertContains(response, f'<li>{error}</li>', status_code=200)

    def test_register(self):
        data_reg = {'email': 'reguser@reguser.com', 'username': 'reguser', 'password': 'password123', 'password_confirm': 'password123'}
        response_register = self.client.post('/authentication/signup', data_reg, format='json')

        self.assertEqual(response_register.status_code, 301)

        data_log = {'username': 'reguser', 'password': 'password123'}
        response_login = self.client.post('/', data_log, format='json')

        self.assertEqual(response_login.status_code, 200)

    def test_missing_fields(self):
        data = {}  # No proporcionar campos obligatorios
        response = self.client.post(reverse('register_user'), data, format='json')
        self.assertEqual(response.status_code, 200)  # Debería devolver la página de registro con errores
        expected_errors = ['All fields are required.']
        self.assert_errors_in_response(response, expected_errors)

    def test_duplicated_username(self):
        data_reg = {'email': 'duplicated@reguser.com', 'username': 'duplicated', 'password': 'password123', 'password_confirm': 'password123'}
        response_register = self.client.post(reverse('register_user'), data_reg, format='json')
        self.assertEqual(response_register.status_code, 200)

        data_reg_duplicated = {'email': 'duplicated2@reguser.com', 'username': 'duplicated', 'password': 'password123', 'password_confirm': 'password123'}
        response_register_duplicated = self.client.post(reverse('register_user'), data_reg_duplicated, format='json')
        self.assertEqual(response_register_duplicated.status_code, 200)
        expected_errors = ['The username is already in use.']
        self.assert_errors_in_response(response_register_duplicated, expected_errors)

    def test_password_mismatch(self):
        data = {
            'email': 'reguser@user.com', 
            'username': 'reguser', 
            'password': 'password123', 
            'password_confirm': 'password456'
        }
        response = self.client.post(reverse('register_user'), data, format='json')
        self.assertEqual(response.status_code, 200)
        expected_errors = ['The passwords do not match.']
        self.assert_errors_in_response(response, expected_errors)

    def test_password_short(self):
        data = {
            'email': 'reguser@user.com', 
            'username': 'reguser', 
            'password': '123', 
            'password_confirm': '123'
        }
        response = self.client.post(reverse('register_user'), data, format='json')
        self.assertEqual(response.status_code, 200)
        expected_errors = ['The password must have 8 characters at least.']
        self.assert_errors_in_response(response, expected_errors)






