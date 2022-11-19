from __future__ import print_function

import six

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from oioioi.contests.models import Contest, ProblemInstance, UserResultForProblem

class Command(BaseCommand):
    help = _("Recalculate all results in a contest with given id")
    
    def add_arguments(self, parser):
        parser.add_argument('id', type=str, help='Contest id')
        parser.add_argument('-q', action='store_true', default=False, dest='quiet', help="Don't print result changes")

    def handle(self, *args, **options):
        quiet = options['quiet']
        
        contest = Contest.objects.get(id=options['id'])
        for prob_inst in ProblemInstance.objects.filter(contest=contest):
            print("--- Updating ", prob_inst.problem)
            for result in UserResultForProblem.objects.filter(problem_instance=prob_inst):
                old_score=result.score
                contest.controller.update_user_result_for_problem(result)
                result.save()
                if !quiet:
                    print(old_score, "-->", result.score)
