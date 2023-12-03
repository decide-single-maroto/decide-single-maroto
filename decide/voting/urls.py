from django.urls import path
from . import views


urlpatterns = [
    path('newVoting/', views.new_voting, name='new_voting'),
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('allVotings/', views.all_votings, name='allVotings'),
    path('newAuth/', views.new_auth, name = 'newAuth'),
    path('<int:voting_id>/edit/', views.edit_voting, name='edit_voting_detail'),
    path('start_voting', views.start_voting, name = 'start_voting'),
    path('stop_voting', views.stop_voting, name = 'stop_voting'),
    path('tally_voting', views.tally_voting, name = 'tally_voting'),
    path('question/new', views.QuestionCreateView,name='new_question'),
    path('allQuestion/', views.all_question, name='allQuestion'),
]
