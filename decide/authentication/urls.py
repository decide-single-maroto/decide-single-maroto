from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import SigninView, GetUserView, LogoutView, RegisterView, RegisterUserView


urlpatterns = [
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view(), name='register'),
    path('singup/', RegisterUserView.as_view(), name='register_user'),
    path('', include('allauth.urls')),
]
