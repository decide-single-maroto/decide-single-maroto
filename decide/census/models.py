from django.db import models


class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

    # String representation for easy identification in admin views
    def __str__(self):
        return f"Census - Voting ID: {self.voting_id}, Voter ID: {self.voter_id}"
