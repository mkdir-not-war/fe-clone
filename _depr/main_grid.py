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
import src.myanim as myanim

# window constants
WIN_WIDTH = 1050
WIN_HEIGHT = 600

# map info and draw constants
TILE_WIDTH = 32
TILE_ZOOM = 2
ZOOMED_WIDTH = TILE_WIDTH * TILE_ZOOM

# camera constants
CAMERA_TILES_WIDE = 16 # even number
CAMERA_TILES_HIGH = 10 # even number
CAMERA_PXOFFSET_FROM_PLAYER = (0, -12)

GAMEMAP_WIDTH = 600

# physics constants
MOVEMENT_CLAMP_DIST2 = 1
#MOVE_ACCEL = 10
MOVE_INIT_ACCEL = 15
MOVE_FRICTION = 12
MOVE_INIT_V = 45
MOVE_COOLDOWN_SEC = 0.2

#PLAYER_FRICTION = 0.1 * PLAYER_MAXSPEED
#PLAYER_ACCEL = 0.03 * PLAYER_MAXSPEED_SQ

# misc constants
NUM_SPRITE_LAYERS = 4
PHYSICS_TIME_STEP = 1.0/100
TILES_PER_ANIMATION = 4

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
font_arial16 = pygame.font.Font("./data/fonts/ARI.ttf", 16)

class InputMoveDir(IntEnum):
	NONE = 0
	RIGHT = 1
	UP_RIGHT = 2
	UP = 3
	UP_LEFT = 4
	LEFT = 5
	DOWN_LEFT = 6
	DOWN = 7
	DOWN_RIGHT = 8

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
		self.tilemap_texture = pygame.image.load(data['tilemap']['filepath'])
		self.tilemap_dim = (
			self.tilemap_texture.get_rect().width // TILE_WIDTH, 
			self.tilemap_texture.get_rect().height // TILE_WIDTH
		)
		
		# load entities
		self.entity64_texture = pygame.image.load(data['entities64']['filepath'])

		# scale everything as necessary
		self.tilemap_texture = pygame.transform.scale_by(self.tilemap_texture, TILE_ZOOM)
		self.entity64_texture = pygame.transform.scale_by(self.entity64_texture, TILE_ZOOM)

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

	def draw_bgtilelayer(self, regionmap, camerabounds, camerapos):

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
				tilemapindex = regionmap.bg_tilelayer[y * regionmap.width + x]
				tile_y = tilemapindex // self.tilemap_dim[0]
				tile_x = tilemapindex - (tile_y * self.tilemap_dim[0])
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
			image = self.entity64_texture # zoom here if we decide the camera can do that
		else:
			pass

		# TODO: zoom here if we decide the camera can do that
		zoomed_width = scale_factor * width

		tile_x, tile_y = entity.curr_animation.sample()

		tilearea = Rect(
			(tile_x * zoomed_width, tile_y * zoomed_width),
			(zoomed_width, zoomed_width)
		)

		map_pos = entity.get_pos()
		#bottom_of_frame = v2_add(map_pos, (0, entity.frame_size))
		screen_pos = SpriteBatch.get_screenpos_from_mappos(map_pos, camerapos)
		drawpos = v2_add(screen_pos, (-zoomed_width/2, -zoomed_width))

		result = (image, Rect(drawpos, (zoomed_width, zoomed_width)).get_pyrect(), tilearea.get_pyrect())
		return result

		return result

class RegionMap:
	def __init__(self):

		self.width = 7
		self.height = 7
		'''
		self.bg_tilelayer = [
			18, 19, 19, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			18, 18, 18, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			19, 19, 20, 20, 18, 19, 18, 19, 19, 18, 19, 18,
			18, 19, 20, 20, 18, 18, 18, 19, 19, 18, 19, 18,
			18, 18, 19, 18, 19, 18, 18, 19, 19, 18, 19, 18,
			19, 19, 18, 18, 19, 18, 18, 19, 19, 18, 19, 18] * 4 # 100% full (width * height)
		'''
		self.bg_tilelayer = [16, 17] * self.width * self.height
		self.bg_tilelayer.pop()

		'''
		self.mid_tilelayer1 = [] # sparse -> (tileindex, x, y)
		self.mid_tilelayer2 = [] # sparse -> (tileindex, x, y)
		self.fg_tilelayer  = [] # sparse -> (tileindex, x, y)
		'''

		self.collisionmap = [0] * self.width * self.height
		'''
		self.collisionmap = [ # 12 x 12
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 
			1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 
			1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 
			1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 
			1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 
			1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 
			1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 
			1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 
			1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 
			1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 
			1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 
			1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1,
			1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1,
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1
		]
		'''

		self.curr_spawn_tile = (3, 3)

	def get_spawnpos(self):
		return (
			self.curr_spawn_tile[0]*TILE_WIDTH + TILE_WIDTH//2,
			self.curr_spawn_tile[1]*TILE_WIDTH + TILE_WIDTH//2
		)

class WorldMap:
	def __init__(self):
		self.curr_region_index = 0
		self.regionmaps = [RegionMap()] * NUM_REGIONS_IN_WORLD

	def regionmap(self):
		return self.regionmaps[self.curr_region_index]

class Entity:
	def __init__(self):
		# basic position
		self.x = 0
		self.y = 0
		self.dp = (0, 0)
		self.ddp = (0, 0)

		self.movemode = EntityMoveModes.STILL
		self.proposed_rel_targettile = (0, 0)
		self.actual_target_position = None
		self.movement_cooldown = 0

		# animation stuff
		self.curr_animation = None
		self.frame_size = 64

		# "collision" stuff
		self.wall2N = False
		self.wall2S = False
		self.wall2E = False
		self.wall2W = False

	def set_pos(self, x, y):
		self.x = x
		self.y = y

	def set_target(self, pos):
		if self.movemode == EntityMoveModes.STILL and self.movement_cooldown <= 0:
			self.proposed_rel_targettile = pos

	def move(self, dir):
		self.x += dir[0]
		self.y += dir[1]

	# position is in pixels, not in tiles
	def get_pos(self):
		return (self.x, self.y)

	def update(self, **kwargs):
		pass

class EntityMoveModes(IntEnum):
	STILL = 0
	MOVING = 1

class Player(Entity):
	def __init__(self):
		super().__init__()
		self.curr_animation = myanim.Animation()
		myanim.load_animation('player', 'idle', self.curr_animation)

	def update(self, **kwargs):
		dt = PHYSICS_TIME_STEP

		if self.movement_cooldown > 0:
			self.movement_cooldown -= dt

		if self.movemode == EntityMoveModes.STILL:
			# if Stationary,
			# if we have a target
			if self.proposed_rel_targettile != (0, 0):
				# TODO: if target isn't a collision_map collider, set the current target to the target
				# set actual target position based on target
				self.actual_target_position = v2_add(self.get_pos(), v2_mult(self.proposed_rel_targettile, TILE_WIDTH))
				
				# finally, switch to moving
				self.movemode = EntityMoveModes.MOVING

				# set initial velocity and zero-out the target proposal
				self.dp = v2_mult(self.proposed_rel_targettile, MOVE_INIT_V)
				self.ddp = v2_mult(v2_sub(self.actual_target_position, (self.x, self.y)), MOVE_INIT_ACCEL)
				self.proposed_rel_targettile = (0, 0)
			pass

		elif self.movemode == EntityMoveModes.MOVING:
			# if Moving
			# TODO: move toward the target
			self.ddp = v2_add(self.ddp, v2_mult(self.ddp, -1 * dt * MOVE_FRICTION))

			# simple motion integral
			self.move(v2_add(v2_mult(self.ddp, 0.5 * dt**2), v2_mult(self.dp, dt))) # change pos before velocity
			self.dp = v2_add(self.dp, v2_mult(self.ddp, dt))

			# if at the target, switch state to Stationary
			if v2_len2(v2_sub((self.x, self.y), self.actual_target_position)) < MOVEMENT_CLAMP_DIST2:
				self.set_pos(*self.actual_target_position)
				self.dp = (0, 0)
				self.ddp = (0, 0)
				self.actual_target_position = None
				self.movemode = EntityMoveModes.STILL
				self.movement_cooldown = MOVE_COOLDOWN_SEC


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
	simstate.entities[0].set_pos(*worldmap.regionmap().get_spawnpos())

	# drawing caches
	drawcache = DrawCache()

	# timing stuff
	t = 0.0
	accum = 0.0

	# debug variables
	current_fps = 0

	while not done:
		frametime = clock.tick(40) # time passed in millisecondss
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

			# update player first?
			simstate.entities[0].update()

			# update all of the entities
			for entity in simstate.entities:
				entity.update()

			# TODO: how is movement affected when two entities move to the same tile?
			# do they bounce off eachother? Is it first-come, first-serve?

			# check collision with hurt/hit boxes and other entities
			#for entity in simstate.entities:
				#do_collision(worldmap.regionmap(), entity)


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

		# draw background tile layers
		drawcache.bgtilecache = spritebatch.draw_bgtilelayer(regionmap, cam_bounds, cam_pos)
		window.blits(drawcache.bgtilecache)

		# DEBUG: draw rects where there are collision in the collision map
		'''
		collisionrectdim = (COLTILE_WIDTH * TILE_ZOOM + 1, COLTILE_WIDTH * TILE_ZOOM + 1)
		for y in range(regionmap.height * 2):
			for x in range(regionmap.width * 2):
				if (regionmap.collisionmap[x + y * (regionmap.width * 2)] == 0):
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

		DRAW_DEBUG = True
		if (DRAW_DEBUG):
			# DEBUG: get player screen pog for upcoming debug stuff
			player_screenpos = SpriteBatch.get_screenpos_from_mappos(simstate.entities[0].get_pos(), cam_pos)

			'''
			# DEBUG: draw player collision box
			player_coll_dim = (simstate.entities[0].coll_width, simstate.entities[0].coll_height)
			player_coll_dim_2draw = v2_mult(player_coll_dim, TILE_ZOOM)
			player_coll_rect = Rect(
				(player_screenpos[0]-player_coll_dim_2draw[0], player_screenpos[1]-player_coll_dim_2draw[1]+1), 
				v2_mult(player_coll_dim_2draw, 2)
			)
			pygame.draw.rect(window, lightred, player_coll_rect.get_pyrect(), width=3)
			'''

			# DEBUG: draw player position dot
			pygame.draw.circle(window, darkred, player_screenpos, 3)

		# Switch buffers
		pygame.display.flip()

	pygame.quit()

if __name__=='__main__':
	main(sys.argv[1:])

