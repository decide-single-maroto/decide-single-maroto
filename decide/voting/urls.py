from django.urls import path
from . import views


urlpatterns = [
    path('newVoting/', views.new_voting, name='new_voting'),
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('allVotings/', views.all_votings, name='allVotings'),
    path('newAuth/', views.new_auth, name = 'newAuth'),
]