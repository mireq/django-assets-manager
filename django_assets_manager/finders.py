# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.storage import FileSystemStorage
from django.utils.functional import cached_property
from six.moves.urllib.request import urlopen


class CdnFinder(BaseFinder):
	def __init__(self, *args, **kwargs):
		super(CdnFinder, self).__init__(*args, **kwargs)
		self.storage = FileSystemStorage(location=settings.STATICFILES_DIRS[0])

	@cached_property
	def settings(self):
		from . import settings as s
		return s

	def find(self, path, all=False): #pylint: disable=redefined-builtin
		return []

	def list(self, ignore_patterns):
		for package, data in self.settings.ASSETS.items():
			if "cache" in data:
				for src, dest in data["cache"]["paths"].items():
					dest = self.to_cache_path(package, dest)
					if matches_patterns(dest, ignore_patterns):
						continue
					dest_dir = os.path.dirname(dest)
					if not os.path.exists(self.storage.path(dest_dir)):
						os.makedirs(self.storage.path(dest_dir))
					if not os.path.exists(self.storage.path(dest)):
						with open(self.storage.path(dest), 'wb') as fp:
							fp.write(urlopen(self.to_url(src)).read())
					yield dest, self.storage

	def to_cache_path(self, package, dest):
		return os.path.join('CACHE', package, dest)

	def transform_and_check_path(self, package, path):
		dest_cache = self.settings.ASSETS.get(package, {}).get('cache', {}).get('paths', {})
		if not path in dest_cache:
			return path
		dest = self.to_cache_path(package, dest_cache[path])
		cache_path = self.storage.path(dest)
		if os.path.exists(cache_path):
			return settings.STATIC_URL + dest
		else:
			return path

	def transform_to_cache(self, package, paths):
		return [self.transform_and_check_path(package, path) for path in paths]

	def to_url(self, url):
		if url[:2] == '//':
			url = 'http:' + url
		return url
