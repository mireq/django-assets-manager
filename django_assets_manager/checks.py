# -*- coding: utf-8 -*-
from django.core.checks import Error

from .settings import SPRITES
from .utils import SpriteCompiler


def check_generated(**kwargs):
	errors = []

	compiler = SpriteCompiler()
	if compiler.recompilation_needed(SPRITES):
		errors.append(Error(
			'Sprites not generated',
			hint='Run manage.py compilesprites',
			id='django_assets_manager.E001'
		))
	return errors
