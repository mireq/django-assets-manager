# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.core import checks

from .checks import check_generated


class AssetsManagerConfig(AppConfig):
	name = 'django_assets_manager'
	verbose_name = "Assets manager"

	def ready(self):
		checks.register()(check_generated)

