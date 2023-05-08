# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders


def find_file(path):
	return finders.find(path)


def to_localfile(path) -> Path:
	return Path.joinpath(Path(settings.STATICFILES_DIRS[0]), path)


class NoSpaceError(RuntimeError):
	pass


class AssetNotFoundError(RuntimeError):
	pass


class Packer:
	def __init__(self, width, height):
		self.root = {
			'pos': (0, 0),
			'size': (width + 1, height + 1), # 1px gap
			'used': False,
			'down': None,
			'right': None
		}

	def fit(self, blocks):
		repeat_mode = None

		for block in blocks:
			if not 'mode' in block:
				block['mode'] = 'no-repeat'
			if block['mode'] == 'repeat-x':
				self.fit_block_repeat_x(block)
				if repeat_mode is None or repeat_mode == 'x':
					repeat_mode = 'x'
				else:
					raise NoSpaceError('Can not mix repeat-x and repeat-y for %s' % block['name'])
			elif block['mode'] == 'repeat-y':
				self.fit_block_repeat_y(block)
				if repeat_mode is None or repeat_mode == 'y':
					repeat_mode = 'y'
				else:
					raise NoSpaceError('Can not mix repeat-x and repeat-y for %s' % block['name'])

		for block in blocks:
			if block['mode'] == 'no-repeat':
				self.fit_block(block)

	def fit_block(self, block):
		size = (block['width'] + 1, block['height'] + 1) # 1px gap
		node = self.find_node(self.root, size)
		if node is None:
			raise NoSpaceError('Block %s' % block['name'])
		self.split_node(node, size)
		node['used'] = block['name']
		block['pos'] = node['pos']
		block['size'] = (block['width'], block['height'])

	def fit_block_repeat_x(self, block):
		self.root['size'] = (self.root['size'][0], self.root['size'][1] - block['height'] - 1)
		if self.root['size'][1] <= -1:
			raise NoSpaceError('Block %s' % block['name'])

		block['pos'] = (0, self.root['size'][1])
		block['size'] = (self.root['size'][0] - 1, block['height'])

	def fit_block_repeat_y(self, block):
		self.root['size'] = (self.root['size'][0] - block['width'] - 1, self.root['size'][1])
		if self.root['size'][0] <= -1:
			raise NoSpaceError('Block %s' % block['name'])

		block['pos'] = (self.root['size'][0], 0)
		block['size'] = (block['width'], self.root['size'][1] - 1)

	def find_node(self, root, size):
		#if not root:
		#	return None

		if root['used']:
			return self.find_node(root['right'], size) or self.find_node(root['down'], size)

		w, h = size
		root_w, root_h = root['size']
		if w <= root_w and h <= root_h:
			return root

		return None

	def split_node(self, root, size):
		root_w, root_h = root['size']
		w, h = size
		x, y = root['pos']

		root['down'] =  {'pos': (x, y + h), 'size': (root_w, root_h - h), 'used': False, 'down': None, 'right': None}
		root['right'] = {'pos': (x + w, y), 'size': (root_w - w, h), 'used': False, 'down': None, 'right': None}


class SpriteGenerator:
	def __init__(self, filename, size, pixel_ratio):
		from PIL import Image
		self.filename = filename
		self.size = size
		self.pixel_ratio = pixel_ratio
		self.out_image = Image.new('RGBA', (size[0] * pixel_ratio, size[1] * pixel_ratio))

	def generate(self, images):
		for img in images:
			self.paste_image(img)
		output_filename = to_localfile(self.filename)
		output_filename.parent.mkdir(parents=True, exist_ok=True)
		self.out_image.save(output_filename)

	def paste_image(self, image):
		from PIL import Image
		in_image = Image.open(find_file(image['src']))
		if image['mode'] == 'repeat-x':
			w = image['width']
			for i in range((self.size[0] + w - 1) // w):
				self.out_image.paste(in_image, (i * w * self.pixel_ratio, image['pos'][1] * self.pixel_ratio))
		elif image['mode'] == 'repeat-y':
			h = image['height']
			for i in range((self.size[1] + h - 1) // h):
				self.out_image.paste(in_image, (image['pos'][0] * self.pixel_ratio, i * h * self.pixel_ratio))
		else:
			self.out_image.paste(in_image, (image['pos'][0] * self.pixel_ratio, image['pos'][1] * self.pixel_ratio))

	def generate_scss(self, sprites, sprite_configs):
		metadata = {
			'_w': str(sprites['width']) + 'px',
			'_h': str(sprites['height']) + 'px',
		}
		metadata['_size'] = metadata['_w'] + ' ' + metadata['_h']
		metadata['_ratio'] = '(' + (' '.join(str(config['ratio']) for config in sprite_configs)) + ')'
		metadata['_url'] = '(' + (' '.join('url(static("' + config['output'] + '"))' for config in sprite_configs)) + ')'

		f = open(to_localfile(sprites['scss_output']), 'w+')
		f.write('$' + sprites['name'] + ': (\n')
		for k, v in metadata.items():
			f.write(k + ': ' + v + ',\n')
		f.write(',\n'.join([self.generate_image_scss(img) for img in sprite_configs[0]['images']]))
		f.write('\n);')

	def generate_image_scss(self, image):
		w, h = (str(image['width']) + 'px', str(image['height']) + 'px')
		x, y = (str(image['pos'][0]) + 'px', str(image['pos'][1]) + 'px')
		ctx = {
			'name': image['original'],
			'w': w,
			'h': h,
			'x': x,
			'y': y,
			'size': w + ' ' + h,
			'offset': '-' + x + ' -' + y,
		}
		return '{name}: (w: {w}, h: {h}, x: {x}, y: {y}, size: {size}, offset: {offset})'.format(**ctx)


class SpriteCompiler:
	def compile(self, sprites):
		for sprite_def in sprites:
			self.pack_sprites(sprite_def)

	def pack_sprites(self, sprites):
		from PIL import Image
		sizes = ((1, ''),)
		sizes += tuple(sprites.get('extra_sizes', ()))

		for img in sprites['images']:
			if not 'width' in img or not 'height' in img:
				src_filename = find_file(img['src'])
				if src_filename is None:
					raise AssetNotFoundError("File %s not found" % img['src'])
				(width, height) = Image.open(src_filename).size
				img['width'] = width
				img['height'] = height

		sprite_configs = []
		for size, suffix in sizes:
			sprite_conf = self.preprocess_pixel_ratio(sprites, (size, suffix))
			packer = Packer(sprite_conf['width'], sprite_conf['height'])
			packer.fit(sprite_conf['images'])
			generator = SpriteGenerator(sprite_conf['output'], (sprite_conf['width'], sprite_conf['height']), size)
			generator.generate(sprite_conf['images'])
			sprite_configs.append(sprite_conf)
		generator.generate_scss(sprites, sprite_configs)

	def add_suffix(self, name, suffix):
		return suffix.join(os.path.splitext(name))

	def preprocess_pixel_ratio(self, sprites, size):
		ratio, suffix = size
		sprites = deepcopy(sprites)
		del sprites['extra_sizes']
		sprites['output'] = self.add_suffix(sprites['output'], suffix)
		sprites['ratio'] = ratio
		sprites['suffix'] = suffix

		for image in sprites['images']:
			image['original'] = image['name']
			image['name'] = image['name'] + suffix
			image['src'] = self.add_suffix(image['src'], suffix)

		return sprites

	def get_mtime(self, filename):
		try:
			return os.path.getmtime(filename)
		except OSError:
			return None

	def get_dependencies(self, sprites):
		dependencies = {}

		for sprite_def in sprites:
			sizes = ((1, ''),)
			sizes += tuple(sprite_def.get('extra_sizes', ()))

			for size, suffix in sizes:
				sprite_conf = self.preprocess_pixel_ratio(sprite_def, (size, suffix))
				deps = []
				dependencies[sprite_conf['output']] = {
					'ts': self.get_mtime(to_localfile(sprite_conf['output'])),
					'dep': deps,
				}
				for img in sprite_conf['images']:
					src_filename = find_file(img['src'])
					if src_filename is None:
						raise AssetNotFoundError("File %s not found" % img['src'])
					deps.append((img['src'], self.get_mtime(find_file(img['src']))))

		return dependencies

	def recompilation_needed(self, sprites):
		deps = self.get_dependencies(sprites)
		for dep in deps.values():
			if dep['ts'] is None:
				return True
			if any(img[1] > dep['ts'] for img in dep['dep']):
				return True
		return False
