# -*- coding: utf-8 -*-
from django.conf import settings


ASSETS = getattr(settings, 'ASSETS_MANAGER_FILES', {})
SPRITES = getattr(settings, 'ASSETS_MANAGER_SPRITES', ())
USE_TEMPLATES = getattr(settings, 'ASSETS_MANAGER_USE_TEMPLATES', False)
