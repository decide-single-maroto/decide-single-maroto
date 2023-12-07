from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_401_UNAUTHORIZED
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import authenticate, login, logout

from .forms import LoginForm

from .serializers import UserSerializer

class SigninView(TemplateView):
    def post(self, request):
        form_class = LoginForm(request.POST)

        if form_class.is_valid():
            username = form_class.cleaned_data.get('username')
            password = form_class.cleaned_data.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("menuSignin")
            else:
                error_message="Usuario y/o contraseña incorrecto/a"
        else:
            error_message = "Error al cargar el formulario"

        return render(request, 'login.html', {'form': form_class, 'msg': error_message})
    
    def get(self, request):
        form_class = LoginForm(None)
        if request.user.is_authenticated:
            return render(request, 'base.html')
        return render(request, 'login.html', {'form': form_class, 'msg': None})
    
class MenuView(TemplateView):
    def post(self, request):
        return render(request, 'menu.html')
    
    def get_template_names(self):
        return ['menu.html']


class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        return Response(UserSerializer(tk.user, many=False).data)

class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect('/')
    
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect('/')

class RegisterView(APIView):
    def get(self, request):
        
        return render(request, 'register.html')
    
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        if not tk.user.is_superuser:
            username = request.data.get('username', '')
            pwd = request.data.get('password', '')
            if not username or not pwd:
                return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)

class RegisterUserView(APIView):
    def get(self, request):
        return render(request, 'register.html')
    
    def post(self, request):
        username = request.data.get('username', '')
        pwd = request.data.get('password', '')
        pwd_confirm = request.data.get('password_confirm', '')
        email = request.data.get('email', '')
        errors = []

        if not username or not pwd or not pwd_confirm or not email:
            errors.append('All fields are required.')

        if User.objects.filter(username=username).exists():
            errors.append('The username is already in use.')

        if User.objects.filter(email=email).exists():
            errors.append('This email is already registered.')

        if pwd != pwd_confirm:
            errors.append('The passwords do not match.')

        if errors:
            return render(request, 'register.html', {'errors': errors})

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            message = 'Account successfully created.'
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return render(request, 'login.html', {'message': message})
