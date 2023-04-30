# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import override_settings
from django_assets_manager.templatetags.assets_manager import assets


class TestDependencies(TestCase):
	def ctx(self):
		return {}

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': 'static://js/app.js',
				'css': 'static://js/app.css',
			},
		}
	)
	def test_single_asset(self):
		print(assets(self.ctx(), 'app'))
