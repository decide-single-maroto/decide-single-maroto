from django.shortcuts import render
from django.views.generic import TemplateView

class MenuView(TemplateView):
    def post(self, request):
        return render(request, 'menu.html')
    
    def get_template_names(self):
        return ['menu.html']
