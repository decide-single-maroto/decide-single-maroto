import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.test import Client

from voting.forms import NewVotingForm, NewAuthForm
from .forms import QuestionForm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption
from datetime import datetime
class VotingTestCase(BaseTestCase):

    def test_update_voting_405(self):
        v = self.create_voting()
        data = {} #El campo action es requerido en la request
        self.login()
        response = self.client.post('/voting/{}/'.format(v.pk), data, format= 'json')
        self.assertEquals(response.status_code, 405)

    def test_create_voting_API(self):
        self.login()
        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

        voting = Voting.objects.get(name='Example')
        self.assertEqual(voting.desc, 'Description example')

    def test_to_string(self):
        #Crea un objeto votacion
        v = self.create_voting()
        #Verifica que el nombre de la votacion es test voting
        self.assertEquals(str(v),"test voting")
        #Verifica que la descripcion de la pregunta sea test question
        self.assertEquals(str(v.question),"test question")
        #Verifica que la primera opcion es option1 (2)
        self.assertEquals(str(v.question.options.all()[0]),"option 1 (2)")

    def setUp(self):
        question = Question.objects.create(id = 100, desc = 'Eres humano?', cattegory = "YES/NO")
        question.save()
        
        
        
        voting = Voting(id = 100,name='test voting', question=question)
        voting.save()
        self.voting = voting
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    def create_voting(self):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting()
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_question_yes_no_options(self):
      
        #Start voting and check options

        #login with user admin
        self.login()
      
        voting = self.voting
        voting.create_options_yes_no()
        
        self.assertEquals(voting.question.options.all()[0].option, "Yes")
        self.assertEquals(voting.question.options.all()[1].option, "No")

    def test_question_yes_no_deleting_options(self):
        
        self.login()
        q = Question(desc='test question yes/no',cattegory = "YES/NO")
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        
        v.save()
        v.create_options_yes_no()
        
        self.assertEquals(v.question.options.all()[0].option, "Yes")
        self.assertEquals(v.question.options.all()[1].option, "No")
        
        
     

    def test_update_voting(self):
        voting = self.create_voting()

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)


        
        
        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')

class LogInSuccessTests(StaticLiveServerTestCase):

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

    def successLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/")

class LogInErrorTests(StaticLiveServerTestCase):

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

    def usernameWrongLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)
        
        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("usuarioNoExistente")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("usuarioNoExistente")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[2]/div/div[1]/p').text == 'Please enter the correct username and password for a staff account. Note that both fields may be case-sensitive.')

    def passwordWrongLogIn(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("wrongPassword")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[2]/div/div[1]/p').text == 'Please enter the correct username and password for a staff account. Note that both fields may be case-sensitive.')

class QuestionsTests(StaticLiveServerTestCase):

    def setUp(self):
        #Load base test functionality for decide
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

        question = Question.objects.create(id = 100, desc = 'Eres humano?', cattegory = 'YES/NO')
        question.save()
        
        voting = Voting(id = 100,name='test voting', question=question)
        voting.save()

        
        super().setUp()
        self.voting = Voting.objects.get(id = 100)

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

        self.base.tearDown()
   
        
    def createQuestionSuccess(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/voting/question/add/")
        
        self.cleaner.find_element(By.ID, "id_desc").click()
        self.cleaner.find_element(By.ID, "id_desc").send_keys('Test')
        self.cleaner.find_element(By.ID, "id_options-0-number").click()
        self.cleaner.find_element(By.ID, "id_options-0-number").send_keys('1')
        self.cleaner.find_element(By.ID, "id_options-0-option").click()
        self.cleaner.find_element(By.ID, "id_options-0-option").send_keys('test1')
        self.cleaner.find_element(By.ID, "id_options-1-number").click()
        self.cleaner.find_element(By.ID, "id_options-1-number").send_keys('2')
        self.cleaner.find_element(By.ID, "id_options-1-option").click()
        self.cleaner.find_element(By.ID, "id_options-1-option").send_keys('test2')
        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/voting/question/")

    def createCensusEmptyError(self):
        self.cleaner.get(self.live_server_url+"/admin/login/?next=/admin/")
        self.cleaner.set_window_size(1280, 720)

        self.cleaner.find_element(By.ID, "id_username").click()
        self.cleaner.find_element(By.ID, "id_username").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").click()
        self.cleaner.find_element(By.ID, "id_password").send_keys("decide")

        self.cleaner.find_element(By.ID, "id_password").send_keys("Keys.ENTER")

        self.cleaner.get(self.live_server_url+"/admin/voting/question/add/")

        self.cleaner.find_element(By.NAME, "_save").click()

        self.assertTrue(self.cleaner.find_element_by_xpath('/html/body/div/div[3]/div/div[1]/div/form/div/p').text == 'Please correct the errors below.')
        self.assertTrue(self.cleaner.current_url == self.live_server_url+"/admin/voting/question/add/")

class VotingModelTestCase(BaseTestCase):
    def setUp(self):
        q = Question(desc='Descripcion')
        q.save()
        
        opt1 = QuestionOption(question=q, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q, option='opcion 2')
        opt1.save()

        self.v = Voting(name='Votacion', question=q)
        self.v.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.v = None

    def testExist(self):
        v=Voting.objects.get(name='Votacion')
        self.assertEquals(v.question.options.all()[0].option, "opcion 1")

class VotingFrontEndTestCase(TestCase):
    def setUp(self):

        self.client = Client()
        self.user_admin = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.user_no_admin = get_user_model().objects.create_user(username = 'noadmin', password='noadmin')

        self.question = Question(desc='¿Pregunta de ejemplo?')
        self.question.save()

        self.auth = Auth(name = 'authDeEjmplo', url = 'http://localhost:8000')
        self.auth.save()

    def test_new_voting_view_with_non_staff_user(self):
        self.client.force_login(self.user_no_admin)

        response = self.client.get(reverse('new_voting'))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

    def test_new_voting_view_with_staff_user(self):
        self.client.force_login(self.user_admin)

        response = self.client.get(reverse('new_voting'))
        self.assertEqual(response.status_code, 200)

        self.assertIn('form', response.context)
        form = response.context['form']

        self.assertIsInstance(form, NewVotingForm)

        selected_model = 'IDENTITY'

        data = {
            'id': 100,
            'name': 'Nombre de la votación',
            'desc': 'Descripción de la votación',
            'question': Question.objects.create(desc='¿Pregunta de ejemplo?').id,
            'auths': Auth.objects.create(name = 'authDeEjmplo', url = 'http://localhost:8000').id, 
            'model': selected_model,
            'seats': 0,
        }

        response_post = self.client.post(reverse('new_voting'), data)
        self.assertEqual(response_post.status_code, 302)



    def test_edit_voting_with_non_staff_user(self):
        self.client.force_login(self.user_no_admin)

        voting = Voting.objects.create(name='Votación de ejemplo', desc='Descripción de la votación', question = self.question, model='IDENTITY', seats=0)
        voting.auths.set([self.auth])

        response = self.client.get(reverse('edit_voting_detail', args=[voting.id]))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

    def test_edit_voting_with_staff_user(self):
        self.client.force_login(self.user_admin)

        voting = Voting.objects.create(name='Votación de ejemplo', desc='Descripción de la votación', question = self.question, model='IDENTITY', seats=0)
        voting.auths.set([self.auth])

        url = reverse('edit_voting_detail', args=[voting.id])

        # Verificar la rama else
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)

        data = {'name': 'Nuevo nombre',
                'desc': 'Nueva descripción',
                'question': voting.question.id,
                'auths': [auth.id for auth in voting.auths.all()],
                'model': voting.model,
                'seats': voting.seats                 
        }

        response = self.client.post(url, data)


        self.assertEqual(response.status_code, 302)
        

        voting.refresh_from_db()
        self.assertEqual(voting.name, 'Nuevo nombre')
        self.assertEqual(voting.desc, 'Nueva descripción')



    def test_all_voting_view_with_no_staf(self):
        self.client.force_login(self.user_no_admin)
        response = self.client.get(reverse('allVotings'))
        
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

    def test_all_voting_view_with_staf(self):
        self.client.force_login(self.user_admin)
        response = self.client.get(reverse('allVotings'))

        self.assertEqual(response.status_code, 200)

    def test_new_auth_view_with_no_staff_user(self):
        self.client.force_login(self.user_no_admin)

        response = self.client.get(reverse('newAuth'))

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

    def test_new_auth_view_with_staff_user(self):
        self.client.force_login(self.user_admin)

        response = self.client.get(reverse('newAuth'))
        self.assertEqual(response.status_code, 200)

        self.assertIn('form', response.context)
        form = response.context['form']

        self.assertIsInstance(form, NewAuthForm)

        data = {
            id: 10,
            'name': 'Nombre de auth',
            'url': 'paginaprueba.com',
            'me': True,
        }

        response = self.client.post(reverse('newAuth'), data)
        self.assertEqual(response.status_code, 302)

    def test_start_stop_tally_voting_no_staff_user(self):
        self.client.force_login(self.user_no_admin)
        response = self.client.get(reverse('start_voting'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('stop_voting'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('tally_voting'))
        self.assertEqual(response.status_code, 403)

    # def test_start_voting_staff_user(self):
    #     self.client.force_login(self.user_admin)

    #     voting = Voting.objects.create(name='Votación de ejemplo', desc='Descripción de la votación', question = self.question, model='IDENTITY', seats=0)
    #     voting.auths.set([self.auth])
    #     voting.save()

    #     response_post = self.client.post(reverse('start_voting'), {'voting_id': voting.id})

    #     self.assertEqual(response_post.status_code, 302)

    #     updated_voting = Voting.objects.get(id=voting.id)
    #     self.assertIsNotNone(updated_voting.start_date)
    #     self.assertIsNotNone(updated_voting.pub_key)

    # def test_stop_voting_staff_user(self):
    #     self.client.force_login(self.user_admin)

    #     voting = Voting.objects.create(name='Votación de ejemplo', desc='Descripción de la votación', question = self.question, model='IDENTITY', seats=0)
    #     voting.auths.set([self.auth])
    #     voting.save()

    #     response_post = self.client.post(reverse('stop_voting'), {'voting_id': voting.id})

    #     self.assertEqual(response_post.status_code, 302)

    #     updated_voting = Voting.objects.get(id=voting.id)
    #     self.assertIsNotNone(updated_voting.end_date)
        
class CreateQuestionView(TestCase):
    
    def test_create_view(self):
        
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
    
        url = reverse('new_question')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Desc', count=1)
        
    def test_create_question_with_form(self):
        
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        form_data = {
            'desc': 'Prueba',
            'cattegory': 'OPTIONS',
            # Agrega más campos según tu formulario
        }
        
        url = reverse('new_question')
        response_post = self.client.post(url, data=form_data)
        self.assertEqual(response_post.status_code, 200)
        
        question = Question.objects.get(desc="Prueba")
        self.assertEqual(question.desc,"Prueba")
    
    def test_create_question_no_admin(self):
        url = reverse('new_question')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'403.html')
    
    def test_create_question_with_error(self):
        
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        form = QuestionForm(data={})

        self.assertFalse(form.is_valid())
        self.assertTrue('desc' in form.errors)
        
class QuestionAllView(TestCase):
    
    def setUp(self):
        q = Question(desc='Descripcion')
        q.save()
        
        opt1 = QuestionOption(question=q, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q, option='opcion 2')
        opt1.save()

        q1 = Question(desc='Descripcion2')
        q1.save()
        
        opt1 = QuestionOption(question=q1, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q1, option='opcion 2')
        opt1.save()

        q2 = Question(desc='Descripcion3')
        q2.save()
        
        opt1 = QuestionOption(question=q2, option='opcion 1')
        opt1.save()
        opt1 = QuestionOption(question=q2, option='opcion 2')
        opt1.save()

        super().setUp()
        
    def test_all_question_view(self):
        
        self.client = Client()
        self.user = get_user_model().objects.create_user(username = 'adminadmin', password='adminadmin', is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        
        url = reverse('allQuestion')
        response = self.client.get(url)
        
        self.assertTemplateUsed(response,'all_question.html')
        self.assertContains(response,"Descripcion")
        self.assertContains(response,"Descripcion2")
        self.assertContains(response,"Descripcion3")
        
    def test_all_question_without_admin(self):
        url = reverse('new_question')
        response = self.client.get(url)
        self.assertTemplateUsed(response,'403.html')