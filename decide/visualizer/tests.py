from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from voting.models import Voting, Question
from census.models import Census
from selenium import webdriver
from selenium.webdriver.common.by import By
from django.utils import timezone

class VisualizerTestCase(StaticLiveServerTestCase):

    def setUp(self):
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

    def create_question(self, desc):
        return Question.objects.create(desc=desc)

    def create_voting(self, name, start_date=None, end_date=None, question_id=None):
        return Voting.objects.create(name=name, start_date=start_date, end_date=end_date, question_id=question_id)

    def create_census(self, voter_id, voting_id):
        return Census.objects.create(voter_id=voter_id, voting_id=voting_id)

    def test_visualizer_not_started(self):
        q = self.create_question('test question')
        v = self.create_voting('test voting not started', question_id=q.id)

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        voting_state = self.driver.find_element(By.TAG_NAME, "h2").text

        self.assertTrue(voting_state, "Voting not started")

    def test_visualizer_started(self):
        q = self.create_question('test question')
        v = self.create_voting('test voting started', start_date=timezone.now(), question_id=q.id)

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}')
        voting_state = self.driver.find_element(By.TAG_NAME, "h2").text
        
        self.assertTrue(voting_state, "Voting started")

    def test_visualizer_closed(self):
        q = self.create_question('test question')
        v = self.create_voting('test voting finished', end_date=timezone.now(), question_id=q.id)

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}')
        voting_state = self.driver.find_element(By.TAG_NAME, "h2").text

        self.assertTrue(voting_state, "Resultados:")

    def test_visualizer_started_no_census(self):
        q = self.create_question('test question')
        v = self.create_voting('test voting started without census', start_date=timezone.now(), question_id=q.id)

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        voting_state = self.driver.find_element(By.ID, "participation").text == "-"

        self.assertTrue(voting_state, "Voting started without census")

    def test_visualizer_started_with_census_without_participation(self):
        q = self.create_question('test question')
        v = self.create_voting('test voting', start_date=timezone.now(), question_id=q.id)
        self.create_census(1, v.id)
        self.create_census(2, v.id)

        self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        voting_state = self.driver.find_element(By.ID, "participation").text == "0.0%"

        self.assertTrue(voting_state, "Voting started with census and no participation")
