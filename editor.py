import pygame
from math import sqrt
from enum import IntEnum
from tkinter import Tk 
import sys
import json

from src.getmath import *

# constants
WIN_WIDTH = 1200
WIN_HEIGHT = 600

# no zoom, adds too much complexity

TILE_WIDTH = 32

# window constants
GAMEMAP_WIDTH = 700
COLLISIONSET_ZOOM = 2.0

TILEPICKER_PXBUFFER = 5
TILEPICKER_WIDTH_IN_TILES = 8
TILEPICKER_NUM_ANIMATED_ROWS = 2
TILEPICKER_WIDTH = (TILEPICKER_WIDTH_IN_TILES * TILE_WIDTH + TILEPICKER_PXBUFFER*2)//10 * 10 + TILEPICKER_PXBUFFER*2

MENU_WIDTH = (WIN_WIDTH - GAMEMAP_WIDTH - TILEPICKER_WIDTH)

SUBSCREEN_RECTS = {
	'menu' : Rect((0, 0), (MENU_WIDTH, WIN_HEIGHT)),
	'game map' : Rect((MENU_WIDTH, 0), (GAMEMAP_WIDTH, WIN_HEIGHT)),
	'tile picker' : Rect(
		(MENU_WIDTH + GAMEMAP_WIDTH, 0), 
		(TILEPICKER_WIDTH, WIN_HEIGHT)
	)
}

# drawing constants
NUM_SPRITE_LAYERS = 4
FPS = 60
FRAMES_PER_ANIMATION = 16
TILES_PER_ANIMATION = 4

# game map tile dimensions
MAP_GRID_WIDTH 		= 13 # only used in combat, not really in editor?
MAP_GRID_HEIGHT 	= 13 # only used in combat, not really in editor?
MAP_HORZBORDER		= 3
MAP_VERTBORDER		= 2
MAP_WIDTH			= MAP_GRID_WIDTH + MAP_HORZBORDER*2
MAP_HEIGHT 			= MAP_GRID_HEIGHT + MAP_VERTBORDER*2

# input codes
class InputCodes(IntEnum):
	MOUSE_LEFT = 1
	MOUSE_MID = 2
	MOUSE_RIGHT = 3
	MOUSE_SCROLLUP = 4
	MOUSE_SCROLLDOWN = 5

# colors
neutralgrey = pygame.Color(150, 150, 160)
darkgrey = pygame.Color(50, 50, 65)
darkred = pygame.Color(80, 0, 0)
lightred = pygame.Color(250, 100, 100)
lightblue = pygame.Color(100, 100, 250)
black = pygame.Color('black')
white = pygame.Color('white')

pygame.font.init()
font_arial = pygame.font.Font("./data/fonts/ARI.ttf", 16)

class TileLayer(IntEnum):
	BG 		= 0
	MG1 	= 1
	MG2 	= 2
	FG 		= 3

class MapData:
	def __init__(self):
		self.filename = ''
		self.tile_layers = [[]] * 4

		# full WIDTH * HEIGHT arrays of indices
		self.tile_layers[TileLayer.BG] = []
		self.tile_layers[TileLayer.MG1] = []

		# arrays of tuples (x, y, index)
		self.tile_layers[TileLayer.MG2] = []
		self.tile_layers[TileLayer.FG] = []

	def get_spriteindex(self, layer, x, y):
		result = -1
		if (x >= MAP_WIDTH or x < 0 or
			y >= MAP_HEIGHT or y < 0):
			result = -1
		else:
			result = self.spriteindex[(layer * MAP_WIDTH * MAP_HEIGHT) + x + MAP_WIDTH * y]
		return result

	def load(self, mapname):
		self.filename = './data/maps/%s.dat' % mapname

		fin = open(self.filename, 'r')

		loadphase = 0

		for line in fin:
			# phase 1, load size params
			if loadphase == 0:
				pass

		self.spriteindex = [-1] * (NUM_SPRITE_LAYERS * MAP_HEIGHT * MAP_WIDTH)
		self.collisionindex = [0] * len(self.spriteindex) * 4 # each tile has 4 quadrants of collision

		fin.close()

	def save(self):
		pass


# one spritebatch for animated sprites, one for not (i.e. geometry)
class SpriteBatch:
	def __init__(self):
		self.length = 0

		self.sprites = []

		fin = open('./data/graphics/texture-data.json')
		self.scenespritedata = json.load(fin)
		fin.close()

		self.tilemap_sprite = pygame.image.load(self.scenespritedata['tilemap']['filepath']).convert_alpha()
		self.tilemap_dim = (
			self.tilemap_sprite.get_rect().width // TILE_WIDTH, 
			self.tilemap_sprite.get_rect().height // TILE_WIDTH
			)

	def draw_tilepicker(self, editorstate):

		tilepickerimg, tilepickerarea, tilepickerdest = None, None, None

		scale = (
			self.tilemap_sprite.get_rect().width, 
			self.tilemap_sprite.get_rect().height
		)
		tilepickerimg = pygame.transform.scale(self.tilemap_sprite, scale)

		## Draw animated tiles animating
		result = []

		# TODO: skip drawing animated tiles that aren't in frame (check scrolling)
		for row in range(TILEPICKER_NUM_ANIMATED_ROWS):
			for col_index in [0, 1]: 
				column = col_index * TILES_PER_ANIMATION

				tilepickerarea = Rect(
					((column + editorstate.animation_step) * TILE_WIDTH, row * TILE_WIDTH),
					(TILE_WIDTH, TILE_WIDTH)
				)

				tilepickerdest = Rect(
					(TILEPICKER_PXBUFFER + col_index * TILE_WIDTH * 4, 
						TILEPICKER_PXBUFFER + row * TILE_WIDTH), 
					(TILE_WIDTH, TILE_WIDTH)
				)

				result.append((tilepickerimg, tilepickerdest.get_pyrect(), tilepickerarea.get_pyrect()))

		## Draw static tiles
		tilepickerarea = Rect(
			(0, max(TILEPICKER_NUM_ANIMATED_ROWS * TILE_WIDTH, 
			editorstate.tilepickerscrolly - (WIN_HEIGHT // 2))),
			(TILE_WIDTH * TILEPICKER_WIDTH_IN_TILES, 
			WIN_HEIGHT - TILEPICKER_PXBUFFER*2)
		)

		# TODO: incorporate scrolling
		tilepickerdest = Rect(
			(0, TILEPICKER_NUM_ANIMATED_ROWS * TILE_WIDTH), 
			(tilepickerarea.width, tilepickerarea.height)
		)
		tilepickerdest.x += TILEPICKER_PXBUFFER
		tilepickerdest.y += TILEPICKER_PXBUFFER

		result.append((tilepickerimg, tilepickerdest.get_pyrect(), tilepickerarea.get_pyrect()))

		return result

	def draw_tilelayer(self, mapdata, tilelayer):

		min_x_tile, max_x_tile, min_y_tile, max_y_tile = (0, MAP_WIDTH, 0, MAP_HEIGHT)

		# scale image to the rect
		scale_factor = 1 # * camera.zoom
		scaled_width = ZOOMED_WIDTH
		image = self.tilemap_texture

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


def get_rect_and_inner(rect, outercolor, innercolor, subscreen):
	result = []
	# highlight it (add <rect, color, window> to list, draw later)
	result.append((rect, outercolor, subscreen))
	# also highlight an inner square as white, so it's visible on dark tiles
	innerrect = rect.copy()
	innerrect.move((1, 1))
	innerrect.width -= 2
	innerrect.height -= 2
	result.append((innerrect, innercolor, subscreen))
	return result

## MOUSE ACTION FUNCTIONS -> return Rect to highlight ###########################
def do_menu(editorstate):
	result = None

	result = Rect((0, 0), (10, 10)) #debug
	return result

def do_gamemap(editorstate):
	result = None

	result = Rect((0, 0), (10, 10)) #debug
	return result

def do_tilepicker(editorstate):
	result = None

	tileposx = (editorstate.subsurf_mousepos[0] - \
		TILEPICKER_PXBUFFER) // TILE_WIDTH
	tileposy = ((editorstate.subsurf_mousepos[1] - \
		TILEPICKER_PXBUFFER + editorstate.tilepickerscrolly) // TILE_WIDTH)

	result = Rect(
		(tileposx * TILE_WIDTH + TILEPICKER_PXBUFFER, tileposy * TILE_WIDTH + TILEPICKER_PXBUFFER), 
		(TILE_WIDTH, TILE_WIDTH)
	)

	# filter out tiles out of range and not over boxes
	if not (tileposy >= 0 and tileposy < WIN_HEIGHT // TILE_WIDTH and
			tileposx >= 0 and tileposx < TILEPICKER_WIDTH_IN_TILES and
			# if inside animated range, only highlight columns 0 and 4
			(tileposy >= TILEPICKER_NUM_ANIMATED_ROWS or 
				(tileposx == 0 or tileposx == 4)
			)):

		result = None

	# click left mouse button -> select tile to paint
	if (result != None and
		InputCodes.MOUSE_LEFT in editorstate.prev_input and 
		not InputCodes.MOUSE_LEFT in editorstate.curr_input):

		editorstate.tileindex2paint = TILEPICKER_WIDTH_IN_TILES * tileposy + tileposx
		editorstate.selectedtilerect = result
		print('tile index set: %d' % editorstate.tileindex2paint)
		
		
	# update selected tile rect position
	if editorstate.selectedtilerect != None:
		selectedtilex = editorstate.tileindex2paint % TILEPICKER_WIDTH_IN_TILES
		selectedtiley = editorstate.tileindex2paint // TILEPICKER_WIDTH_IN_TILES
		editorstate.selectedtilerect = Rect(
			(selectedtilex * TILE_WIDTH + TILEPICKER_PXBUFFER, 
			selectedtiley * TILE_WIDTH + TILEPICKER_PXBUFFER), 
			(TILE_WIDTH, TILE_WIDTH)
		)

	return result
## End MOUSE ACTION FUNCTIONS

	
# class to hold essentially global vars
class EditorState:
	def __init__(self):
		# animated tile stuff
		self.counter = 0
		self.animation_step = 0

		# input stuff
		self.prev_input = []
		self.curr_input = [] # int list
		self.subsurf_mousepos = None

		# tilepicker stuff
		self.tileindex2paint = None
		self.selectedtilerect = None
		self.tilepickerscrolly = 0

		# gamemap stuff
		self.gamemap = None

	def animate(self):
		self.counter += 1
		if (self.counter >= FRAMES_PER_ANIMATION):
			self.animation_step += 1
			self.counter = 0
		if (self.animation_step >= 4):
			self.animation_step = 0

def main(argv):
	if (len(sys.argv) != 2):
		print('wrong number of command line args. Received %d, expected %d' % (len(sys.argv), 2))
		quit()

	pygame.init()
	Tk().withdraw()

	# Set the width and height of the screen (width, height).
	screendim = (WIN_WIDTH, WIN_HEIGHT)
	window = pygame.display.set_mode(screendim)#, flags=pygame.SRCALPHA)
	pygame.display.set_caption("topdown editor")

	done = False
	clock = pygame.time.Clock()

	# set up fonts
	font = pygame.font.Font('./data/fonts/ARI.ttf', 20)

	# set up window Surfaces
	subscreen_menu = window.subsurface(SUBSCREEN_RECTS['menu'].get_pyrect())
	subscreen_gamemap = window.subsurface(SUBSCREEN_RECTS['game map'].get_pyrect())
	subscreen_tilepicker = window.subsurface(SUBSCREEN_RECTS['tile picker'].get_pyrect())

	# cache structure for all sprite flyweights
	spritebatch = SpriteBatch()

	# editor state
	editorstate = EditorState()

	# setup gamemap
	editorstate.gamemap = MapData()
	editorstate.gamemap.load(sys.argv[1])

	while not done:
		clock.tick(FPS)
		editorstate.animate()

		highlighted_rects_to_draw = []

		################################################################################
		# INPUT ########################################################################
		################################################################################

		# copy curr input to previous input
		editorstate.prev_input = editorstate.curr_input[:]

		# remove mouse scroll inputs from current input
		editorstate.curr_input = [x for x in editorstate.curr_input if x != 4 and x != 5]

		for event in pygame.event.get(): # User did something.

			# quit early
			if event.type == pygame.QUIT: # If user clicked close.
				done = True # Flag that we are done so we exit this loop.
				break
			elif event.type == pygame.KEYDOWN: # use for Esc to close, at least
				if event.key == pygame.K_ESCAPE:
					done = True
					break

			# mouse inputs
			elif event.type == pygame.MOUSEBUTTONDOWN:
				editorstate.curr_input.append(event.button) # event.button
			elif event.type == pygame.MOUSEWHEEL:
				editorstate.curr_input.append(4 if event.y == 1 else 5) # event.y = 1 or -1
			elif event.type == pygame.MOUSEBUTTONUP:
				# same quesiton as keyup
				if event.button in editorstate.curr_input:
					editorstate.curr_input.remove(event.button)

		# mouse position
		screenmousepos = pygame.mouse.get_pos()

		# get surface mouse is on
		mouse_subscreen = None
		for subscreen_rect in SUBSCREEN_RECTS:
			if SUBSCREEN_RECTS[subscreen_rect].contains_point(screenmousepos):
				mouse_subscreen = subscreen_rect
				break

		editorstate.subsurf_mousepos = None

		if (screenmousepos != None and SUBSCREEN_RECTS[subscreen_rect] != None):
			editorstate.subsurf_mousepos = v2_sub(screenmousepos, SUBSCREEN_RECTS[subscreen_rect].get_topleft())

			# get mouse-able rect from surface
			mouse_rect = None
			if mouse_subscreen == None:
				mouse_rect = None
			elif mouse_subscreen == 'menu':
				mouse_rect = do_menu(editorstate)
			elif mouse_subscreen == 'game map':
				mouse_rect = do_gamemap(editorstate)
			elif mouse_subscreen == 'tile picker':
				mouse_rect = do_tilepicker(editorstate)

				# if mouse in tile picker and scrolling, scroll the tile picker
				if InputCodes.MOUSE_SCROLLUP in editorstate.curr_input:
					pass
				elif InputCodes.MOUSE_SCROLLDOWN in editorstate.curr_input:
					pass

			# if mouse rect, 
			if mouse_rect != None:
				# highlight it (add <rect, color, window> to list, draw later)
				# and also highlight an inner square as white, so it's visible on dark tiles
				highlighted_rects_to_draw.extend(
					get_rect_and_inner(mouse_rect, black, white, mouse_subscreen)
				)

		################################################################################
		# DRAW! ########################################################################
		################################################################################

		# Start drawing
		window.fill(neutralgrey) # TODO: change this to off-black??

		## Draw Menu Options ###########################################################

		# TODO: draw currently selected tile (animated if relevant)

		pygame.draw.rect(subscreen_menu, darkred, subscreen_menu.get_rect(), 2)
		## End Draw Menu Options


		## Draw Tile Picker Surface ####################################################
		tilepickerimgs = spritebatch.draw_tilepicker(editorstate)
		subscreen_tilepicker.blits(tilepickerimgs)

		pygame.draw.rect(subscreen_tilepicker, darkred, subscreen_tilepicker.get_rect(), 3)
		
		# highlight selected tile to paint
		if editorstate.selectedtilerect != None:
			selectedtilerects = get_rect_and_inner(
				editorstate.selectedtilerect, None, None, None
			)
			'''
			# TODO: alpha doesn't work? Maybe make another overlaid subsurface to draw alpha stuff to?
			subscreen_tilepicker.fill(
				pygame.Color(100, 100, 250, a=128), rect=selectedtilerects[0][0].get_pyrect()
			)
			'''
			pygame.draw.rect(
				subscreen_tilepicker, lightblue, selectedtilerects[0][0].get_pyrect(), 1
			)
			pygame.draw.rect(
				subscreen_tilepicker, white, selectedtilerects[1][0].get_pyrect(), 1
			)

		## End Draw Tile Picker Surface

		
		## Draw Map Surface ############################################################
		subscreen_gamemap.fill(darkgrey)

		# TODO: draw map here
		if (editorstate.gamemap != None):
			'''
			maprange = (0, 9, 0, 9)
			for i in range(maprange[0], maprange[1]+1):
				for j in range(maprange[2], maprange[3]+1):
					bgtilerect = Rect(
						(i * TILE_WIDTH, j * TILE_WIDTH),
						(TILE_WIDTH, TILE_WIDTH)
					)
					pygame.draw.rect(
						subscreen_gamemap, white, bgtilerect.get_pyrect(), 1
					)

			blitlists = editorstate.gamemap.draw(spritebatch, 0, 10, 0, 10)
			for blitlist in blitlists:
				subscreen_gamemap.blits(blitlist)
			'''

			# draw background grid #######
			maprange = (1, MAP_WIDTH, 1, MAP_HEIGHT)
			for i in range(maprange[0], maprange[1]+1):
				for j in range(maprange[2], maprange[3]+1):
					bgtilerect = Rect(
						(i * TILE_WIDTH, j * TILE_WIDTH),
						(TILE_WIDTH, TILE_WIDTH)
					)
					pygame.draw.rect(
						subscreen_gamemap, neutralgrey, bgtilerect.get_pyrect(), 1
					)

			wholemaprect = Rect(
				(maprange[0] * TILE_WIDTH, maprange[2] * TILE_WIDTH), 
				((maprange[1]-maprange[0]+1) * TILE_WIDTH, (maprange[3]-maprange[2]+1) * TILE_WIDTH)
			)
			pygame.draw.rect(
				subscreen_gamemap, neutralgrey, wholemaprect.get_pyrect(), 2
			)
			## end draw background grid

		pygame.draw.rect(subscreen_gamemap, darkred, subscreen_gamemap.get_rect(), 2)
		## End Draw Map Surface


		## Draw Mouse Hover Highlight ##################################################
		'''
		pygame.draw.rect(screen, black, 
			Rect(camera.game2screen(
				mpos[0] - mpos[0]%(TILE_WIDTH*2), 
				mpos[1] - mpos[1]%(TILE_WIDTH*2)),
				(TILE_WIDTH*2*camera.zoom, TILE_WIDTH*2*camera.zoom)
			).get_pyrect(), 
			1
		)
		'''
		## End Draw Mouse Hover Highlight
		for highlight_info in highlighted_rects_to_draw:
			highlighted_rect, color, subscreen = highlight_info

			window_rect = highlighted_rect.copy()
			window_rect.move(SUBSCREEN_RECTS[subscreen].get_topleft())

			pygame.draw.rect(window, color, window_rect.get_pyrect(), 1)

		# Draw Debug stuff
		subscreen_menu.blit(font.render(str(mouse_subscreen), 0, black), (5, 2))

		# Switch buffers
		pygame.display.flip()


	pygame.quit()

if __name__=='__main__':
	main(sys.argv[1:])