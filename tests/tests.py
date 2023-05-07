# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import get_template
from django.test import TestCase, override_settings
from jinja2.runtime import Context

from django_assets_manager.templatetags.assets_manager import assets, assets_by_type


class TestDependencies(TestCase):
	def ctx(self):
		return {}

	def jinja_ctx(self):
		tpl = get_template('index.html', using='jinja')
		environment = tpl.backend.env
		return Context(environment, parent={}, name='index.html', blocks={})

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': 'static://js/app.js',
				'css': 'static://js/app.css',
			},
		},
		X='x'
	)
	def test_single_asset(self):
		self.assertEqual('<link rel="stylesheet" href="/static/js/app.css" /><script src="/static/js/app.js"></script>', assets(self.ctx(), 'app'))

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': 'static://js/app.js',
				'css': 'static://js/app.css',
			},
		},
	)
	def test_dont_repeat(self):
		ctx = self.ctx()
		assets(ctx, 'app')
		self.assertEqual('', assets(ctx, 'app'))

		ctx = self.jinja_ctx()
		assets(ctx, 'app')
		self.assertEqual('', assets(ctx, 'app'))

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': 'http://example.tld/app.js',
				'css': 'http://example.tld/app.css',
			},
		},
	)
	def test_external(self):
		self.assertEqual('<link rel="stylesheet" href="http://example.tld/app.css" /><script src="http://example.tld/app.js"></script>', assets(self.ctx(), 'app'))

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': ['static://1.js', 'static://2.js'],
				'css': ['static://1.css', 'static://2.css'],
			},
		},
	)
	def test_array(self):
		self.assertEqual('<link rel="stylesheet" href="/static/1.css" /><link rel="stylesheet" href="/static/2.css" /><script src="/static/1.js"></script><script src="/static/2.js"></script>', assets(self.ctx(), 'app'))

	@override_settings(
		ASSETS_MANAGER_FILES = {
		},
	)
	def test_throw_error(self):
		with self.assertRaises(ImproperlyConfigured):
			assets(self.ctx(), 'app')

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'dep': {
				'js': ['static://1.js'],
			},
			'app': {
				'js': ['static://2.js'],
				'depends': ['dep'],
			},
		},
	)
	def test_dependencies(self):
		self.assertEqual('<script src="/static/1.js"></script><script src="/static/2.js"></script>', assets(self.ctx(), 'app'))

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'custom': ['custom.script'],
			},
		},
	)
	def test_custom_type(self):
		self.assertEqual('Custom: custom.script', assets_by_type(self.ctx(), 'custom', 'app').strip())
