# -*- coding: utf-8 -*-
from copy import deepcopy
from itertools import zip_longest

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.html import escape, format_html

from .finders import CdnFinder


ASSETS = getattr(settings, 'ASSETS_MANAGER_FILES', {})
SPRITES = getattr(settings, 'ASSETS_MANAGER_SPRITES', ())
USE_TEMPLATES = getattr(settings, 'ASSETS_MANAGER_USE_TEMPLATES', False)


finder = CdnFinder()


def transform_static(path):
	if path.find("static://") != 0:
		return path
	return settings.STATIC_URL + path[9:]


def render_attributes(attributes):
	return ''.join(format_html(' {}={}', key, value) for key, value in attributes)


def convert_asset_data(name, asset):
	asset.setdefault("depends", [])

	asset.setdefault("css", [])
	if isinstance(asset["css"], str):
		asset["css"] = [asset["css"]]
	asset['css'] = [transform_static(path) for path in asset['css']]
	asset['css'] = finder.transform_to_cache(name, asset['css'])
	asset['css'] = [escape(item) for item in asset['css']]

	asset.setdefault("js", [])
	if isinstance(asset["js"], str):
		asset["js"] = [asset["js"]]
	asset['js'] = [transform_static(path) for path in asset['js']]
	asset['js'] = finder.transform_to_cache(name, asset['js'])
	asset['js'] = [escape(item) for item in asset['js']]

	asset.setdefault("attributes", [])
	if isinstance(asset["attributes"], dict):
		asset["attributes"] = [asset["attributes"]]
	asset['attributes'] = [render_attributes(item) for item in asset['attributes']]

	asset["css"] = list(zip_longest(asset['css'], asset['attributes'], fillvalue=''))
	asset["js"] = list(zip_longest(asset['js'], asset['attributes'], fillvalue=''))
	return asset


@receiver(setting_changed)
def update_settings(**kwargs):
	setting = kwargs.get('setting')
	if setting is not None and setting != 'ASSETS_MANAGER_FILES':
		return
	assets = deepcopy(getattr(settings, 'ASSETS_MANAGER_FILES', {}))
	ASSETS.clear()
	ASSETS.update({n: convert_asset_data(n, v) for n, v in assets.items()})


update_settings()
