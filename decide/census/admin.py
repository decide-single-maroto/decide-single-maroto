from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from django.http import HttpResponse
from django.contrib.admin import SimpleListFilter
import csv
from .models import Census
from .resources import CensusResource

# Custom admin filter to allow filtering Census records by Voting ID
class VotingIdFilter(SimpleListFilter):
    title = 'Voting ID'
    parameter_name = 'voting_id'

    def lookups(self, request, model_admin):
        voting_ids = Census.objects.values_list('voting_id', flat=True).distinct()
        return [(voting_id, str(voting_id)) for voting_id in voting_ids]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(voting_id=value)
        return queryset


class CensusAdmin(ImportExportModelAdmin):
    resource_class = CensusResource
    list_display = ('voting_id', 'voter_id')
    list_filter = (VotingIdFilter, )
    search_fields = ('voter_id', )
    actions = ["export_selected"]

    @classmethod
    def export_selected(cls, modeladmin, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="census_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['voting_id', 'voter_id'])

        for census in queryset:
            voting_id = census.voting_id if census.voting_id is not None else ''
            voter_id = census.voter_id if census.voter_id is not None else ''
            writer.writerow([voting_id, voter_id])

        return response

    export_selected.short_description = "Export census"



admin.site.register(Census, CensusAdmin)

