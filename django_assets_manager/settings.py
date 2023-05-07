# -*- coding: utf-8 -*-
from copy import deepcopy
from itertools import zip_longest

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.html import escape

from .finders import CdnFinder


ASSETS = getattr(settings, 'ASSETS_MANAGER_FILES', {})
SPRITES = list(getattr(settings, 'ASSETS_MANAGER_SPRITES', []))
USE_TEMPLATES = getattr(settings, 'ASSETS_MANAGER_USE_TEMPLATES', False)


finder = CdnFinder()


def transform_static(path):
	if path.find("static://") != 0:
		return path
	return settings.STATIC_URL + path[9:]


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

	asset["css"] = list(zip_longest(asset['css'], {}, fillvalue=''))
	asset["js"] = list(zip_longest(asset['js'], {}, fillvalue=''))
	return asset


@receiver(setting_changed)
def update_settings(**kwargs):
	setting = kwargs.get('setting')
	if setting is not None and setting not in {'ASSETS_MANAGER_FILES', 'ASSETS_MANAGER_SPRITES'}:
		return
	sprites = deepcopy(list(getattr(settings, 'ASSETS_MANAGER_SPRITES', [])))
	SPRITES.clear()
	SPRITES.extend(sprites)

	assets = deepcopy(getattr(settings, 'ASSETS_MANAGER_FILES', {}))
	ASSETS.clear()
	ASSETS.update({n: v for n, v in assets.items()}) # cache is used in convert_asset_data
	ASSETS.update({n: convert_asset_data(n, v) for n, v in assets.items()})
	# download assets
	list(finder.list(ignore_patterns=[]))
	assets = deepcopy(getattr(settings, 'ASSETS_MANAGER_FILES', {}))
	ASSETS.update({n: convert_asset_data(n, v) for n, v in assets.items()})


update_settings()
