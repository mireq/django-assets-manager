# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import izip_longest

import traceback
from copy import deepcopy
from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from ..finders import CdnFinder
from ..settings import ASSETS


register = template.Library()
finder = CdnFinder()


class ShadowRequest(object):
	pass


class FakeRequest(object):
	def __init__(self, *args, **kwargs):
		super(FakeRequest, self).__init__(*args, **kwargs)
		self.__dict__['requests'] = [ShadowRequest(), ShadowRequest()]

	def __getattr__(self, item):
		fake = any(f[2] == 'render_nodelist' for f in traceback.extract_stack())
		return getattr(self.__dict__['requests'][0 if fake else 1], item)

	def __setattr__(self, item, value):
		fake = any(f[2] == 'render_nodelist' for f in traceback.extract_stack())
		return setattr(self.__dict__['requests'][0 if fake else 1], item, value)


def transform_static(path):
	if path.find("static://") != 0:
		return path
	return settings.STATIC_URL + path[9:]


def convert_asset_data(name, asset):
	asset.setdefault("depends", [])

	asset.setdefault("css", [])
	if isinstance(asset["css"], unicode):
		asset["css"] = [asset["css"]]
	asset['css'] = [transform_static(path) for path in asset['css']]
	asset['css'] = finder.transform_to_cache(name, asset['css'])

	asset.setdefault("js", [])
	if isinstance(asset["js"], unicode):
		asset["js"] = [asset["js"]]
	asset['js'] = [transform_static(path) for path in asset['js']]
	asset['js'] = finder.transform_to_cache(name, asset['js'])

	asset.setdefault("attributes", [])
	if isinstance(asset["attributes"], dict):
		asset["attributes"] = [asset["attributes"]]

	asset["css"] = list(izip_longest(asset['css'], asset['attributes'], fillvalue=[]))
	asset["js"] = list(izip_longest(asset['js'], asset['attributes'], fillvalue=[]))
	return asset


ASSETS = deepcopy(ASSETS)
ASSETS = {n: convert_asset_data(n, v) for n, v in ASSETS.iteritems()}


def get_asset_sources(asset, unused, asset_type):
	if not asset in unused:
		if not asset in ASSETS:
			raise ImproperlyConfigured("Asset %s not registered" % asset)
		return []

	asset_data = ASSETS[asset]
	unused.remove(asset)

	sources = []
	for depend in asset_data["depends"]:
		sources += get_asset_sources(depend, unused, asset_type)

	if asset_data[asset_type]:
		context = {
			"data": asset_data[asset_type],
		}
		sources.append(render_to_string("assets_manager/" + asset_type + ".html", context))
	return sources


def get_simple_asset_sources(asset, asset_type):
	if not asset in ASSETS:
		raise ImproperlyConfigured("Asset %s not registered" % asset)

	asset_data = ASSETS[asset]
	sources = []

	if asset_data[asset_type]:
		context = {
			"data": asset_data[asset_type],
		}
		sources.append(render_to_string("assets_manager/" + asset_type + ".html", context))
	return sources


def get_or_create_unused_assets(context, asset_type):
	if not "request" in context:
		context["request"] = FakeRequest()
	if hasattr(context["request"], "unused_" + asset_type):
		return getattr(context["request"], "unused_" + asset_type)
	else:
		unused_assets = set(ASSETS.keys())
		setattr(context["request"], "unused_" + asset_type, unused_assets)
		return unused_assets


def assets_by_type(context, asset_type, *asset_list):
	unused = get_or_create_unused_assets(context, asset_type)
	asset_sources = []
	for asset in asset_list:
		asset_sources += get_asset_sources(asset, unused, asset_type)
	return "".join(asset_sources)


@register.simple_tag(takes_context=True)
def assets_js(context, *asset_list):
	return mark_safe(assets_by_type(context, "js", *asset_list))


@register.simple_tag(takes_context=True)
def assets_css(context, *asset_list):
	return mark_safe(assets_by_type(context, "css", *asset_list))


@register.simple_tag(takes_context=True)
def assets(context, *asset_list):
	return mark_safe(assets_css(context, *asset_list) + assets_js(context, *asset_list))
