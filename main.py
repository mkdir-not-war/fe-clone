import os

# Maybe people want to keep watching the joystick feedback even when this
# window doesn't have focus. Possibly by capturing this window into OBS.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

# A tiny performance/latency hit isn't a problem here. Instead, it's more
# important to keep the desktop compositing effects running fine. Disabling
# compositing is known to cause issues on KDE/KWin/Plasma/X11 on Linux.
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"

import pygame
from enum import IntEnum
from tkinter import Tk 
import json
import sys

from src.getmath import *
from src.myinput import *
from src.collision import *
from src.constants import *
import src.myanim as myanim

# window constants
WIN_WIDTH = 1050
WIN_HEIGHT = 600

# map info and draw constants
TILE_ZOOM = 2
ZOOMED_WIDTH = TILE_WIDTH * TILE_ZOOM
TILEMAP_WIDTH_IN_TILES = 8
TILEMAP_NUM_ANIMATED_ROWS = 2
TILEMAP_FRAMES_PER_ANIMATION = 16
TILEMAP_TILES_PER_ANIMATION = 4
TILEMAP_BLANK_TILE_INDEX = TILEMAP_NUM_ANIMATED_ROWS * TILEMAP_WIDTH_IN_TILES

# camera constants
CAMERA_TILES_WIDE = 16 # even number
CAMERA_TILES_HIGH = 10 # even number
CAMERA_PXOFFSET_FROM_PLAYER = (0, -12)

GAMEMAP_WIDTH = 600

# physics constants
PLAYER_MAXSPEED = 10.0 * TILE_WIDTH
PLAYER_MINSPEED_SQ = 1.0
PLAYER_MAXSPEED_SQ = PLAYER_MAXSPEED**2

PLAYER_FRICTION = 0.1 * PLAYER_MAXSPEED
PLAYER_ACCEL = 0.03 * PLAYER_MAXSPEED_SQ

# misc constants
PHYSICS_TIME_STEP = 1.0/100
NUM_REGIONS_IN_WORLD = 1

# colors
neutralgrey = pygame.Color(150, 150, 160)
darkgrey = pygame.Color(50, 50, 65)
darkred = pygame.Color(80, 0, 0)
lightred = pygame.Color(250, 100, 100)
lightblue = pygame.Color(100, 100, 250)
black = pygame.Color('black')
white = pygame.Color('white')

# fonts
pygame.font.init()
font_arial16 = pygame.font.Font('./data/fonts/ARI.ttf', 16)

# collision data for tilemap
colfin = open('./data/maps/collisiontilemap.dat', 'r')
tilemap_coldata = [int(i) for i in colfin.read().split(' ')]
colfin.close()

class DrawCache:
	def __init__(self):
		self.bgtilecache = []

# one spritebatch for animated sprites, one for not (i.e. geometry)
class SpriteBatch:
	def __init__(self):
		self.length = 0

		self.sprites = []

		fin = open('./data/graphics/texture-data.json')
		data = json.load(fin)
		fin.close()

		# load tilemap
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

	def get_screenpos_from_mappos(map_pos, camera_pos):
		screen_pos = v2_mult(v2_sub(map_pos, camera_pos), TILE_ZOOM)
		screen_pos = v2_add(screen_pos, (WIN_WIDTH / 2, WIN_HEIGHT / 2))
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

	def draw_tilelayer(self, regionmap, tilelayer, camerabounds, camerapos):

		min_x_tile, max_x_tile, min_y_tile, max_y_tile = camerabounds

		# scale image to the rect
		scale_factor = 1 # * camera.zoom
		scaled_width = ZOOMED_WIDTH
		image = self.tilemap_texture
		'''
		if (not scale_factor == 1):
			scaled_width *= scale_factor
			image = pygame.transform.scale_by(self.tilemap_texture, scale_factor)
		'''

		result = []

		# TODO: if index is in animated range, 
		#       draw animated using animationstep in editorstate

		for y in range(min_y_tile, max_y_tile):
			for x in range(min_x_tile, max_x_tile):
				tilemapindex = regionmap.tile_layers[tilelayer][y * regionmap.width + x]
				#print(tilemapindex)
				tile_y = tilemapindex // self.tilemap_dim[0]
				tile_x = tilemapindex - (tile_y * self.tilemap_dim[0])

				# skip if tile is the blank tile
				if tile_x == 0 and tile_y == TILEMAP_NUM_ANIMATED_ROWS:
					continue

				tilearea = Rect(
					(tile_x * scaled_width, tile_y * scaled_width),
					(scaled_width, scaled_width)
				)

				map_pos = (x * TILE_WIDTH, y * TILE_WIDTH)
				screen_pos = SpriteBatch.get_screenpos_from_mappos(map_pos, camerapos)

				result.append(
					(image, 
					Rect(screen_pos, (scaled_width, scaled_width)).get_pyrect(), 
					tilearea.get_pyrect())
				)

		return result

	def draw_entity(self, entity, camerapos):

		scale_factor = TILE_ZOOM # * camera.zoom
		image = None

		width = entity.frame_size
		if (width == 64):
			# zoom here if we decide the camera can do that
			if entity.flipanimhorz:
				image = self.entity64_texture_flipped
			else:
				image = self.entity64_texture 
		else:
			pass

		# TODO: zoom here if we decide the camera can do that
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
		screen_pos = SpriteBatch.get_screenpos_from_mappos(bottom_of_collision_box, camerapos)
		drawpos = v2_add(screen_pos, (-zoomed_width/2, -zoomed_width))

		result = (image, Rect(drawpos, (zoomed_width, zoomed_width)).get_pyrect(), tilearea.get_pyrect())
		
		return result

class TileLayer(IntEnum):
	BG 		= 0
	MG1 	= 1
	MG2 	= 2
	FG 		= 3

class RegionMap:
	def __init__(self):

		# TODO: load map data from a map file eventually, and entity positions and shit too

		self.width = 24
		self.height = 13
		
		'''
		self.bg_tilelayer = [
			18, 19, 19, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			18, 18, 18, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			19, 19, 20, 20, 18, 19, 18, 19, 19, 18, 19, 18,
			18, 19, 20, 20, 18, 18, 18, 19, 19, 18, 19, 18,
			18, 18, 19, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			19, 19, 18, 18, 19, 18, 18, 19, 19, 18, 19, 18] * 4 # 100% full (width * height)
		'''

		# test combat map -- grass and fenced-in area
		self.tile_layers = [[]] * 4

		self.tile_layers[TileLayer.BG] = [
			18, 19, 19, 18, 20, 18, 19, 20, 18, 19, 18, 19, 20, 20, 19, 18, 19, 19, 18, 18, 18, 18, 19, 35,
			19, 19, 18, 18, 19, 18, 19, 18, 18, 19, 19, 18, 20, 18, 19, 18, 18, 19, 18, 19, 20, 20, 19, 34,
			19, 19, 18, 19, 19, 18, 20, 18, 19, 18, 18, 19, 18, 19, 20, 20, 19, 18, 19, 20, 19, 19, 19, 18,
			19, 20, 20, 18, 25, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 27, 20, 18, 19, 18, 18, 19, 18, 
			20, 19, 19, 20, 33, 34, 68, 34, 34, 68, 68, 68, 34, 68, 34, 68, 35, 20, 18, 18, 18, 18, 19, 35,
			18, 19, 20, 19, 33, 34, 68, 68, 68, 68, 68, 34, 68, 68, 68, 34, 35, 19, 19, 18, 20, 18, 19, 18, 
			18, 19, 19, 18, 33, 68, 34, 68, 68, 34, 34, 68, 68, 34, 34, 34, 35, 19, 18, 18, 19, 19, 18, 36,
			19, 19, 18, 18, 33, 68, 68, 34, 34, 68, 34, 34, 34, 68, 34, 68, 35, 19, 20, 20, 19, 18, 18, 19, 
			19, 18, 19, 20, 33, 68, 34, 68, 68, 34, 68, 34, 68, 34, 68, 34, 35, 20, 18, 19, 18, 20, 19, 35,
			20, 19, 18, 19, 41, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 43, 19, 18, 19, 20, 20, 19, 34,
			19, 20, 19, 20, 20, 19, 18, 18, 18, 19, 20, 19, 19, 19, 19, 18, 19, 19, 18, 20, 18, 19, 18, 18, 
			18, 20, 18, 19, 19, 18, 19, 19, 18, 20, 18, 19, 18, 18, 19, 18, 19, 20, 20, 19, 18, 19, 19, 18,
			19, 19, 18, 19, 19, 18, 20, 18, 19, 18, 18, 19, 18, 19, 20, 20, 19, 18, 19, 20, 19, 19, 19, 18
		]

		bl = TILEMAP_BLANK_TILE_INDEX
		self.tile_layers[TileLayer.MG1] = [
			bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 93, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 94, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 89, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, 88, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, 101, 86, 86, 86, 86, 86, 86, 86, 86, 86, 86, 86, 86, 86, 102, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl,
			bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl, bl
		]

		self.tile_layers[TileLayer.MG2] = [bl] * self.width * self.height # sparse -> (tileindex, x, y)
		self.tile_layers[TileLayer.FG] = [bl] * self.width * self.height # sparse -> (tileindex, x, y)

		self.collisionmap = self.load_collisionmap()

		self.curr_spawn_tile = (6, 5)

	def get_spawnpos(self):
		return (
			self.curr_spawn_tile[0]*TILE_WIDTH + TILE_WIDTH//2,
			self.curr_spawn_tile[1]*TILE_WIDTH + TILE_WIDTH//2
		)

	'''
	use this for int-map of collision tiles

	0x0000_1234 =>

		1  2

		3  4 (not that we would ever use 2, 3 or 4. Just showing them here for illustration purpose)

	'''
	def get_colltile(self, coltilex, coltiley):
		tilex = coltilex // 2
		tiley = coltiley // 2
		xoff = coltilex % 2
		yoff = coltiley % 2 # because collision is 2x2 grid on each tile

		collint = self.collisionmap[tilex + tiley * self.width]
		bitmask = (0x1 << yoff*8) << xoff*4

		return collint & bitmask > 0

	def load_collisionmap(self):
		# go through each of the tile layers, OR the coll ints
		result = []

		for i in range(self.width*self.height):
			collint = 0

			collint |= tilemap_coldata[self.tile_layers[TileLayer.BG][i]]
			collint |= tilemap_coldata[self.tile_layers[TileLayer.MG1][i]]
			collint |= tilemap_coldata[self.tile_layers[TileLayer.MG2][i]]
			# NOTE: foreground (fg) layer does not collide

			result.append(collint)

		return result

class WorldMap:
	def __init__(self):
		self.curr_region_index = 0
		self.regionmaps = [RegionMap()] * NUM_REGIONS_IN_WORLD

	def regionmap(self):
		return self.regionmaps[self.curr_region_index]

class Entity:
	def __init__(self):
		# basic position
		self.prev_x = 0
		self.prev_y = 0
		self.x = 0
		self.y = 0

		# movement physics stuff
		self.ddp = (0, 0)
		self.dp = (0, 0)

		# animation stuff
		self.curr_animation = None
		self.frame_size = 64
		self.flipanimhorz = False
		self.facing_direction = None
		self.facing_stunned = False # when this is on, don't turn directions

		# collision stuff
		# width and height are half the length of the rectangle -- position is in the center of the rect
		self.coll_width = 0 # since we only have width and height, 
		self.coll_height = 0 # entity collision shapes are only rectangles?
		# TODO: maybe later we condier circular collision as well? Not sure if needed
		# 		remember, collision isn't the same as hit/hurt boxes.
		self.wall2N = False
		self.wall2S = False
		self.wall2E = False
		self.wall2W = False

	def get_prevpos(self):
		return (self.prev_x, self.prev_y)

	def set_pos(self, x, y):
		self.prev_x = self.x
		self.prev_y = self.y
		self.x = x
		self.y = y

	def spawn(self, x, y):
		self.prev_x = x
		self.prev_y = y
		self.x = x
		self.y = y

	def move(self, dir):
		self.prev_x = self.x
		self.prev_y = self.y
		self.x += dir[0]
		self.y += dir[1]

	# position is in pixels, not in tiles
	def get_pos(self):
		return (self.x, self.y)

	# position in tiles
	def get_tile(self):
		return (self.x // TILE_WIDTH, self.y // TILE_WIDTH)

	def update(self, **kwargs):
		pass

class PlayerAnimState(IntEnum):
	IDLE = 0
	WALK = 1

# NOTE: player does not have player-specific variables -- everything goes in entity
# player is really just an Init function and an Update function. That's it.
# Still useful to inherit Entity because we can use the Update function polymorphed
class Player(Entity):
	def __init__(self):
		super().__init__()
		self.curr_animation = myanim.Animation()
		myanim.load_animation(self.curr_animation, 'player', 'idle-side')

		self.facing_direction = InputMoveDir.RIGHT
		self.input_ddp = (0, 0)
		self.animstate = PlayerAnimState.IDLE

	def update(self, **kwargs):
		dt = PHYSICS_TIME_STEP

		# ddp starts as exactly equal to input direction (<= 1.0 length)
		self.ddp = v2_mult(self.input_ddp, PLAYER_ACCEL)

		# add friction force
		self.ddp = v2_sub(self.ddp, v2_mult(self.dp, PLAYER_FRICTION))

		# simple motion integral
		self.move(v2_add(v2_mult(self.ddp, 0.5 * dt**2), v2_mult(self.dp, dt))) # change pos before velocity
		self.dp = v2_add(self.dp, v2_mult(self.ddp, dt))

		# change facing direction based on movement
		if not self.facing_stunned:
			self.facing_direction = v2_to_facingdirection(self.facing_direction, self.input_ddp)

		# change animation
		if self.input_ddp == (0, 0):
			self.change_animation(PlayerAnimState.IDLE)
		else:
			self.change_animation(PlayerAnimState.WALK)

		# flip animation if facing left	
		if (self.facing_direction in [InputMoveDir.LEFT, InputMoveDir.LEFT_UP, InputMoveDir.LEFT_DOWN]):
			self.flipanimhorz = True
		else:
			self.flipanimhorz = False

	def change_animation(self, newanimstate):
		if newanimstate != self.animstate:
			self.animstate = newanimstate

			if newanimstate == PlayerAnimState.IDLE:
				myanim.load_animation(self.curr_animation, 'player', 'idle-side')
			elif newanimstate == PlayerAnimState.WALK:
				myanim.load_animation(self.curr_animation, 'player', 'walk-side')

# hexagonal facing directions -- no pure up/down.
def v2_to_facingdirection(currdirection, v2):
	result = currdirection

	if v2 != (0, 0):
		dpx, dpy = v2
		# discrete thumbstick/keyboard directions
		if dpx > 0:
			if dpx**2 > dpy**2:
				result = InputMoveDir.RIGHT
			elif dpy < 0:
				result = InputMoveDir.RIGHT_UP
			elif dpy > 0:
				result = InputMoveDir.RIGHT_DOWN
		elif dpx < 0:
			if dpx**2 > dpy**2:
				result = InputMoveDir.LEFT
			elif dpy < 0:
				result = InputMoveDir.LEFT_UP
			elif dpy > 0:
				result = InputMoveDir.LEFT_DOWN
		else: # no x-direction, default facing right
			if dpy > 0:
				result = InputMoveDir.RIGHT_DOWN
			elif dpy < 0:
				result = InputMoveDir.RIGHT_UP

	return result

class Camera(Entity):
	def __init__(self):
		super().__init__()
		self.target_pos = None

	def update(self, **kwargs):
		dt = PHYSICS_TIME_STEP

		self.target_pos = v2_add(kwargs['playerpos'], CAMERA_PXOFFSET_FROM_PLAYER)
		
		self.set_pos(*self.target_pos)

		# TODO: do some smoothing here to follow the character a bit more loosely?
		#self.move()

def get_tilebounds_from_camera(cameraentity, mapwidth, mapheight):
	tile_x_pos, tile_y_pos = v2_int(v2_mult(cameraentity.get_pos(), 1/TILE_WIDTH))

	result = [0, 0, 0, 0]
	result[0] = max(tile_x_pos - (CAMERA_TILES_WIDE // 2 + 2), 0)
	result[1] = min(tile_x_pos + CAMERA_TILES_WIDE // 2 + 2, mapwidth-1)
	result[2] = max(tile_y_pos - (CAMERA_TILES_HIGH // 2 + 2), 0)
	result[3] = min(tile_y_pos + CAMERA_TILES_HIGH // 2 + 2, mapheight-1)

	return result

# class to hold essentially global vars
class SimulationState:
	def __init__(self):
		# animated tile stuff
		self.animation_step = 0 # always under MAX_ANIM_FRAMES

		# input stuff
		self.joystick = JoystickHandler(0)
		self.inputdata = InputDataBuffer()
		self.curr_inputhandler = None

		# debug stuff
		self.debugstuff = {}

		# players, actors, obstacles. Anything that needs to be physically updated
		self.entities = []
		self.entities.append(Player()) # player is index 0
		self.entities[0].coll_width = TILE_WIDTH * 0.4 # half width of collision rect
		self.entities[0].coll_height = TILE_WIDTH * 0.2 # half height of collision rect

	def animate(self):
		for entity in self.entities:
			if entity.curr_animation:
				entity.curr_animation.stepfunc()

	def get_player(self):
		return self.entities[0]

def main(argv):
	pygame.init()
	pygame.event.set_blocked((pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN))
	Tk().withdraw()

	# Set the width and height of the screen (width, height).
	screendim = (WIN_WIDTH, WIN_HEIGHT)
	window = pygame.display.set_mode(screendim)#, flags=pygame.SRCALPHA)
	pygame.display.set_caption("topdown game")

	done = False
	clock = pygame.time.Clock()

	# cache structure for all sprite flyweights
	spritebatch = SpriteBatch()

	# input handlers
	inputhandlers = [IH_MovingAround()]

	# editor state
	simstate = SimulationState()
	simstate.curr_inputhandler = inputhandlers[0]
	worldmap = WorldMap()
	camera = Camera()

	# set player spawn
	simstate.entities[0].spawn(*worldmap.regionmap().get_spawnpos())

	# drawing caches
	drawcache = DrawCache()

	# timing stuff
	t = 0.0
	accum = 0.0

	# debug variables
	current_fps = 0

	while not done:
		frametime = clock.tick(60) # time passed in millisecondss
		accum += frametime/1000.0

		# display FPS
		current_fps = int(clock.get_fps()*0.5 + current_fps*0.5)
		simstate.debugstuff['FPS'] = current_fps

		# poll input and update physics 100 times a second
		while (accum >= PHYSICS_TIME_STEP):
			accum -= PHYSICS_TIME_STEP
			t += PHYSICS_TIME_STEP

			################################################################################
			# INPUT ########################################################################
			################################################################################

			# poll input, put in curr_input and prev_input
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					quit()
				elif event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_q]:
					quit()
				elif event.type == pygame.JOYBUTTONDOWN and event.button == 6: # select button to quit
					quit()
				elif event.type == pygame.JOYAXISMOTION:
					simstate.joystick.axis[event.axis] = event.value
				elif event.type == pygame.JOYBALLMOTION:
					simstate.joystick.ball[event.ball] = event.rel
				elif event.type == pygame.JOYHATMOTION:
					simstate.joystick.hat[event.hat] = event.value
				elif event.type == pygame.JOYBUTTONUP:
					simstate.joystick.button[event.button] = 0
				elif event.type == pygame.JOYBUTTONDOWN:
					simstate.joystick.button[event.button] = 1

			# TODO: handle input
			simstate.inputdata.newinput(simstate.joystick)
			simstate.curr_inputhandler.handle_input(simstate)

			################################################################################
			# UPDATE #######################################################################
			################################################################################

			# update all of the entities
			for entity in simstate.entities:
				entity.update()

			# bound entities by collision
			# QUESTION: if enemy AI avoids collision, do we really
			# 	need to check collision on any entities other than the player?
			# ANSWER: Yes, because the player's attacks often cause the enemies to move back,
			#	potentially against a wall, for example
			for entity in simstate.entities:
				do_collision(worldmap.regionmap(), entity)

			playercollisions = []

			# debug stuff
			## simstate.debugstuff['inputsize'] = len(simstate.curr_input)

			# update camera and animation step (not tied to frame rate!)
			camera.update(playerpos=simstate.entities[0].get_pos())
			simstate.animate()

			#print(simstate.entities[0].get_pos()) # print player pos

		################################################################################
		# DRAW! ########################################################################
		################################################################################

		# Start drawing
		window.fill(neutralgrey) # TODO: change this to off-black??

		regionmap = worldmap.regionmap()
		cam_bounds = get_tilebounds_from_camera(camera, regionmap.width, regionmap.height)
		cam_pos = camera.get_pos()

		# draw background tile layers, cache if helpful
		if (not cam_pos == camera.get_prevpos() or not drawcache.bgtilecache):
			drawcache.bgtilecache = spritebatch.draw_tilelayer(regionmap, TileLayer.BG, cam_bounds, cam_pos)
		window.blits(drawcache.bgtilecache)

		# draw middleground tile layers, no need to cache since sparse
		mgtiles = spritebatch.draw_tilelayer(regionmap, TileLayer.MG1, cam_bounds, cam_pos)
		window.blits(mgtiles)
		mgtiles = spritebatch.draw_tilelayer(regionmap, TileLayer.MG2, cam_bounds, cam_pos)
		window.blits(mgtiles)

		# DEBUG: draw rects where there are collision in the collision map
		'''
		collisionrectdim = (COLTILE_WIDTH * TILE_ZOOM + 1, COLTILE_WIDTH * TILE_ZOOM + 1)
		for y in range(regionmap.height * 2):
			for x in range(regionmap.width * 2):
				if (not regionmap.get_colltile(x, y)):
					continue
				screenpos = SpriteBatch.get_screenpos_from_mappos(
					(x * COLTILE_WIDTH, y * COLTILE_WIDTH), 
					cam_pos
				)
				pygame.draw.rect(window, black, Rect(screenpos, collisionrectdim).get_pyrect(), 1)
		'''
		

		# draw entities
		blitlist = []
		for entity in simstate.entities:
			if (entity.curr_animation):
				blitlist.append(spritebatch.draw_entity(entity, cam_pos))
		window.blits(blitlist)

		# draw foreground tile layer

		# Draw Debug stuff
		debuglineystart = 2
		currdebugliney = debuglineystart
		blitlist = []
		for line in simstate.debugstuff:
			blitlist.append((font_arial16.render(str(simstate.debugstuff[line]), 0, black), (5, currdebugliney)))
			currdebugliney += 16

		window.blits(blitlist)

		DRAW_DEBUG = False
		if (DRAW_DEBUG):
			# DEBUG: get player screen pos for upcoming debug stuff
			player_screenpos = SpriteBatch.get_screenpos_from_mappos(simstate.entities[0].get_pos(), cam_pos)

			# DEBUG: draw player collision box
			player_coll_dim = (simstate.entities[0].coll_width, simstate.entities[0].coll_height)
			player_coll_dim_2draw = v2_mult(player_coll_dim, TILE_ZOOM)
			player_coll_rect = Rect(
				(player_screenpos[0]-player_coll_dim_2draw[0], player_screenpos[1]-player_coll_dim_2draw[1]+1), 
				v2_mult(player_coll_dim_2draw, 2)
			)
			pygame.draw.rect(window, lightred, player_coll_rect.get_pyrect(), width=3)

			# DEBUG: draw player position dot
			pygame.draw.circle(window, darkred, player_screenpos, 3)

		# Switch buffers
		pygame.display.flip()

	pygame.quit()

if __name__=='__main__':
	main(sys.argv[1:])

