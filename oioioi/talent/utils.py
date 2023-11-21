from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.db import transaction

from oioioi.participants.models import Participant
from oioioi.supervision.models import Membership, Group
from oioioi.talent.models import TalentRegistration


def get_group(cid):
    return Group.objects.filter(
        name=settings.TALENT_CONTEST_NAMES[cid],
    ).first()


def set_talent_participant(user, cid, room=None):
    with transaction.atomic():
        if cid not in settings.TALENT_CONTEST_NAMES:
            raise SuspiciousOperation

        # Cleanup from the previous contest group
        old_tr = TalentRegistration.objects.filter(
            user=user,
        ).first()
        if old_tr:
            old_cid = old_tr.contest_id
            # Remove from supervision group
            Membership.objects.filter(
                user=user,
                group=get_group(old_cid),
            ).delete()
            # Intentionally don't remove old Participant object,
            # as we want to leave them in the ranking (?) etc.
            # Also, the user should remain able to see that contest.

        update_dict = {'contest_id': cid}
        if not (room is None):
            update_dict['room'] = room
        TalentRegistration.objects.update_or_create(
            user=user,
            defaults=update_dict,
        )
        # Add to supervision group
        if cid in settings.TALENT_SUPERVISED_IDS:
            Membership.objects.get_or_create(
                user=user,
                group=get_group(cid),
            )
        # Add to potentially (really) closed contest
        Participant.objects.get_or_create(
            contest_id=cid,
            user=user,
        )
        # Add to semi-open contests
        for g in settings.TALENT_CONTEST_IDS:
            if g not in settings.TALENT_CLOSED_CONTEST_IDS:
                Participant.objects.get_or_create(
                    contest_id=g,
                    user=user,
                )
