import os

'''
I don't actually know what these do exactly, so I'm commenting them out for now.
TODO: look them up to get a better understanding.

# Maybe people want to keep watching the joystick feedback even when this
# window doesn't have focus. Possibly by capturing this window into OBS.
#os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

# A tiny performance/latency hit isn't a problem here. Instead, it's more
# important to keep the desktop compositing effects running fine. Disabling
# compositing is known to cause issues on KDE/KWin/Plasma/X11 on Linux.
#os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"
'''

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
from src.mapgen import *

# window constants (16:9)
TILE_ZOOM = 1 # eventually go 2 here
WIN_WIDTH = 960 * TILE_ZOOM
WIN_HEIGHT = 540 * TILE_ZOOM

# map info and draw constants
ZOOMED_WIDTH = TILE_WIDTH * TILE_ZOOM
TILEMAP_WIDTH_IN_TILES = 8
TILEMAP_FRAMES_PER_ANIMATION = 16

# gamemap constants
GAMEMAP_SCREEN_Y = (WIN_HEIGHT - GAMEMAP_TILES_HIGH * TILE_WIDTH * TILE_ZOOM) // 2
GAMEMAP_SCREEN_X = WIN_WIDTH - GAMEMAP_TILES_WIDE * TILE_WIDTH * TILE_ZOOM - GAMEMAP_SCREEN_Y

# physics constants
PLAYER_MAXSPEED = 18.0 * TILE_WIDTH
PLAYER_MINSPEED_SQ = 1.0
PLAYER_MAXSPEED_SQ = PLAYER_MAXSPEED**2

PLAYER_FRICTION = 0.1 * PLAYER_MAXSPEED
PLAYER_ACCEL = 0.03 * PLAYER_MAXSPEED_SQ
PLAYER_FOLLOWINGDIST = TILE_WIDTH * 1.2
PLAYER_FOLLOWINGEPSILON	 = TILE_WIDTH * 0.15

# misc constants
FRAMERATE_LOCK = 144
PHYSICS_TIME_STEP = 1.0/100

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

######## ENUMS #################

class GameInputMode(IntEnum):
	MENUMODE		= 0
	FREEMODE		= 1
	COMBATPLAYER	= 2
	COMBATENEMY		= 3

######## END ENUMS #############

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
		self.anim_finished = False
		self.frame_size = 64
		self.flipanimhorz = False
		self.facing_direction = None

		# collision stuff
		# width and height are half the length of the rectangle -- position is in the center of the rect
		self.coll_width = self.frame_size//2 # since we only have width and height, 
		self.coll_height = self.frame_size//2 # entity collision shapes are only rectangles?

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

	def update(self, kwargs):
		pass

class Entity_MapExit(Entity):
	def __init__(self, exitdirection):
		super().__init__()
		self.curr_animation = myanim.Animation()
		
		if (exitdirection == ExitDirection.NORTH or exitdirection == ExitDirection.BUILDING):
			myanim.load_animation(self.curr_animation, 'exit', 'north')
		elif (exitdirection == ExitDirection.SOUTH):
			myanim.load_animation(self.curr_animation, 'exit', 'south')
		elif (exitdirection == ExitDirection.EAST):
			myanim.load_animation(self.curr_animation, 'exit', 'east-west')
		elif (exitdirection == ExitDirection.WEST):
			myanim.load_animation(self.curr_animation, 'exit', 'east-west')
			self.flipanimhorz = True

def check_exit_events(mapgen, activeplayer):
	pass

class PlayerAnimState(IntEnum):
	IDLE = 0
	WALK = 1

# NOTE: player does not have player-specific variables -- everything goes in entity
# player is really just an Init function and an Update function. That's it.
# Still useful to inherit Entity because we can use the Update function polymorphed
class Entity_Player(Entity):
	def __init__(self):
		super().__init__()
		self.curr_animation = myanim.Animation()
		myanim.load_animation(self.curr_animation, 'player', 'idle-side')

		self.facing_direction = InputMoveDir.RIGHT
		self.input_ddp = (0, 0)
		self.animstate = PlayerAnimState.IDLE

	def update(self, kwargs):
		dt = PHYSICS_TIME_STEP

		# set input_ddp if this is the following player
		followingdist2 = None
		vec2player = None
		if 'leader_pos' in kwargs:
			playerpos = kwargs['leader_pos']
			vec2player = v2_sub(playerpos, (self.x, self.y))
			target = v2_add(
				v2_mult(v2_normalize(v2_sub((self.x, self.y), playerpos)), PLAYER_FOLLOWINGDIST), 
				playerpos
			)
			nearesttarget = target # TODO: use A* here to get actual target and movevec
			movevec = v2_sub(nearesttarget, (self.x, self.y)) 
			followingdist2 = v2_len2(movevec)
			if (followingdist2 < PLAYER_FOLLOWINGEPSILON**2):
				movevec = (0, 0)
			else:
				movevec = v2_mult(v2_normalize(movevec), 0.98)
			self.input_ddp = movevec


		# ddp starts as exactly equal to input direction (<= 1.0 length)
		self.ddp = v2_mult(self.input_ddp, PLAYER_ACCEL)

		# add friction force
		self.ddp = v2_sub(self.ddp, v2_mult(self.dp, PLAYER_FRICTION))

		# simple motion integral
		self.move(v2_add(v2_mult(self.ddp, 0.5 * dt**2), v2_mult(self.dp, dt))) # change pos before velocity
		self.dp = v2_add(self.dp, v2_mult(self.ddp, dt))

		# change facing direction based on movement (or face the player if following)
		if followingdist2 == None:
			self.facing_direction = v2_to_facingdirection(self.facing_direction, self.input_ddp)
		else:
			self.facing_direction = v2_to_facingdirection(self.facing_direction, vec2player)

		# change animation
		if self.input_ddp == (0, 0):
			if followingdist2 == None or self.anim_finished:
				self.change_animation(PlayerAnimState.IDLE)
		else:
			self.change_animation(PlayerAnimState.WALK)

		# flip animation if facing left	
		if (self.facing_direction == InputMoveDir.LEFT):
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

# just face left or right, no need for other directions
def v2_to_facingdirection(currdirection, v2):
	result = currdirection
	if v2 != (0, 0):
		dpx, dpy = v2
		# discrete thumbstick/keyboard directions
		if dpx > 0:
			result = InputMoveDir.RIGHT
		elif dpx < 0:
			result = InputMoveDir.LEFT
		else: # no x-direction, default facing right
			result = InputMoveDir.RIGHT
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
		# two player characters, at indices 0 and 1.
		self.entities.append(Entity_Player())
		self.entities.append(Entity_Player())
		self.activeplayer = 0
		self.followingplayer = 1

		self.entities[0].coll_width = self.entities[1].coll_width = TILE_WIDTH * 0.4 # half width of collision rect
		self.entities[0].coll_height = self.entities[1].coll_height = TILE_WIDTH * 0.2 # half height of collision rect

		# five exits, at indices 2, 3, 4, 5, 6
		self.exitindex = 2
		for i in range(1):#ExitDirection.TOTAL):
			self.entities.append(Entity_MapExit(ExitDirection.NORTH))

	def animate(self):
		for entity in self.entities:
			if entity.curr_animation:
				entity.anim_finished = entity.curr_animation.stepfunc()

	def swap_active_player(self):
		self.activeplayer = self.activeplayer * -1 + 1
		self.followingplayer = self.followingplayer * -1 + 1
		assert(self.activeplayer != self.followingplayer)

	def get_active_player(self):
		return self.entities[self.activeplayer]

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
	mapgen = MapGenerator()
	mapgen.run()
	mapgen.load_regionmaps_fromindex() # default: Region 0 Map 0

	# set player spawn
	spawntiles = mapgen.get_currmap().get_spawntiles(ExitDirection.SOUTH)
	simstate.entities[0].spawn(*get_tilepos_center(spawntiles[0], percenty=0.75))
	simstate.entities[1].spawn(*get_tilepos_center(spawntiles[1], percenty=0.75))
	
	# spawn exit entities
	simstate.entities[2].spawn(*get_tilepos_center(EXIT_TILES[ExitDirection.NORTH]))

	# drawing caches
	drawcache = DrawCache()

	# timing stuff
	t = 0.0
	accum = 0.0

	# debug variables
	current_fps = 0

	while not done:
		frametime = clock.tick(FRAMERATE_LOCK) # time passed in milliseconds (frame rate in parens)
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
			for i in range(len(simstate.entities)):
				kwargs = {}
				if (i == simstate.followingplayer):
					kwargs['leader_pos'] = simstate.get_active_player().get_pos()
				simstate.entities[i].update(kwargs)

			# bound player entities by collision
			do_collision(mapgen.get_currmap(), simstate.entities[simstate.activeplayer])
			do_collision(mapgen.get_currmap(), simstate.entities[simstate.followingplayer])

			check_exit_events(mapgen, simstate.entities[simstate.activeplayer])

			# update animation step (not tied to frame rate!)
			simstate.animate()

		################################################################################
		# DRAW! ########################################################################
		################################################################################

		# Start drawing
		window.fill(neutralgrey) # TODO: change this to off-black??

		# draw background tile layers, cache if helpful
		if (not drawcache.bgtilecache):
			drawcache.bgtilecache = spritebatch.draw_tilelayer(mapgen.get_currmap(), TileLayer.BG)
		window.blits(drawcache.bgtilecache)

		# TODO: draw overlay grid here, underneath the middleground but over the background

		# draw middleground tile layers, no need to cache since sparse
		mgtiles = spritebatch.draw_tilelayer(mapgen.get_currmap(), TileLayer.MG)
		window.blits(mgtiles)

		# draw entities in order of y position
		blitlist = []
		entityids_by_y = list(range(len(simstate.entities)))
		entityids_by_y.sort(key=lambda e: simstate.entities[e].y)
		for eid in entityids_by_y:
			if (simstate.entities[eid].curr_animation):
				blitlist.append(spritebatch.draw_entity(simstate.entities[eid]))
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
			player_screenpos = SpriteBatch.get_screenpos_from_mappos(simstate.entities[0].get_pos())

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

