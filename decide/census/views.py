from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census
import csv
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
import json

def export_census(request):
    selected_ids = request.GET.get('ids', '')
    try:
        selected_ids = [int(id) for id in selected_ids.split(',') if id]
    except ValueError:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid IDs provided'}), content_type='application/json')

    try:
        census_list = Census.objects.filter(id__in=selected_ids)
    except ValidationError:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid IDs provided'}), content_type='application/json')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="census_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Voting ID', 'Voter ID'])

    for census in census_list:
        writer.writerow([census.voting_id, census.voter_id])

    return response


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
