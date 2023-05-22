# -*- coding: utf-8 -*-

from __future__ import print_function

try:
    from setuptools import find_packages, setup
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup, find_packages

import os
import sys

if os.getuid() == 0:  # root
    print("ERROR: This setup.py cannot be run as root.", file=sys.stderr)
    print("ERROR: If you want to proceed anyway, hunt this", file=sys.stderr)
    print("ERROR: message and edit the source at your own risk.", file=sys.stderr)
    sys.exit(2)

requirements = [
    "Django>=3.2,<3.3",  # when upgrading, upgrade also django-two-factor-auth!
    "pytz",
    "sqlalchemy<1.5",
    "beautifulsoup4",
    "PyYAML<5.5",
    "python-dateutil<2.9",
    "django-two-factor-auth==1.13.2",
    "django-formtools>=2.2,<=2.3",
    "django-registration-redux>=2.6,<=2.9",
    "Celery==4.4.7",
    "coreapi>=2.3.0,<2.4",
    "dj-pagination==2.5",
    "django-compressor==2.4.1",  # latest version
    "django-statici18n<2.4",
    "pygments",
    "django-libsass>=0.7,<=0.8",
    "django-debug-toolbar>=3.0,<=3.3",
    "django-extensions>=3.0,<=3.2",  # Django 2.2
    "djangorestframework",
    'pytest==4.6.11',
    'pytest-metadata==1.11.0',
    'pytest-django==3.10.0',
    'pytest-html==1.22.1',
    'pytest-xdist==1.34.0',
    'pytest-cov>=2.11,<2.12',
    'requests<3',
    "fpdf<1.8",
    "unicodecsv<0.15",
    "shortuuid",
    "dnslib<0.10",
    "bleach",
    "chardet",
    "django-gravatar2<1.5",
    "django-mptt",
    "mistune==0.8.4",
    "pika",
    "raven<6.11",
    "unidecode",
    "sentry-sdk",
    "fontawesomefree",
    # A library allowing to nest inlines in django admin.
    # Used in quizzes module for adding new quizzes.
    "django-nested-admin",
    # SIO2 dependencies:
    "filetracker>=2.1.5,<3.0",
    "django-simple-captcha",
    # HOTFIX
    "phonenumbers<8.13",
    "pdfminer.six",
    # https://stackoverflow.com/questions/73929564/entrypoints-object-has-no-attribute-get-digital-ocean
    "importlib-metadata<5.0",
]

setup(
    name='oioioi',
    version='0.2.0.dev',
    description='The web frontend of the SIO2 Project contesting system',
    author='The SIO2 Team',
    author_email='sio2@sio2project.mimuw.edu.pl',
    url='http://sio2project.mimuw.edu.pl',
    install_requires=requirements,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='oioioi.runtests.runtests',
    entry_points={
        'console_scripts': [
            'oioioi-create-config = oioioi.deployment.create_config:main',
        ],
    },
)
