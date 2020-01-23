# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from ... import utils
from ...settings import SPRITES


class Command(BaseCommand):
	requires_system_checks = False

	def handle(self, *args, **opions): #pylint: disable=unused-argument
		compiler = utils.SpriteCompiler()
		compiler.compile(SPRITES)
