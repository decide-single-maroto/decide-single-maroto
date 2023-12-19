from django.db import transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import  render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.template import loader
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from base.perms import UserIsStaff
from .models import Census
from voting.models import Voting
from .forms import NewCensusForm, ImportCensusForm
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)
import csv
import json
import io



def all_census(request):
    census_list = Census.objects.all()

    context = {
        'census_list': census_list,
    }
    return render(request, 'all_census.html', context)

def delete_census(request):
    if request.method == 'POST':
        census_ids = request.POST.get('selected_censuses', '').split(',')
        if not census_ids or not census_ids[0]:
            # No se seleccionó ningún censo, eliminar todos
            Census.objects.all().delete()
            messages.success(request, 'Todos los censos han sido eliminados.')
            return redirect('all_census')

        censuses = Census.objects.filter(id__in=census_ids)
        if not censuses.exists():
            messages.error(request, 'No existen censos con los IDs proporcionados.')
        else:
            censuses.delete()
            messages.success(request, 'Censos eliminados correctamente.')

    return redirect('all_census')

def export_census(request):
    selected_ids = request.GET.get('ids', '')
    try:
        selected_ids = [int(id) for id in selected_ids.split(',') if id]
    except ValueError:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid IDs provided'}), content_type='application/json')

    if not selected_ids:
        # If no IDs are selected, export all census data
        census_list = Census.objects.all()
    else:
        try:
            # Filter the census based on the selected IDs
            census_list = Census.objects.filter(id__in=selected_ids)
        except IntegrityError:
            return HttpResponseBadRequest(json.dumps({'error': 'IDs no válidos'}), content_type='application/json')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="census_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['voting_id', 'voter_id'])

    for census in census_list:
        writer.writerow([census.voting_id, census.voter_id])

    return response

def validate_ids(voting_id, voter_id):
    if not Voting.objects.filter(id=voting_id).exists():
        return False

    if not User.objects.filter(id=voter_id).exists():
        return False

    return True

def validate_and_read_csv(csv_file):
    try:
        # Decodificar el archivo CSV y crear un lector de CSV
        dataset = csv_file.read().decode('utf-8')
        io_string = io.StringIO(dataset)
        csv_reader = csv.reader(io_string, delimiter=',')

        # Leer la primera línea del archivo CSV (encabezados)
        headers = next(csv_reader)

        # Verificar que los encabezados son correctos
        if len(headers) != 2 or headers[0] != 'voting_id' or headers[1] != 'voter_id':
            return None, 'El archivo CSV debe tener dos columnas: voting_id y voter_id.'

        new_census_list = []
        for row in csv_reader:
            try:
                voting_id = int(row[0])
                voter_id = int(row[1])
            except ValueError:
                return None, 'Todos los valores deben ser enteros.'
            if not validate_ids(voting_id, voter_id):
                return None, 'El archivo contiene datos no existentes en la base de datos.'
            elif Census.objects.filter(voting_id=voting_id, voter_id=voter_id).exists():
                return None, 'El archivo contiene censos ya existentes.'
            else:
                # Crear un nuevo objeto Census
                new_census = Census(voting_id=voting_id, voter_id=voter_id)
                new_census_list.append(new_census)

        return new_census_list, None
    except Exception as e:
        return None, f'Error al leer el archivo CSV: {str(e)}'

def import_census(request):
    ImportCensusForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'No se ha subido ningún archivo CSV')
            return redirect('all_census')
        elif not csv_file.name.endswith('.csv'):
            messages.error(request, 'El archivo debe ser un archivo CSV.')
            return redirect('all_census')
        else:
            new_census_list, error = validate_and_read_csv(csv_file)
            if error:
                messages.error(request, error)
                return redirect('all_census')

            # Verificar si cada censo ya existe antes de agregarlo a new_census_list
            unique_census_list = [census for census in new_census_list
                                  if not Census.objects.filter(voting_id=census.voting_id,
                                                               voter_id=census.voter_id).exists()]

            messages.success(request, 'Censo importado correctamente.')
            with transaction.atomic():
                Census.objects.bulk_create(unique_census_list)

            return redirect('all_census')

    return redirect('all_census')

class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):
    
    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')
    
def new_census_form(request):
    form = NewCensusForm()
    
    if not request.user.is_staff:
        template = loader.get_template('403.html')
        return HttpResponseForbidden(template.render({}, request))

    if request.method == 'POST':
        form = NewCensusForm(request.POST, request.FILES)

        if form.is_valid():
            voting_id = form.cleaned_data.get('voting_id')
            voter_id = form.cleaned_data.get('voter_id')

            if not validate_ids(voting_id, voter_id):
                request.session['form_messages'] = [{'message': 'Voting ID o Voter ID inválidos.', 'tag': 'error'}]
            else:
                try:
                    item = form.save(commit=False)
                    item.save()
                    request.session['form_messages'] = [{'message': 'Censo creado exitosamente.', 'tag': 'success'}]
                    return redirect('new_census')
                except IntegrityError:
                    print("IntegrityError caught")
                    request.session['form_messages'] = [{'message': 'Censos con este Voting ID o Voter Id ya existen', 'tag': 'error'}]
        else:
            request.session['form_messages'] = [{'message': f'{field.capitalize()}: {error}', 'tag': 'error'}
                                                for field, errors in form.errors.items() for error in errors]
            if '__all__' in form.errors:
                for error in form.errors['__all__']:
                    if 'already exists' in error:
                        request.session['form_messages'] = [{'message': 'Censos con este Voting ID o Voter ID ya existen', 'tag': 'error'}]

    messages = request.session.get('form_messages', None)
    response = render(request, 'new_census_form.html', {
        'form': form,
        'title': 'Nuevo Censo',
        'messages': messages,
    })

    if 'form_messages' in request.session:
        del request.session['form_messages']

    return response
