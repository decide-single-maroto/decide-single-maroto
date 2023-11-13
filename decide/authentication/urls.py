from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import MenuView, SigninView, GetUserView, LogoutView, RegisterView


urlpatterns = [
    path('login/', obtain_auth_token),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('signin/', SigninView.as_view(), name='signin'),
    path('menu', MenuView.as_view(), name='menuSignin'),
    path('', include('allauth.urls')),
]
