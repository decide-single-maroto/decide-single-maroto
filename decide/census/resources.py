from import_export import resources
from .models import Census

class CensusResource(resources.ModelResource):
    class Meta:
        model = Census
        exclude = ('id',)
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('voting_id', 'voter_id',)