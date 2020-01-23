# -*- coding: utf-8 -*-
import traceback
from copy import deepcopy
from itertools import zip_longest

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..finders import CdnFinder
from ..settings import ASSETS, USE_TEMPLATES


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
	if isinstance(asset["css"], str):
		asset["css"] = [asset["css"]]
	asset['css'] = [transform_static(path) for path in asset['css']]
	asset['css'] = finder.transform_to_cache(name, asset['css'])

	asset.setdefault("js", [])
	if isinstance(asset["js"], str):
		asset["js"] = [asset["js"]]
	asset['js'] = [transform_static(path) for path in asset['js']]
	asset['js'] = finder.transform_to_cache(name, asset['js'])

	asset.setdefault("attributes", [])
	if isinstance(asset["attributes"], dict):
		asset["attributes"] = [asset["attributes"]]

	asset["css"] = list(zip_longest(asset['css'], asset['attributes'], fillvalue=[]))
	asset["js"] = list(zip_longest(asset['js'], asset['attributes'], fillvalue=[]))
	return asset


ASSETS = deepcopy(ASSETS)
ASSETS = {n: convert_asset_data(n, v) for n, v in ASSETS.items()}


def render_css(context):
	return ''.join(format_html('<link rel="stylesheet" href="{}" />', css) for css, __ in context['data'])


def render_attributes(attributes):
	return ''.join(format_html(' {}={}', key, value) for key, value in attributes)


def render_js(context):
	return ''.join(format_html('<script src="{}" type="text/javascript" charset="utf-8"{}></script>', src, render_attributes(attributes)) for src, attributes in context['data'])


def get_asset_sources(asset, unused, asset_type, render):
	if not asset in unused:
		if not asset in ASSETS:
			raise ImproperlyConfigured("Asset %s not registered" % asset)
		return []

	asset_data = ASSETS[asset]
	unused.remove(asset)

	sources = []
	for depend in asset_data["depends"]:
		sources += get_asset_sources(depend, unused, asset_type, render)

	if asset_data[asset_type]:
		context = {
			"data": asset_data[asset_type],
		}
		sources.append(render(context))
	return sources


def get_simple_asset_sources(asset, asset_type, render):
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
		extra = {'request': FakeRequest()}
		if hasattr(context, 'update'):
			context.update(extra)
		else:
			context.vars.update(extra)
	if hasattr(context["request"], "unused_" + asset_type):
		return getattr(context["request"], "unused_" + asset_type)
	else:
		unused_assets = set(ASSETS.keys())
		setattr(context["request"], "unused_" + asset_type, unused_assets)
		return unused_assets


def assets_by_type(context, asset_type, *asset_list):
	unused = get_or_create_unused_assets(context, asset_type)
	asset_sources = []
	if USE_TEMPLATES or asset_type not in ('css', 'js'):
		render = lambda context: render_to_string("assets_manager/" + asset_type + ".html", context)
	else:
		render = render_css if asset_type == 'css' else render_js

	for asset in asset_list:
		if USE_TEMPLATES or asset_type not in ('css', 'js'):
			asset_sources += get_asset_sources(asset, unused, asset_type, render)
		else:
			asset_sources += get_asset_sources(asset, unused, asset_type, render)
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


try:
	from django_jinja import library
	from jinja2 import contextfunction

	library.global_function(contextfunction(assets_js))
	library.global_function(contextfunction(assets_css))
	library.global_function(contextfunction(assets))
except ImportError:
	pass
