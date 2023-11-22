from django.conf import settings

from oioioi.base.utils.execute import execute


def print_filename(filename):
    if settings.TESTS:
        print("Printing " + filename)
    else:
        execute(['lp', '-o', 'media=a4', filename])
