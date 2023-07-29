from datetime import timedelta

from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response

from oioioi.contests.models import Submission

@api_view()
def recent_submissions_number(request):
    """ Return number of submissions in the last minute """
    interval_start = request.timestamp - timedelta(minutes=1)
    num = Submission.objects.filter(
        date__gt=interval_start,
        date__lte=request.timestamp,
    ).count()
    return Response(num)
