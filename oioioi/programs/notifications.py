from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_noop

from oioioi.base.notification import NotificationHandler


def notification_function_initial_results(arguments):
    assert hasattr(arguments, 'user') and hasattr(arguments, 'submission')
    pi = arguments.submission.problem_instance
    request = RequestFactory().get('/', data={'name': u'test'})
    request.user = arguments.user
    request.contest = pi.contest
    request.timestamp = timezone.now()

    # Check if any initial result is visible for user
    if not pi.controller.can_see_submission_status(request, arguments.submission):
        return

    if pi.contest:
        url = reverse(
            'submission',
            kwargs={
                'contest_id': pi.contest.pk,
                'submission_id': arguments.submission.pk,
            },
        )
    elif pi.problem.problemsite:
        url = (
            reverse('problem_site', kwargs={'site_key': pi.problem.problemsite.url_key})
            + '?key=submissions'
        )
    else:
        url = ''

    message = gettext_noop("Initial result for task %(short_name)s is ready")
    message_arguments = {'short_name': pi.short_name, 'address': url, 'submission_id': arguments.submission.pk}

    NotificationHandler.send_notification(
        arguments.user, 'initial_results', message, message_arguments
    )


NotificationHandler.register_notification(
    'initial_results', notification_function_initial_results
)


def notification_function_submission_judged(arguments):
    assert hasattr(arguments, 'user') and hasattr(arguments, 'submission')
    pi = arguments.submission.problem_instance
    pic = pi.controller
    request = RequestFactory().get('/', data={'name': u'test'})
    request.user = arguments.user
    request.contest = pi.contest
    request.timestamp = timezone.now()

    can_see_score = pic.can_see_submission_score(request, arguments.submission)
    can_reveal = (
        'oioioi.scoresreveal' in settings.INSTALLED_APPS
        and pi.contest # otherwise there can't be reveals
        and hasattr(pic, 'can_reveal')
        and pic.can_reveal(request, arguments.submission)[0]
    )
    # Check if the user will see any change in the submission
    # FIXME: We should have a method in the controllers for this
    if not can_see_score and not can_reveal:
        return

    if pi.contest:
        url = reverse(
            'submission',
            kwargs={
                'contest_id': pi.contest.pk,
                'submission_id': arguments.submission.pk,
            },
        )
    elif pi.problem.problemsite:
        url = (
            reverse('problem_site', kwargs={'site_key': pi.problem.problemsite.url_key})
            + '?key=submissions'
        )
    else:
        url = ''

    message = pi.controller.get_notification_message_submission_judged(
        arguments.submission
    )

    message_arguments = {
        'short_name': pi.short_name,
        'task_name': str(pi),
        'address': url,
        'submission_id': arguments.submission.pk,
    }
    # For reveals-only we can't send this
    if can_see_score:
        message_arguments['score'] = str(arguments.submission.score)
    else:
        message_arguments['score'] = gettext_noop("unknown")
    if pi.contest:
        message_arguments['contest_name'] = pi.contest.name
        
    NotificationHandler.send_notification(
        arguments.user, 'submission_judged', message, message_arguments
    )


NotificationHandler.register_notification(
    'submission_judged', notification_function_submission_judged
)
