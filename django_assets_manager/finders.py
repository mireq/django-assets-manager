# -*- coding: utf-8 -*-
import os
from pathlib import Path

from django.conf import settings as django_settings
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.storage import FileSystemStorage
from urllib.request import urlopen

from . import settings


class CdnFinder(BaseFinder):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.storage = FileSystemStorage(location=django_settings.STATICFILES_DIRS[0])

	def find(self, path, all=False): #pylint: disable=redefined-builtin
		return [] # pragma: no cover

	def list(self, ignore_patterns):
		for package, data in settings.ASSETS.items():
			if "cache" in data:
				for src, dest in data["cache"]["paths"].items():
					dest_path = Path(self.storage.path(self.to_cache_path(package, dest)))
					if matches_patterns(dest, ignore_patterns): # pragma: no cover
						continue
					if not dest_path.exists():
						dest_path.parent.mkdir(parents=True, exist_ok=True)
						content = urlopen(self.to_url(src)).read()
						with dest_path.open('wb') as fp:
							fp.write(content)
					yield dest, self.storage

	def to_cache_path(self, package, dest):
		return os.path.join('CACHE', package, dest)

	def transform_and_check_path(self, package, path):
		dest_cache = settings.ASSETS.get(package, {}).get('cache', {}).get('paths', {})
		if not path in dest_cache:
			return path
		dest = self.to_cache_path(package, dest_cache[path])
		cache_path = Path(self.storage.path(dest))
		if cache_path.exists():
			return django_settings.STATIC_URL + dest
		else:
			return path

	def transform_to_cache(self, package, paths):
		return [self.transform_and_check_path(package, path) for path in paths]

	def to_url(self, url):
		if url[:2] == '//':
			url = 'http:' + url
		return url
