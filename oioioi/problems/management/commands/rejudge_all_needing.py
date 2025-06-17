from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from oioioi.contests.models import ProblemInstance


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):
        for p in ProblemInstance.objects.filter(needs_rejudge=True):
            for s in p.submission_set.all():
                    p.controller.judge(s, {}, is_rejudge=True)
            p.needs_rejudge=False
            p.save()
