import json
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404

from base import mods
from census.models import Census
from store.models import Vote


class VisualizerView(TemplateView):
    template_name = 'visualizer/visualizer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting_id = kwargs.get('voting_id', 0)

        try:
            voting = mods.get('voting', params={'id': voting_id})
            context['voting'] = json.dumps(voting[0])
            num_census = 0
            num_votos = 0
            participation = "-"

            if voting[0].get('start_date'):
                num_census = Census.objects.filter(voting_id=voting_id).count()
                num_votos = Vote.objects.filter(voting_id=voting_id).count()

                if num_census != 0:
                    participation = str(round((num_votos*100)/num_census, 2)) + '%'
            
            realTimeData = {'num_census': num_census, 'num_votos': num_votos, 'participation': participation}
            context['realTimeData'] = realTimeData

        except:
            raise Http404

        return context
