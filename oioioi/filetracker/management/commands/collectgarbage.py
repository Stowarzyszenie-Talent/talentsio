from __future__ import print_function

from concurrent.futures import ProcessPoolExecutor
import datetime
import itertools

from django.conf import settings
from django.core.management.base import BaseCommand
from django.apps import apps
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from filetracker.client import Client
from filetracker.utils import split_name


client = Client(remote_url=settings.FILETRACKER_URL, local_store=None)

def set_client():
    global client
    client = Client(remote_url=settings.FILETRACKER_URL, local_store=None)

def delete_file(args):
    global client
    if args[2] > 1:
        print(" " + args[0])
    client.delete_file('/' + args[0] + '@' + args[1])

class Command(BaseCommand):
    help = _("Delete all orphaned files older than specified number of days.")

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            action='store',
            type=int,
            dest='days',
            default=30,
            help=_(
                "Orphaned files older than DAYS days will "
                "be deleted. Default value is 30."
            ),
            metavar=_("DAYS"),
        )
        parser.add_argument(
            '-n',
            '--paralell',
            action='store',
            type=int,
            dest='workers',
            default=0,
            help=_("How many files to delete in paralell."),
        )
        parser.add_argument(
            '-p',
            '--pretend',
            action='store_true',
            dest='pretend',
            default=False,
            help=_(
                "If set, the orphaned files will only be displayed, not deleted."
            ),
        )

    def _get_needed_files(self):
        result = []
        for app in apps.get_app_configs():
            model_list = app.get_models()
            for model in model_list:
                file_fields = [
                    field.name
                    for field in model._meta.fields
                    if field.get_internal_type() == 'FileField'
                ]

                if len(file_fields) > 0:
                    files = model.objects.all().values_list(*file_fields)
                    result.extend(
                        [
                            split_name(file)[0]
                            for file in itertools.chain.from_iterable(files)
                            if file
                        ]
                    )
        return result

    def handle(self, *args, **options):
        assert options['workers'] >= 0
        print("Getting needed files...")
        needed_files = self._get_needed_files()
        print("Got needed files.")
        print("Getting list of files on filetracker...")
        all_files = client.list_remote_files()
        print("Got list of files on filetracker.")
        all_files = [f for f in all_files if not f[0].startswith("sandboxes")]
        max_date_to_delete = int((datetime.datetime.now() - datetime.timedelta(
            days=options['days']
        )).timestamp())
        diff = set([f[0] for f in all_files]) - set(needed_files)
        to_delete = [
            f[0]
            for f in all_files
            if f[0] in diff
            and f[1] < max_date_to_delete # f[1] is a timestamp
        ]

        files_count = len(to_delete)
        if files_count == 0 and int(options['verbosity']) > 0:
            print(_("No files to delete."))
        elif options['pretend']:
            if int(options['verbosity']) > 1:
                print(
                    ngettext(
                        "The following %d file is scheduled for deletion:",
                        "The following %d files are scheduled for deletion:",
                        files_count,
                    )
                    % files_count
                )
                for file in to_delete:
                    print(" ", file)
            elif int(options['verbosity']) == 1:
                print(
                    ngettext(
                        "%d file scheduled for deletion.",
                        "%d files scheduled for deletion.",
                        files_count,
                    )
                    % files_count
                )
        else:
            if int(options['verbosity']) > 1:
                print(
                    ngettext(
                        "Deleting the following %d file:",
                        "Deleting the following %d files:",
                        files_count,
                    )
                    % files_count
                )
            if int(options['verbosity']) == 1:
                print(
                    ngettext("Deleting %d file", "Deleting %d files", files_count)
                    % files_count
                )
            timestamp = str(max_date_to_delete)
            if options['workers'] == 0:
                for file in to_delete:
                    delete_file((file, timestamp, options['verbosity']))
            else:
                print(f"Starting {str(options['workers'])} paralell workers.")
                with ProcessPoolExecutor(max_workers=options['workers'], initializer=set_client) as pool:
                    len([*pool.map(delete_file, [
                        (file, timestamp, options['verbosity']) for file in to_delete
                    ])])
                print("Done.")
