from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.urls import reverse

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from bs4 import BeautifulSoup

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

    # def test_login(self):
    #     data = {'username': 'voter1', 'password': '123'}
    #     response = self.client.post('/authentication/login/', data, format='json')
    #     self.assertEqual(response.status_code, 200)

    #     token = response.json()
    #     self.assertTrue(token.get('token'))

    # def test_login_fail(self):
    #     data = {'username': 'voter1', 'password': '321'}
    #     response = self.client.post('/authentication/login/', data, format='json')
    #     self.assertEqual(response.status_code, 400)

    def test_login_google_auth(self):
        signin_url = reverse('signin')

        response = self.client.get(signin_url)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Login with Google')

        response = self.client.get('/authentication/google/login/?next=http://127.0.0.1:8000/base/')

        # Verifica que la respuesta sea una redirección a Google OAuth
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('https://accounts.google.com/o/oauth2'))


    # def test_logout(self):
    #     data = {'username': 'voter1', 'password': '123'}
    #     response = self.client.post('/authentication/login/', data, format='json')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

    #     token = response.json()
    #     self.assertTrue(token.get('token'))

    #     response = self.client.post('/authentication/logout/', token, format='json')
    #     self.assertEqual(response.status_code, 302)
