# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.core import checks

from .checks import check_generated


class AssetsManagerConfig(AppConfig):
	name = 'django_assets_manager'
	verbose_name = "Assets manager"

	def ready(self):
		checks.register()(check_generated)

