# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).parent

INSTALLED_APPS = ['tests', 'django_assets_manager']
SECRET_KEY = 'secret'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'tests.urls'
USE_TZ = False
STATICFILES_DIRS = [BASE_DIR / 'static']

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': ':memory:',
	}
}

TEMPLATES = [
	{
		"BACKEND": "django_jinja.backend.Jinja2",
		'DIRS': [BASE_DIR / 'templates' / 'jinja'],
		"APP_DIRS": True,
		"OPTIONS": {}
	},
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [BASE_DIR / 'templates' / 'django'],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': ['django.template.context_processors.request'],
			'builtins': ['django_universal_paginator.templatetags.paginator_tags'],
		},
	},
]
