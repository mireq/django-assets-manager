# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).parent

INSTALLED_APPS = ['tests', 'django_assets_manager']
SECRET_KEY = 'secret'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'tests.urls'
USE_TZ = False
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_URL = '/static/'

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.sqlite3',
		'NAME': ':memory:',
	}
}

STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	'django_assets_manager.finders.CdnFinder',
)
TEMPLATES = [
	{
		'BACKEND': 'django_jinja.backend.Jinja2',
		'NAME': 'jinja',
		'DIRS': [BASE_DIR / 'templates' / 'jinja'],
		'APP_DIRS': False,
		'OPTIONS': {
			"match_extension": None,
		}
	},
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'NAME': 'django',
		'DIRS': [BASE_DIR / 'templates' / 'django'],
		'APP_DIRS': False,
		'OPTIONS': {
			'context_processors': ['django.template.context_processors.request'],
			'builtins': ['django_assets_manager.templatetags.assets_manager'],
		},
	},
]
