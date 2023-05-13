=======================================
Simple assets manager with dependencies
=======================================

Install
-------

`pip install django-assets-manager`

Usage
-----

Settings
^^^^^^^^

.. code:: python

	INSTALLED_APPS = (
		# ...
		'django_assets_manager',
	)

	STATICFILES_FINDERS = (
		'django.contrib.staticfiles.finders.FileSystemFinder',
		'django.contrib.staticfiles.finders.AppDirectoriesFinder',
		'django_assets_manager.finders.CdnFinder',
	)

	ASSETS_MANAGER_FILES = {
		"utils": {
			"js": "static://js/utils.js",
		},
		"cooleffect": {
			"js": ["static://js/cooleffect.js"],
			"css": ["static://css/cooleffect.css"],
			"depends": ["utils", "jquery"],
		},
		"jquery": {
			"js": "//code.jquery.com/jquery-2.1.4.min.js",
			"cache": {
				"paths": {
					"//code.jquery.com/jquery-2.1.4.min.js": "jquery-2.1.4.min.js",
				}
			},
		},
	}

	ASSETS_MANAGER_SPRITES = (
		{
			'name': 'main',
			'output': 'images/sprites.png',
			'scss_output': 'css/_sprites.scss',
			'extra_sizes': ((2, '@2x'),),
			'width': 640,
			'height': 640,
			'images': (
				{
					'name': 'logo',
					'src': 'img/logo.png',
				},
				{
					'name': 'bar_bg',
					'src': 'img/bar_bg.png',
					'mode': 'repeat-x',
				},
			),
		},
	)

Template
^^^^^^^^

.. code:: html

	{% load assets_manager %}
	{% assets "cooleffect" %}
	<!-- or -->
	{% assets_css "cooleffect" %}
	{% assets_js "cooleffect" %}
