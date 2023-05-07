# -*- coding: utf-8 -*-
import os
import shutil
from datetime import datetime
from pathlib import Path

import httpretty
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.template.loader import get_template
from django.test import TestCase, override_settings
from jinja2.runtime import Context

from django_assets_manager.checks import check_generated
from django_assets_manager.templatetags.assets_manager import assets, assets_by_type


def get_static_path(path: str) -> Path:
	static_dir = Path(settings.STATICFILES_DIRS[0])
	return Path.joinpath(static_dir, path)


def clear_cached_static_files():
	generated_dir = get_static_path('CACHE')
	if generated_dir.exists():
		shutil.rmtree(generated_dir)


class TemplateContextMixin(object):
	def ctx(self):
		return {}

	def jinja_ctx(self):
		tpl = get_template('index.html', using='jinja')
		environment = tpl.backend.env
		return Context(environment, parent={}, name='index.html', blocks={})


class TestAssets(TemplateContextMixin, TestCase):
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


class TestChecks(TestCase):
	def setUp(self):
		clear_cached_static_files()

	@classmethod
	def tearDownClass(cls):
		clear_cached_static_files()

	@override_settings(
		ASSETS_MANAGER_SPRITES = [
			{
				'name': 'main',
				'output': 'CACHE/sprites.png',
				'scss_output': 'CACHE/sprites.scss',
				'extra_sizes': ((2, '@2x'),),
				'width': 640,
				'height': 640,
				'images': (
					{
						'name': 'img',
						'src': 'img.png',
					},
				),
			},
		],
	)
	def test_recompilation_needed(self):
		# not generated
		errors = check_generated()
		self.assertEqual(1, len(errors))

		# now call generate sprites
		call_command('compilesprites')
		errors = check_generated()
		self.assertEqual(0, len(errors))

		# now pretend, that generated file is order
		older_time = int(datetime.now().timestamp()) - 100000
		generated_file = get_static_path('CACHE/sprites.png')
		os.utime(generated_file, (older_time, older_time))

		# check again
		errors = check_generated()
		self.assertEqual(1, len(errors))


class TestCdnFinder(TemplateContextMixin, TestCase):
	def setUp(self):
		clear_cached_static_files()

	@classmethod
	def tearDownClass(cls):
		clear_cached_static_files()

	@override_settings(
		ASSETS_MANAGER_FILES = {
			'app': {
				'js': '//external.com/script.js',
			},
		},
	)
	def test_get_external_files(self):
		self.assertEqual('<script src="//external.com/script.js"></script>', assets(self.ctx(), 'app'))

	@httpretty.activate
	def test_cached_external_file(self):
		httpretty.register_uri(httpretty.GET, "http://external.com/script.js", body="")
		httpretty.register_uri(httpretty.GET, "http://external.com/script2.js", body="")
		with override_settings(
			ASSETS_MANAGER_FILES = {
				'app': {
					'js': 'http://external.com/script.js',
					'cache': {
						'paths': {
							'http://external.com/script.js': 'script.js',
						}
					},
				},
			},
		):
			self.assertEqual('<script src="/static/CACHE/app/script.js"></script>', assets(self.ctx(), 'app'))
		# same request without http prefix
		with override_settings(
			ASSETS_MANAGER_FILES = {
				'app': {
					'js': ['http://external.com/script.js', '//external.com/script2.js'],
					'cache': {
						'paths': {
							'http://external.com/script.js': 'script.js',
							'//external.com/script2.js': 'script2.js',
						}
					},
				},
			},
		):
			self.assertEqual('<script src="/static/CACHE/app/script.js"></script><script src="/static/CACHE/app/script2.js"></script>', assets(self.ctx(), 'app'))
