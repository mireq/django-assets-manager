# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings


ASSETS = getattr(settings, 'ASSETS_MANAGER_FILES', {})
SPRITES = getattr(settings, 'ASSETS_MANAGER_SPRITES', ())
