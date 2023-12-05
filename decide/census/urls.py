from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('export/', views.export_census, name='export_census'), # Adding the URL for exporting the census
    path('new/', views.new_census_form, name = 'new_census'),
    path('all_census/', views.all_census, name='all_census'),
    path('export_census/', views.export_census, name='export_census'),
    path('import_census/', views.import_census, name='import_census'),
]
