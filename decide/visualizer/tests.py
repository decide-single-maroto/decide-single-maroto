from django.test import TestCase
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from voting.models import Voting, Question
from census.models import Census

from selenium import webdriver
from selenium.webdriver.common.by import By

import time

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


    def test_visualizer_not_started(self):        
        q = Question(desc='test question')
        q.save()
        v = Voting(name='test voting not started', question_id=q.id)
        v.save()

        response = self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        votingState = self.driver.find_element(By.TAG_NAME,"h2").text

        self.assertTrue(votingState, "Voting not started")

    def test_visualizer_started(self):
        q = Question(desc = 'test question')
        q.save()
        v = Voting(name = 'test voting started', start_date = timezone.now(), question_id = q.id)
        v.save()

        response = self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}')
        votingState = self.driver.find_element(By.TAG_NAME, "h2").text
        
        self.assertTrue(votingState, "Voting started")

    def test_visualizer_closed(self):
        q = Question(desc = 'test question')
        q.save()
        v = Voting(name='test voting finished', end_date=timezone.now(), question_id = q.id)
        v.save()

        response = self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}')
        votingState = self.driver.find_element(By.TAG_NAME, "h2").text

        self.assertTrue(votingState, "Resultados:")

    def test_visualizerStarted_noCensus(self):
        q = Question(desc = 'test question')
        q.save()
        v = Voting(name = 'test voting started without census', start_date = timezone.now(), question_id = q.id)
        v.save()

        response = self.driver.get(f'{self.live_server_url}/visualizer/{v.pk}/')
        votingState = self.driver.find_element(By.ID, "participation").text == "-"

        self.assertTrue(votingState, "Voting started without census")

    def test_visualizer_started_withCensus_withoutParticipation(self):        
        question = Question(desc='test question')
        question.save()
        voting = Voting(name='test voting', start_date=timezone.now(), question_id=question.id)
        voting.save()

        census1 = Census(voter_id=1, voting_id=voting.id)
        census1.save()
        census2 = Census(voter_id=2, voting_id=voting.id)
        census2.save()

        self.driver.get(f'{self.live_server_url}/visualizer/{voting.pk}/')
        votingState = self.driver.find_element(By.ID, "participation").text == "0.0%"

        self.assertTrue(votingState, "Voting started with census and no participation")
