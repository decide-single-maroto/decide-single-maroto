from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView

@login_required(login_url='/')
def menu_view(request):
    return render(request, 'menu.html')
