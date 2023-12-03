from django.urls import path
from . import views


urlpatterns = [
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('question/new', views.QuestionCreateView,name='new_question'),
    path('allQuestion/', views.all_question, name='allQuestion'),
]
