from __future__ import print_function

from collections import defaultdict
from operator import itemgetter  # pylint: disable=E0611

import unicodecsv
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from oioioi.base.models import PreferencesSaved
from oioioi.base.utils import ObjectWithMixins, RegisteredSubclassesBase
from oioioi.contests.controllers import ContestController, ContestControllerContext
from oioioi.contests.models import Contest, ProblemInstance, UserResultForProblem
from oioioi.contests.utils import is_contest_basicadmin, is_contest_observer
from oioioi.filetracker.utils import make_content_disposition_header
from oioioi.rankings.models import Ranking, RankingPage

CONTEST_RANKING_KEY = 'c'


class RankingMixinForContestController(object):
    """ContestController mixin that sets up rankings app."""

    def ranking_controller(self):
        """Return the actual :class:`RankingController` for the contest."""
        return DefaultRankingController(self.contest)

    def update_user_results(self, user, problem_instance, *args, **kwargs):
        super(RankingMixinForContestController, self).update_user_results(
            user, problem_instance, *args, **kwargs
        )
        self.ranking_controller().invalidate_pi(
            problem_instance
        )


ContestController.mix_in(RankingMixinForContestController)


class RankingController(RegisteredSubclassesBase, ObjectWithMixins):
    """Ranking system uses two types of keys: "partial key"s and "full key"s.
    Please note that full keys are abbreviated in the code as "key"s.

    A pair (request, partial_key) should allow to build a full key, while a
    partial_key can always be extracted from the full key.
    partial keys identify the rounds to display and are used everywhere
    outside controllers and rankingsd (e.g. in views and urls). However, the
    actual ranking contents can depend on many other factors, like user
    permissions. This was the reason for introduction of full keys, which
    are always sufficient to choose the right data for serialization and
    display.
    """

    modules_with_subclasses = ['controllers']
    abstract = True
    PERMISSION_LEVELS = ['admin', 'observer', 'regular',]
    PERMISSION_CHECKERS = [
        lambda request: 'admin' if is_contest_basicadmin(request) else None,
        lambda request: 'observer' if is_contest_observer(request) else None,
        lambda request: 'regular',
    ]

    def get_partial_key(self, key):
        """Extracts partial key from a full key."""
        return key.split('#')[1]

    def replace_partial_key(self, key, new_partial):
        """Replaces partial key in a full key"""
        return key.split('#')[0] + '#' + new_partial

    def get_full_key(self, request, partial_key):
        """Returns a full key associated with request and partial_key"""
        for checker in self.PERMISSION_CHECKERS:
            res = checker(request)
            if res is not None:
                return res + '#' + partial_key

    def construct_full_key(self, perm_level, partial_key):
        return perm_level + '#' + partial_key

    def get_all_partial_keys(self, contest):
        """Returns a list of possible partial keys for a contest."""
        raise NotImplementedError

    def validate_ranking(self, r):
        """Returns True if r's key is valid, otherwise False"""
        raise NotImplementedError

    def construct_all_full_keys(self, partial_keys):
        fulls = []
        for perm in self.PERMISSION_LEVELS:
            for partial in partial_keys:
                fulls.append(self.construct_full_key(perm, partial))
        return fulls

    def _key_permission(self, key):
        """Returns a permission level associated with given full key"""
        return key.split('#')[0]

    def is_admin_key(self, key):
        """Returns true if a given full key corresponds to users with
        administrative permissions.
        """
        return self._key_permission(key) == 'admin'

    def __init__(self, contest):
        self.contest = contest

    def available_rankings(self, request):
        """Returns a list of available rankings.

        Each ranking is a pair ``(key, description)``.
        """
        raise NotImplementedError

    def can_search_for_users(self):
        """Determines if in this ranking, searching for users is enabled."""
        return False

    def find_user_position(self, request, partial_key, user):
        """Returns user's position in the ranking.
        User should be an object of class User, not a string with username.

        If user is not in the ranking, None is returned.
        """
        raise NotImplementedError

    def get_rendered_ranking(self, request, partial_key):
        """Retrieves ranking generated by rankingsd.

        You should never override this function. It will be responsible for
        communication with rankingsd and use render_ranking for actual
        HTML generation. Feel free to override render_ranking to customize
        its logic.

        If the ranking is still being generated, or the user requested an
        invalid page, displays an appropriate message.
        """
        try:
            page_nr = int(request.GET.get('page', 1))
        except ValueError:
            return HttpResponseBadRequest("Page number must be integer")
        key = self.get_full_key(request, partial_key)
        # Let's pretend the ranking is always up-to-date during tests.
        if getattr(settings, 'MOCK_RANKINGSD', False):
            data = self.serialize_ranking(key)
            html = self._render_ranking_page(key, data, page_nr)
            print(data)
            return mark_safe(html)

        ranking = Ranking.objects.get_or_create(contest=self.contest, key=key)[0]
        try:
            page = ranking.pages.get(nr=page_nr)
        except RankingPage.DoesNotExist:
            # The ranking hasn't been yet generated
            if page_nr == 1:
                return mark_safe(render_to_string("rankings/generating_ranking.html"))
            return mark_safe(render_to_string("rankings/no_page.html"))

        context = {
            'ranking_html': mark_safe(page.data),
            'is_up_to_date': ranking.is_up_to_date(),
        }
        return mark_safe(render_to_string("rankings/rendered_ranking.html", context))

    def get_serialized_ranking(self, key):
        return self.serialize_ranking(key)

    def build_ranking(self, key):
        """Serializes data and renders html for given key.

        Results are processed using serialize_ranking, and then as many
        pages as needed are rendered. Returns a tuple containing serialized
        data and a list of strings, that are html code of ranking pages.
        """
        data = self.serialize_ranking(key)
        pages = []
        num_participants = len(data['rows'])
        on_page = data['participants_on_page']
        num_pages = (num_participants + on_page - 1) // on_page
        num_pages = max(num_pages, 1)  # Render at least a single page
        for i in range(1, num_pages + 1):
            pages.append(self._render_ranking_page(key, data, i))
        return data, pages

    def _fake_request(self, page):
        """Creates a fake request used to render ranking.

        Pagination engine requires access to request object, so it can
        extract page number from GET parameters.
        """
        fake_req = RequestFactory().get('/?page=' + str(page))
        fake_req.user = AnonymousUser()
        fake_req.contest = self.contest
        # This is required by dj-pagination
        # Normally they monkey patch this function in their middleware
        fake_req.page = lambda _: page
        return fake_req

    def _render_ranking_page(self, key, data, page):
        raise NotImplementedError

    def render_ranking_to_csv(self, request, partial_key):
        raise NotImplementedError

    def serialize_ranking(self, key):
        """Returns some data (representing ranking).
        This data will be used by :meth:`render_ranking`
        to generate the html code.
        """
        raise NotImplementedError


class DefaultRankingController(RankingController):
    description = _("Default ranking")

    def _iter_rounds(self, can_see_all, timestamp, partial_key, request=None):
        ccontroller = self.contest.controller
        queryset = self.contest.round_set.all()
        if partial_key != CONTEST_RANKING_KEY:
            queryset = queryset.filter(id=partial_key)
        # A not-None request enables caching of round times
        request = request or self._fake_request(1)
        for round in queryset:
            times = ccontroller.get_round_times(request, round)
            if can_see_all or times.public_results_visible(timestamp):
                yield round

    def _rounds_for_ranking(self, request, partial_key=CONTEST_RANKING_KEY):
        can_see_all = is_contest_basicadmin(request) or is_contest_observer(request)
        return self._iter_rounds(can_see_all, request.timestamp, partial_key, request)

    def _rounds_for_key(self, key):
        can_see_all = self._key_permission(key) in {'admin', 'observer'}
        partial_key = self.get_partial_key(key)
        return self._iter_rounds(can_see_all, timezone.now(), partial_key)

    def get_all_partial_keys(self, contest):
        # _iter_rounds should be changed to iter_rounds and standardised.
        # acm's rankingcontroller uses a slightly different version, but it
        # still works here.
        return [CONTEST_RANKING_KEY,] + [
            str(r.id) for r in self._iter_rounds(True, 0, CONTEST_RANKING_KEY)
        ]

    def validate_ranking(self, r):
        return r.key in self.construct_all_full_keys(
            self.get_all_partial_keys(r.contest)
        )

    def available_rankings(self, request):
        rankings = [(CONTEST_RANKING_KEY, _("Contest"))]
        for round in self._rounds_for_ranking(request):
            rankings.append((str(round.id), round.name))
        if len(rankings) == 1:
            # No rounds have visible results
            return []
        if len(rankings) == 2:
            # Only a single round => call this "contest ranking".
            return rankings[:1]
        return rankings

    def keys_for_pi(self, pi):
        partial_keys = [CONTEST_RANKING_KEY, str(pi.round_id)]
        return self.construct_all_full_keys(partial_keys)

    def invalidate_pi(self, pi):
        Ranking.invalidate_queryset(Ranking.objects.filter(
            contest_id=pi.round.contest_id,
            key__in=self.keys_for_pi(pi),
        ))

    def can_search_for_users(self):
        return True

    def find_user_position(self, request, partial_key, user):
        key = self.get_full_key(request, partial_key)
        if getattr(settings, 'MOCK_RANKINGSD', False):
            rows = self.serialize_ranking(key)['rows']
        else:
            try:
                ranking = Ranking.objects.get(contest=self.contest, key=key)
            except Ranking.DoesNotExist:
                return None
            serialized = ranking.serialized or {}
            rows = serialized.get('rows')
            if not rows:  # Ranking isn't ready yet
                return None

        for i, row in enumerate(rows):
            if row['user'] == user:
                return i + 1
        # User not found
        return None

    def _render_ranking_page(self, key, data, page):
        request = self._fake_request(page)
        data['is_admin'] = self.is_admin_key(key)
        return render_to_string(
            'rankings/default_ranking.html', context=data, request=request
        )

    def _get_csv_header(self, key, data):
        header = [_("No."), _("Login"), _("First name"), _("Last name")]
        for pi, _statement_visible in data['problem_instances']:
            header.append(pi.get_short_name_display())
        header.append(_("Sum"))
        return header

    def _get_csv_row(self, key, row):
        line = [
            row['place'],
            row['user'].username,
            row['user'].first_name,
            row['user'].last_name,
        ]
        line += [r.score if r and r.score is not None else '' for r in row['results']]
        line.append(row['sum'])
        return line

    def render_ranking_to_csv(self, request, partial_key):
        key = self.get_full_key(request, partial_key)
        data = self.serialize_ranking(key)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = make_content_disposition_header(
            'attachment', u'%s-%s-%s.csv' % (_("ranking"), self.contest.id, key)
        )
        writer = unicodecsv.writer(response)

        writer.writerow(list(map(force_str, self._get_csv_header(key, data))))
        for row in data['rows']:
            writer.writerow(list(map(force_str, self._get_csv_row(key, row))))

        return response

    def filter_users_for_ranking(self, key, queryset):
        return queryset.filter(is_superuser=False)

    def _filter_pis_for_ranking(self, partial_key, queryset):
        return queryset

    def _allow_zero_score(self):
        return True

    def _get_users_results(self, pis, results, rounds, users):
        by_user = defaultdict(dict)
        for r in results:
            by_user[r.user_id][r.problem_instance_id] = r
        users = users.filter(id__in=list(by_user.keys()))
        data = []
        all_rounds_trial = all(r.is_trial for r in rounds)
        for user in users.order_by('last_name', 'first_name', 'username'):
            by_user_row = by_user[user.id]
            user_results = []
            user_data = {'user': user, 'results': user_results, 'sum': None}

            for pi in pis:
                result = by_user_row.get(pi.id)
                if (
                    result
                    and hasattr(result, 'submission_report')
                    and hasattr(result.submission_report, 'submission_id')
                ):
                    submission_id = result.submission_report.submission_id
                    kwargs = {
                        'contest_id': self.contest.id,
                        'submission_id': submission_id,
                    }
                    result.url = reverse('submission', kwargs=kwargs)

                user_results.append(result)
                if (
                    result
                    and result.score
                    and (not pi.round.is_trial or all_rounds_trial)
                ):
                    if user_data['sum'] is None:
                        user_data['sum'] = result.score
                    else:
                        user_data['sum'] += result.score
            if user_data['sum'] is not None:
                # This rare corner case with sum being None may happen if all
                # user's submissions do not have scores (for example the
                # problems do not support scoring, or all the evaluations
                # failed with System Errors).
                if self._allow_zero_score() or user_data['sum'].to_int() != 0:
                    data.append(user_data)
        return data

    def _assign_places(self, data, extractor):
        """Assigns places to the serialized ranking ``data``.

        Extractor should return values by which users should be ordered in
        the ranking. Users with the same place should have same value
        returned.
        """
        data.sort(key=extractor, reverse=True)
        prev_sum = None
        place = None
        for i, row in enumerate(data, 1):
            if extractor(row) != prev_sum:
                place = i
                prev_sum = extractor(row)
            row['place'] = place

    def _is_problem_statement_visible(self, key, pi, timestamp):
        if self.is_admin_key(key):
            return True
        ccontroller = self.contest.controller
        context = ContestControllerContext(self.contest, timezone.now(), False)
        return ccontroller.can_see_problem(
            context, pi
        ) and ccontroller.can_see_statement(context, pi)

    def _get_pis_with_visibility(self, key, pis):
        now = timezone.now()
        return [(pi, self._is_problem_statement_visible(key, pi, now)) for pi in pis]

    def _get_results_qs_for_serialization(self, key):
        return UserResultForProblem.objects.all().prefetch_related(
            'problem_instance__round',
        ).select_related(
            'submission_report',
            'problem_instance',
            'problem_instance__contest',
        )

    def serialize_ranking(self, key):
        partial_key = self.get_partial_key(key)
        rounds = list(self._rounds_for_key(key))
        pis = list(
            self._filter_pis_for_ranking(
                partial_key, ProblemInstance.objects.filter(round__in=rounds)
            )
            .select_related('problem')
            .prefetch_related('round')
        )
        users = self.filter_users_for_ranking(key, User.objects.all()).distinct()
        results = self._get_results_qs_for_serialization(key).filter(
            problem_instance__in=pis, user__in=users
        )

        data = self._get_users_results(pis, results, rounds, users)
        self._assign_places(data, itemgetter('sum'))
        return {
            'rows': data,
            'problem_instances': self._get_pis_with_visibility(key, pis),
            'participants_on_page': getattr(settings, 'PARTICIPANTS_ON_PAGE', 100),
        }


def update_rankings_with_user_callback(sender, user, **kwargs):
    contests = Contest.objects.filter(probleminstance__submission__user=user)
    for contest in contests:
        Ranking.invalidate_contest(contest)


PreferencesSaved.connect(update_rankings_with_user_callback)
