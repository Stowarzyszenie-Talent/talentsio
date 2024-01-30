from django.conf import settings

from oioioi.base.utils.execute import execute


def print_filename(filename):
    if getattr(settings, 'TESTS', False):
        print("Printing " + filename)
    else:
        execute(['lp', '-o', 'media=a4', filename])
