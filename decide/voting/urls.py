from django.urls import path
from . import views


urlpatterns = [
    path('newVoting/', views.new_voting, name='newVoting'),
    path('allVotings/', views.all_votings, name='allVotings'),
    path('allVotings/<int:voting_id>', views.votings_detail, name='votings_detail'),
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('newAuth/', views.new_auth, name = 'newAuth'),
]
