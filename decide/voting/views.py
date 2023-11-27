import django_filters.rest_framework
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.template import loader
from django.shortcuts import get_object_or_404, render, redirect
from rest_framework import generics, status
from rest_framework.response import Response

from .models import Question, QuestionOption, Voting
from .serializers import SimpleVotingSerializer, VotingSerializer
from base.perms import UserIsStaff

from base.models import Auth

from .forms import NewVotingForm


class VotingView(generics.ListCreateAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_fields = ('id', )

    def get(self, request, *args, **kwargs):
        idpath = kwargs.get('voting_id')
        self.queryset = Voting.objects.all()
        version = request.version
        if version not in settings.ALLOWED_VERSIONS:
            version = settings.DEFAULT_VERSION
        if version == 'v2':
            self.serializer_class = SimpleVotingSerializer

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        for data in ['name', 'desc', 'question', 'question_opt']:
            if not data in request.data:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)

        question = Question(desc=request.data.get('question'))
        question.save()
        for idx, q_opt in enumerate(request.data.get('question_opt')):
            opt = QuestionOption(question=question, option=q_opt, number=idx)
            opt.save()
        voting = Voting(name=request.data.get('name'), desc=request.data.get('desc'),
                question=question)
        voting.save()

        auth, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        auth.save()
        voting.auths.add(auth)
        return Response({}, status=status.HTTP_201_CREATED)

    def create_yes_no_options(self,request):
        question = self

class VotingUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    permission_classes = (UserIsStaff,)

    def put(self, request, voting_id, *args, **kwars):
        action = request.data.get('action')
        if not action:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        voting = get_object_or_404(Voting, pk=voting_id)
        msg = ''
        st = status.HTTP_200_OK
        if action == 'start':
            if voting.start_date:
                msg = 'Voting already started'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.start_date = timezone.now()
                voting.save()
                msg = 'Voting started'
        elif action == 'stop':
            if not voting.start_date:
                msg = 'Voting is not started'
                st = status.HTTP_400_BAD_REQUEST
            elif voting.end_date:
                msg = 'Voting already stopped'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.end_date = timezone.now()
                voting.save()
                msg = 'Voting stopped'
        elif action == 'tally':
            if not voting.start_date:
                msg = 'Voting is not started'
                st = status.HTTP_400_BAD_REQUEST
            elif not voting.end_date:
                msg = 'Voting is not stopped'
                st = status.HTTP_400_BAD_REQUEST
            elif voting.tally:
                msg = 'Voting already tallied'
                st = status.HTTP_400_BAD_REQUEST
            else:
                voting.tally_votes(request.auth.key)
                msg = 'Voting tallied'
        else:
            msg = 'Action not found, try with start, stop or tally'
            st = status.HTTP_400_BAD_REQUEST
        return Response(msg, status=st)

def new_voting(request):
    form = NewVotingForm()
    if not request.user.is_staff:
        template = loader.get_template('403.html')
        return HttpResponseForbidden(template.render({}, request))
    
    if request.method == 'POST':
        form = NewVotingForm(request.POST, request.FILES)

        if form.is_valid():
            item=form.save(commit=False)
            item.save()

            return redirect('/voting/allVotings')
        else:
            form = NewVotingForm()

    return render(request, 'form.html', {
        'form': form,
        'title': 'Nueva Votación',
    })

def all_votings(request):
    if not request.user.is_staff:
        template = loader.get_template('403.html')
        return HttpResponseForbidden(template.render({}, request))
    else:
        votings = Voting.objects.all()
        return render(request, 'allVotings.html', {'votings': votings, 'title': 'Votaciones',})
    
def votings_detail(request, voting_id):
    if not request.user.is_staff:
        template = loader.get_template('403.html')
        return HttpResponseForbidden(template.render({}, request))
    else:
        voting = Voting.objects.get(pk=voting_id)
        return render(request, 'votings_detail.html', {'voting': [voting], 'title': 'Votacion',})

    