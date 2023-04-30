# -*- coding: utf-8 -*-
import traceback
from itertools import chain

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from ..settings import ASSETS, USE_TEMPLATES


register = template.Library()


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


def render_css(context):
	return ''.join(f'<link rel="stylesheet" href="{css}" />' for css, __ in context['data'])


def render_js(context):
	return ''.join(f'<script src="{src}"{attributes}></script>' for src, attributes in context['data'])


def get_asset_sources(asset, unused, asset_type, render):
	if not asset in unused:
		if not asset in ASSETS:
			raise ImproperlyConfigured("Asset %s not registered" % asset)
		return ()

	asset_data = ASSETS[asset]
	unused.remove(asset)

	sources = []
	for depend in asset_data["depends"]:
		sources += get_asset_sources(depend, unused, asset_type, render)

	if asset_data[asset_type]:
		sources.append(render({'data': asset_data[asset_type]}))
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
		sources.append(render(context))
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
	if USE_TEMPLATES or asset_type not in ('css', 'js'):
		render = lambda context: render_to_string("assets_manager/" + asset_type + ".html", context)
	else:
		render = render_css if asset_type == 'css' else render_js

	return ''.join(chain(*(get_asset_sources(asset, unused, asset_type, render) for asset in asset_list)))


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
	try:
		from jinja2 import pass_context
	except ImportError:
		from jinja2 import contextfunction as pass_context

	library.global_function(pass_context(assets_js))
	library.global_function(pass_context(assets_css))
	library.global_function(pass_context(assets))
except ImportError:
	pass
