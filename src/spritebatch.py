import pygame
import json

from src.constants import *
from src.mymath import *

class DrawCache:
	def __init__(self):
		self.bgtilecache = []

# one spritebatch for animated sprites, one for not (i.e. geometry)
# NOTE: ^^ is this true? Are we doing this?
class SpriteBatch:
	def __init__(self):
		self.length = 0

		self.sprites = []

		fin = open('./data/graphics/texture-data.json')
		data = json.load(fin)
		fin.close()

		# load UI elements
		self.ui_frame_texture = pygame.image.load('./res/ui-frame.png').convert_alpha()
		self.ui_frame_texture = pygame.transform.scale_by(self.ui_frame_texture, TILE_ZOOM * 2)

		# load tilemap (TODO: eventually load all tilemaps)
		self.tilemap_texture = pygame.image.load(data['tilemap']['filepath']).convert_alpha()
		self.tilemap_dim = (
			self.tilemap_texture.get_rect().width // TILE_WIDTH, 
			self.tilemap_texture.get_rect().height // TILE_WIDTH
		)
		#print(self.tilemap_dim)
		
		# load entities
		self.entity64_texture = pygame.image.load(data['entities64']['filepath']).convert_alpha()

		# scale everything as necessary
		self.tilemap_texture = pygame.transform.scale_by(self.tilemap_texture, TILE_ZOOM)
		self.entity64_texture = pygame.transform.scale_by(self.entity64_texture, TILE_ZOOM)

		# also keep a flipped image so we don't have to do it every frame per entity
		self.entity64_texture_flipped = pygame.transform.flip(self.entity64_texture, True, False)
		self.entity64_texture_pxwidth = self.entity64_texture.get_rect().width

	def draw_ui_overlay(self):
		result = []

		image = self.ui_frame_texture
		area = Rect((0, 0), (WIN_WIDTH, WIN_HEIGHT))
		result.append((image, (0, 0), area.get_pyrect()))
		
		return result

	def get_screenpos_from_mappos(map_pos):
		screen_pos = v2_mult(map_pos, TILE_ZOOM)
		screen_pos = v2_add((GAMEMAP_SCREEN_X, GAMEMAP_SCREEN_Y), screen_pos)
		return screen_pos

	def draw_tile(self, tilemapindex, pos):
		# scale image to the rect
		#scale = (TILE_WIDTH * camera.zoom, TILE_WIDTH * camera.zoom)
		'''
		zoomed_tile_width = TILE_WIDTH * TILE_ZOOM
		scale = (zoomed_tile_width, zoomed_tile_width)
		image = pygame.transform.scale(self.tilemap_texture, scale)
		'''
		image = self.tilemap_texture

		tile_y = tilemapindex // self.tilemap_dim[0]
		tile_x = tilemapindex - (tile_y * self.tilemap_dim[0])
		tilearea = Rect(
			(tile_x * TILE_WIDTH, tile_y * TILE_WIDTH),
			(TILE_WIDTH, TILE_WIDTH)
		)

		result = (image, Rect((pos[0], pos[1]), (zoomed_tile_width, zoomed_tile_width)).get_pyrect(), tilearea.get_pyrect())
		return result

	def draw_tilelayer(self, regionmap, tilelayer):

		# scale image to the rect
		scale_factor = 1
		scaled_width = ZOOMED_WIDTH
		image = self.tilemap_texture
		'''
		if (not scale_factor == 1):
			scaled_width *= scale_factor
			image = pygame.transform.scale_by(self.tilemap_texture, scale_factor)
		'''

		result = []

		for y in range(GAMEMAP_TILES_HIGH):
			for x in range(GAMEMAP_TILES_WIDE):
				tilemapindex = regionmap.tile_layers[tilelayer][y * GAMEMAP_TILES_WIDE + x]
				#print(tilemapindex)
				tile_y = tilemapindex // self.tilemap_dim[0]
				tile_x = tilemapindex - (tile_y * self.tilemap_dim[0])

				# skip if tile is the blank tile
				if tilemapindex == 0:
					continue

				tilearea = Rect(
					(tile_x * scaled_width, tile_y * scaled_width),
					(scaled_width, scaled_width)
				)

				map_pos = (x * TILE_WIDTH, y * TILE_WIDTH)
				screen_pos = SpriteBatch.get_screenpos_from_mappos(map_pos)

				result.append(
					(image, 
					Rect(screen_pos, (scaled_width, scaled_width)).get_pyrect(), 
					tilearea.get_pyrect())
				)

		return result

	def draw_entity(self, entity):

		scale_factor = TILE_ZOOM
		image = None

		width = entity.frame_size
		if (width == 64):
			if entity.flipanimhorz:
				image = self.entity64_texture_flipped
			else:
				image = self.entity64_texture 
		else:
			pass

		zoomed_width = scale_factor * width

		tile_x, tile_y = entity.curr_animation.sample()

		# since the source images are flipped, we need to get the area starting from the right side on flip
		if entity.flipanimhorz:
			tilearea = Rect(
				(self.entity64_texture_pxwidth - (tile_x+1) * zoomed_width, tile_y * zoomed_width),
				(zoomed_width, zoomed_width)
			)
		else:
			tilearea = Rect(
				(tile_x * zoomed_width, tile_y * zoomed_width),
				(zoomed_width, zoomed_width)
			)

		map_pos = entity.get_pos()
		bottom_of_collision_box = v2_add(map_pos, (0, entity.coll_height))
		screen_pos = SpriteBatch.get_screenpos_from_mappos(bottom_of_collision_box)
		drawpos = v2_add(screen_pos, (-zoomed_width/2, -zoomed_width))

		result = (image, Rect(drawpos, (zoomed_width, zoomed_width)).get_pyrect(), tilearea.get_pyrect())
		
		return result