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

from src.mymath import *
from src.myinput import *
from src.collision import *
from src.constants import *
import src.myanim as myanim
from src.mapgen import *
from src.entities import *
from src.spritebatch import *
from src.mymenu import *

######## ENUMS #################

class GameContext(IntEnum):
	IN_MENU			= 0
	FREE_MOVE		= 1
	COMBAT_CHOOSE	= 2
	COMBAT_PLAYER	= 3
	COMBAT_ENEMY	= 4

######## END ENUMS #############

def check_exit_events(mapgen, simstate):
	playercolrect = simstate.entities[simstate.activeplayer].get_collrect()
	exitingdir = None
	for i in range(ExitDirection.TOTAL):
		if simstate.entities[simstate.exits_startindex+i].active:
			tilebox = get_exittilebox(i)
			if playercolrect.collides_rect(tilebox):
				exitingdir = i
				break

	if exitingdir != None:
		oldmapindex = mapgen.curr_mapindex
		exits2activate = mapgen.load_adjacentregionmap(exitingdir)

		allnewexits = mapgen.allmaps[mapgen.curr_mapindex].exits
		entrancedir = None
		for i in range(ExitDirection.TOTAL):
			simstate.entities[simstate.exits_startindex+i].active = exits2activate[i]
			if allnewexits[i] == oldmapindex:
				entrancedir = i

		if mapgen.map_combatcompleted[mapgen.curr_mapindex]:
			spawn_players(simstate, mapgen, entrancedir)
		else:
			# entering a map with combat, switch context to combat!
			simstate.begin_combat()

def spawn_players(simstate, mapgen, entrancedir):
	spawntiles = mapgen.get_currmap().get_spawntiles(entrancedir)
	simstate.entities[0].spawn(*get_tilepos_center(spawntiles[0], percenty=0.75))
	simstate.entities[1].spawn(*get_tilepos_center(spawntiles[1], percenty=0.75))

# class to hold essentially global vars
class SimulationState:
	def __init__(self):
		# animated tile stuff
		self.animation_step = 0 # always under MAX_ANIM_FRAMES

		# input stuff
		self.joystick = JoystickHandler(0)
		self.inputdata = InputDataBuffer()
		self.curr_gamecontext = None
		self.buttonholdtimer = 0.0

		# debug stuff
		self.debugstuff = {}

		# players, actors, obstacles. Anything that needs to be physically updated
		self.entities = []
		# two player characters, at indices 0 and 1.
		self.entities.append(Entity_Player())
		self.entities.append(Entity_Player())
		self.activeplayer = 0
		self.followingplayer = 1

		# five exits, at entity-indices 2, 3, 4, 5, 6
		self.exits_startindex = 2
		for i in range(ExitDirection.TOTAL):
			self.entities.append(Entity_MapExit(i))

		self.mostrecent_entrance = ExitDirection.SOUTH

		# combat stuff
		self.combathandler = CombatHandler()
		self.combathandler.setup()

	def animate(self):
		for entity in self.entities:
			if entity.active and entity.curr_animation:
				entity.anim_finished = entity.curr_animation.stepfunc()

	def swap_active_player(self):
		self.activeplayer = self.activeplayer * -1 + 1
		self.followingplayer = self.followingplayer * -1 + 1

	def begin_combat(self):
		#simstate.curr_gamecontext = GameContext.COMBAT_CHOOSE
		simstate.curr_gamecontext = GameContext.COMBAT_PLAYER

		# TODO: probably start combat music, maybe check for dialogue events, etc.

	def combat_choose_action(self, selectiondir):
		if (selectiondir == InputMoveDir.DOWN):
			self.combathandler.selectedactionindex = CombatActionIndex.DEFEND
		elif (selectiondir == InputMoveDir.UP):
			pass
		elif (selectiondir == InputMoveDir.RIGHT_DOWN):
			pass
		elif (selectiondir == InputMoveDir.LEFT_DOWN):
			pass
		elif (selectiondir == InputMoveDir.RIGHT_UP):
			pass
		elif (selectiondir == InputMoveDir.LEFT_UP):
			pass

###################################### Combat stuff #################

class CombatTileFlag(IntEnum):
	WALKABLE 		= 0
	BLOCKED 		= 1
	BLOCKED_BURNING	= 2
	ENTITY 			= 3

class CombatTile:
	def __init__(self):
		self.flag = CombatTileFlag.WALKABLE
		self.index = -1 # index into combathandler.combatentities if tile has entity

class CombatHandler:
	def __init__(self):
		self.combattiles = []
		self.combatentities = []

		# player turn vars
		self.selectedactionindex = -1
		self.entity_actionindicator = None # just using x, y and facingdirection
		self.indicator_startpos = (0, 0)
		self.overlappingplayer = True

		# enemy turn vars
		# self.enemies_megabrain = None ## I think we skip a Brain class and just do the AI in CombatHandler

	def get_tile(self, x, y):
		return self.combattiles[x + y * GAMEMAP_TILES_WIDE]

	def reset_indicator(self, player_entityindex):
		# default attack direciton opposite entrance direction
		self.entity_actionindicator.facingdirection = get_oppdirection(self.mostrecent_entrance)

		# default attack tile position to player character tile position
		self.indicator_startpos = self.combatentities[player_entityindex].get_pos()
		self.entity_actionindicator.spawn(*self.indicator_startpos)

	def move_indicator(self, movedir):
		newpos = v2_add(movedir, self.entity_actionindicator.get_pos())
		testtile = self.get_tile(*newpos)
		# can attack/move from any walkable tile or from original tile (i.e. don't move)
		if testtile.flag == CombatTileFlag.WALKABLE or newpos == self.indicator_startpos:
			self.entity_actionindicator.move(movedir)

	def turn_indicator(self):
		indicatordir = self.entity_actionindicator.facingdirection

	def setup(self):
		for i in range(GAMEMAP_SIZE):
			self.combattiles.append(CombatTile())

		for i in range(2 + MAX_COMBAT_ENEMIES):
			self.combatentities.append(CombatEntity())

		self.indicator_pos = Entity()

	def reset(self, simstate, mapgen):
		regionmap = mapgen.get_currmap()

		# first, reset combat tiles to collisionmap
		for i in range(GAMEMAP_SIZE):
			self.combattiles[i].index = -1
			if regionmap.collisionmap[i] > 0:
				if regionmap.burningmap[i] > 0:
					self.commbattiles[i].flag = CombatTileFlag.BLOCKED_BURNING
				else:
					self.commbattiles[i].flag = CombatTileFlag.BLOCKED
			else:
				self.commbattiles[i].flag = CombatTileFlag.WALKABLE

		# setup and place player characters
		self.combatentities[0].entityindex = simstate.activeplayer
		self.combatentities[1].entityindex = simstate.followingplayer

		spawntiles = regionmap.get_spawntiles(entrancedir)

############ End Combat stuff #########################################

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
	# Menu, MoveAround, CombatChoose, CombatPlayer, CombatEnemy
	inputhandlers = [None, IH_MovingAround(), IH_CombatChoose(), IH_CombatPlayer(), None]

	# editor state
	simstate = SimulationState()
	simstate.curr_gamecontext = GameContext.FREE_MOVE

	mapgen = MapGenerator()
	mapgen.run()

	menuhandler = MenuHandler()
	menuhandler.load()

	exits2activate = mapgen.load_regionmaps_fromindex() # default: Region 0 Map 0
	for i in range(ExitDirection.TOTAL):
		simstate.entities[simstate.exits_startindex+i].active = exits2activate[i]
		simstate.entities[simstate.exits_startindex+i].spawn(*get_tilepos_center(EXIT_TILES[i]))

	# set player spawn (default south entrance)
	spawn_players(simstate, mapgen, ExitDirection.SOUTH)

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

			# handle input
			simstate.inputdata.newinput(simstate.joystick)
			inputhandlers[simstate.curr_gamecontext].handle_input(simstate)

			# update menu elements (if activated by input)
			menuhandler.update(simstate, mapgen)

			################################################################################
			# UPDATE #######################################################################
			################################################################################

			# update all of the entities
			for i in range(len(simstate.entities)):
				kwargs = {}
				if (i == simstate.followingplayer):
					kwargs['leader_pos'] = simstate.entities[simstate.activeplayer].get_pos()
				simstate.entities[i].update(kwargs)

			# bound player entities by collision
			do_collision(mapgen.get_currmap(), simstate.entities[simstate.activeplayer])
			do_collision(mapgen.get_currmap(), simstate.entities[simstate.followingplayer])

			check_exit_events(mapgen, simstate)

			# update animation step (not tied to frame rate!)
			simstate.animate()

		################################################################################
		# DRAW! ########################################################################
		################################################################################

		# Start drawing
		window.fill(COLORS['neutralgrey']) # TODO: change this to off-black??

		## Draw Game Map ##########################
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
			if (simstate.entities[eid].active and simstate.entities[eid].curr_animation):
				blitlist.append(spritebatch.draw_entity(simstate.entities[eid]))
		window.blits(blitlist)

		# draw foreground tile layer

		## End Draw Game Map #######################

		## Draw UI ################################
		blitlist = []
		blitlist.extend(spritebatch.draw_ui_overlay())
		blitlist.extend(spritebatch.draw_menuscene(menuhandler))
		window.blits(blitlist)

		## End Draw UI ############################

		################## Draw Debug stuff ####################################################
		debuglineystart = 2
		currdebugliney = debuglineystart
		blitlist = []
		for line in simstate.debugstuff:
			blitlist.append((
				font_depixel16.render(str(simstate.debugstuff[line]), 0, COLORS['bone']), 
				(5, currdebugliney)
			))
			currdebugliney += 16

		window.blits(blitlist)

		DRAW_DEBUG = False
		if (DRAW_DEBUG):
			# DEBUG: get player screen pos for upcoming debug stuff
			player_screenpos = SpriteBatch.get_screenpos_from_mappos(simstate.entities[0].get_pos())

			# DEBUG: draw player collision box
			player_coll_rect = simstate.entities[simstate.activeplayer].get_collrect()
			player_coll_rect = player_coll_rect.move((GAMEMAP_SCREEN_X, GAMEMAP_SCREEN_Y))
			pygame.draw.rect(window, lightred, player_coll_rect.get_pyrect(), width=3)

			# DEBUG: draw player position dot
			pygame.draw.circle(window, darkred, player_screenpos, 3)

		## End Debug ###########################################################################

		# Switch buffers
		pygame.display.flip()

	pygame.quit()

if __name__=='__main__':
	main(sys.argv[1:])

