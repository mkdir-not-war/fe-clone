import pygame
from math import sqrt
from enum import IntEnum
from tkinter import Tk 
import sys
import json
import pickle

from src.getmath import *

# constants
WIN_WIDTH = 800
WIN_HEIGHT = 600

# no zoom, adds too much complexity

TILE_WIDTH = 32

TILEMAPWIN_WIDTH = 600
COLLISIONSET_ZOOM = 2

TILEMAP_WIDTH_IN_TILES = 8
TILEMAP_NUM_ANIMATED_ROWS = 2

MENU_WIDTH = (WIN_WIDTH - TILEMAPWIN_WIDTH)
TILEMAP_XWINPOS = MENU_WIDTH

SUBSCREEN_RECTS = {
	'menu' : Rect((0, 0), (MENU_WIDTH, WIN_HEIGHT)),
	'tile map' : Rect((TILEMAP_XWINPOS, 0), (TILEMAPWIN_WIDTH, WIN_HEIGHT))
}

FPS = 60
FRAMES_PER_ANIMATION = 16
TILES_PER_ANIMATION = 4

# input codes
class InputCodes(IntEnum):
	MOUSE_LEFT = 1
	MOUSE_SCROLLUP = 4
	MOUSE_SCROLLDOWN = 5

# colors
lightgrey = pygame.Color(180, 180, 190)
neutralgrey = pygame.Color(150, 150, 160)
darkgrey = pygame.Color(50, 50, 65)
darkred = pygame.Color(80, 0, 0)
lightred = pygame.Color(250, 100, 100)
lightblue = pygame.Color(100, 100, 250)
black = pygame.Color('black')
white = pygame.Color('white')

pygame.font.init()
font_arial = pygame.font.Font("./data/fonts/ARI.ttf", 16)

# one spritebatch for animated sprites, one for not (i.e. geometry)
class SpriteBatch:
	def __init__(self):
		self.length = 0

		self.sprites = []

		fin = open('./data/graphics/texture-data.json')
		self.scenespritedata = json.load(fin)
		fin.close()

		self.tilemap_sprite = pygame.image.load(self.scenespritedata['tilemap']['filepath'])

		self.tilemap_dim = (
			self.tilemap_sprite.get_rect().width // TILE_WIDTH, 
			self.tilemap_sprite.get_rect().height // TILE_WIDTH
		)

		# scale by collision zoom
		scale = (
			self.tilemap_sprite.get_rect().width * COLLISIONSET_ZOOM, 
			self.tilemap_sprite.get_rect().height * COLLISIONSET_ZOOM
		)
		self.tilemap_sprite = pygame.transform.scale(self.tilemap_sprite, scale)

	def draw_tilemap(self, editorstate):

		tilepickerimg, tilepickerarea, tilepickerdest = self.tilemap_sprite, None, None

		drawxpos = TILEMAPWIN_WIDTH//2 - (TILE_WIDTH * TILEMAP_WIDTH_IN_TILES)//2 * COLLISIONSET_ZOOM

		## Draw animated tiles animating
		result = []

		# TODO: skip drawing animated tiles that aren't in frame (check scrolling)
		for row in range(TILEMAP_NUM_ANIMATED_ROWS):
			for col_index in [0, 1]: 
				column = col_index * TILES_PER_ANIMATION

				tilepickerarea = Rect(
					((column + editorstate.animation_step) * TILE_WIDTH * COLLISIONSET_ZOOM, 
						row * TILE_WIDTH * COLLISIONSET_ZOOM),
					(TILE_WIDTH * COLLISIONSET_ZOOM, 
						TILE_WIDTH * COLLISIONSET_ZOOM)
				)

				tilepickerdest = Rect(
					(drawxpos + col_index * TILE_WIDTH * 4 * COLLISIONSET_ZOOM, 
						row * TILE_WIDTH * COLLISIONSET_ZOOM - editorstate.tilepickerscrolly * TILE_WIDTH), 
					(TILE_WIDTH * COLLISIONSET_ZOOM, 
						TILE_WIDTH * COLLISIONSET_ZOOM)
				)

				result.append((tilepickerimg, tilepickerdest.get_pyrect(), tilepickerarea.get_pyrect()))

		## Draw static tiles

		area_yval = None #(editorstate.tilepickerscrolly - (TILEMAP_NUM_ANIMATED_ROWS * COLLISIONSET_ZOOM)) * TILE_WIDTH
		if TILEMAP_NUM_ANIMATED_ROWS * COLLISIONSET_ZOOM > editorstate.tilepickerscrolly:
			area_yval = TILEMAP_NUM_ANIMATED_ROWS * COLLISIONSET_ZOOM * TILE_WIDTH
		else:
			area_yval = editorstate.tilepickerscrolly * TILE_WIDTH

		tilepickerarea = Rect(
			(0, area_yval),
			(
				TILE_WIDTH * TILEMAP_WIDTH_IN_TILES * COLLISIONSET_ZOOM, 
				WIN_HEIGHT
			)
		)

		tilepickerdest = Rect(
			(
				drawxpos,
				max(
					0,
					(TILEMAP_NUM_ANIMATED_ROWS * COLLISIONSET_ZOOM - editorstate.tilepickerscrolly) * TILE_WIDTH
				)
			), 
			(tilepickerarea.width, tilepickerarea.height)
		)

		result.append((tilepickerimg, tilepickerdest.get_pyrect(), tilepickerarea.get_pyrect()))

		return result

	def draw_collmap(self, editorstate, tilepickheight):
		result = []

		tilepicker_xpos = TILEMAPWIN_WIDTH//2 - (TILE_WIDTH * TILEMAP_WIDTH_IN_TILES)//2 * COLLISIONSET_ZOOM

		for y in range(WIN_HEIGHT // TILE_WIDTH + 1): # for each collision tile on the screen

			tileposy = (y + editorstate.tilepickerscrolly) // COLLISIONSET_ZOOM
			yoff = (y + editorstate.tilepickerscrolly) % COLLISIONSET_ZOOM

			for x in range(TILEMAP_WIDTH_IN_TILES * COLLISIONSET_ZOOM):

				tileposx = x // COLLISIONSET_ZOOM
				xoff = x % COLLISIONSET_ZOOM

				thisrect = Rect(
					(
						x * TILE_WIDTH + tilepicker_xpos, 
						y * TILE_WIDTH
					), 
					(TILE_WIDTH, TILE_WIDTH)
				)

				# filter out tiles out of range and not over boxes
				if (tileposy >= 0 and 
					tileposy < tilepickheight and 
					tileposx >= 0 and 
					tileposx < TILEMAP_WIDTH_IN_TILES and
					# if inside animated range, only highlight single columns
					(tileposy >= TILEMAP_NUM_ANIMATED_ROWS or 
						(x in range(0, COLLISIONSET_ZOOM) or 
						x in range(4*COLLISIONSET_ZOOM, 5*COLLISIONSET_ZOOM))
					)
				):

					bitmask = (0x1 << (yoff*4 * COLLISIONSET_ZOOM)) << xoff*4
					colmapindex = tileposx + tileposy * TILEMAP_WIDTH_IN_TILES

					iscollide = editorstate.collisionmap[colmapindex] & bitmask > 0
					result.append((thisrect.get_pyrect(), iscollide))

		return result

def get_rect_and_inner(rect, outercolor, innercolor, subscreen, offset=2):
	result = []
	# highlight it (add <rect, color, window> to list, draw later)
	result.append((rect, outercolor, subscreen))
	# also highlight an inner square as white, so it's visible on dark tiles
	innerrect = rect.copy()
	innerrect.move((offset//2, offset//2))
	innerrect.width -= offset//2*2
	innerrect.height -= offset//2*2
	result.append((innerrect, innercolor, subscreen))
	return result

## MOUSE ACTION FUNCTIONS -> return Rect to highlight ###########################
def do_tilemap(editorstate, tilepickheight):
	result = None

	tilepicker_xpos = TILEMAPWIN_WIDTH//2 - (TILE_WIDTH * TILEMAP_WIDTH_IN_TILES)//2 * COLLISIONSET_ZOOM
	coltileposx = (editorstate.subsurf_mousepos[0] - tilepicker_xpos) // TILE_WIDTH

	screentileposy = (editorstate.subsurf_mousepos[1] // TILE_WIDTH)
	coltileposy = screentileposy + editorstate.tilepickerscrolly

	result = Rect(
		(coltileposx * TILE_WIDTH + tilepicker_xpos, screentileposy * TILE_WIDTH), 
		(TILE_WIDTH, TILE_WIDTH)
	)

	mousedtile = coltileposx//COLLISIONSET_ZOOM + coltileposy//COLLISIONSET_ZOOM * TILEMAP_WIDTH_IN_TILES

	# filter out tiles out of range and not over boxes
	if not (coltileposy >= 0 and coltileposy < (tilepickheight+TILEMAP_NUM_ANIMATED_ROWS) * COLLISIONSET_ZOOM and
			coltileposx >= 0 and coltileposx < TILEMAP_WIDTH_IN_TILES * COLLISIONSET_ZOOM and
			# if inside animated range, only highlight columns 0 and 4
			(coltileposy >= TILEMAP_NUM_ANIMATED_ROWS * COLLISIONSET_ZOOM or 
				(coltileposx in range(0, COLLISIONSET_ZOOM) or 
					coltileposx in range(4*COLLISIONSET_ZOOM, 5*COLLISIONSET_ZOOM))
			)):

		result = None

	# click left mouse button -> toggle collision
	if (result != None and
		InputCodes.MOUSE_LEFT in editorstate.prev_input and 
		not InputCodes.MOUSE_LEFT in editorstate.curr_input):

		succ = togglecollision(editorstate, coltileposx, coltileposy)

	return result, mousedtile
## End MOUSE ACTION FUNCTIONS

## COLLISION MAP FUNCTIONS
def togglecollision(editorstate, coltilex, coltiley):
	if (coltilex < 0 or 
		coltilex >= TILEMAP_WIDTH_IN_TILES * COLLISIONSET_ZOOM or 
		coltiley < 0 or
		False # check if y is too high, idk
	):
		print(coltilex, coltiley, TILEMAP_WIDTH_IN_TILES * COLLISIONSET_ZOOM, len(editorstate.collisionmap))
		return False
	else:
		tilex = coltilex // COLLISIONSET_ZOOM
		tiley = coltiley // COLLISIONSET_ZOOM
		colmapindex = tilex + tiley * TILEMAP_WIDTH_IN_TILES

		xoff = coltilex % COLLISIONSET_ZOOM
		yoff = coltiley % COLLISIONSET_ZOOM

		bitmask = (0x1 << (yoff*4 * COLLISIONSET_ZOOM)) << xoff*4
		
		editorstate.collisionmap[colmapindex] ^= bitmask

		#print('collision tile %d index toggled: 0x%.4x' % (colmapindex, bitmask))

		return True

'''
Save collision map as ints where each bit in the hex saves the collision of the
corresponding tile starting at top-left, then top-right, then bottom-left, then bottom-right

0x0000_1234 =>

	1  2

	3  4 (not that we would ever use 2, 3 or 4. Just showing them here for illustration purpose)

collisionmap in editorstate is a list of ints each making up one chunk (four bits)

'''
def loadcollision(tilemap_dim):
	fin = open('./data/maps/collisiontilemap.dat', 'r')
	flatresult = [int(i) for i in fin.read().split(' ')]
	fin.close()

	maplen = tilemap_dim[0] * tilemap_dim[1]

	if len(flatresult) < maplen:
		extrazeroes = [0] * (maplen - len(flatresult))
		flatresult.extend(extrazeroes)

	'''
	print(flatresult)
	for i in flatresult:
		print(i, '=>', i&(0x1000)>0, i&(0x0100)>0, i&(0x0010)>0, i&(0x0001)>0)
	print(int(0x1000), int(0x0100), int(0x0010), int(0x0001))
	print(int(0x1 << 3), int(0x1000))
	'''

	return flatresult

def savecollision(editorstate):
	# save copy of old map
	fin = open('./data/maps/collisiontilemap.dat', 'r')
	fincopy = open('./data/maps/collisiontilemap-old.dat', 'w')

	output = fin.read()
	fincopy.write(output)

	fincopy.close()
	fin.close()

	# save off new map
	fin = open('./data/maps/collisiontilemap.dat', 'w')
	output = ' '.join([str(i) for i in editorstate.collisionmap])
	fin.write(output)
	fin.close()
## End COLLISION MAP FUNCTIONS

	
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
		self.recently_saved = False

		# tilepicker stuff
		self.tileindex2paint = None
		self.selectedtilerect = None
		self.tilepickerscrolly = 0

		# gamemap stuff
		self.collisionmap = None

	def animate(self):
		self.counter += 1
		if (self.counter >= FRAMES_PER_ANIMATION):
			self.animation_step += 1
			self.counter = 0
		if (self.animation_step >= 4):
			self.animation_step = 0

def main(argv):
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
	subscreen_tilemap = window.subsurface(SUBSCREEN_RECTS['tile map'].get_pyrect())

	# cache structure for all sprite flyweights
	spritebatch = SpriteBatch()

	# editor state
	editorstate = EditorState()
	editorstate.collisionmap = loadcollision(spritebatch.tilemap_dim)
	#savecollision(editorstate)

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
				elif event.key == pygame.K_s:
					editorstate.curr_input.append('s')
			elif event.type == pygame.KEYUP:
				if event.key == pygame.K_s:
					editorstate.curr_input.remove('s')

			# mouse inputs
			elif event.type == pygame.MOUSEWHEEL:
				if event.y == 1:
					editorstate.curr_input.append(4)
				elif event.y == -1:
					editorstate.curr_input.append(5)
			# mouse clicking		
			elif event.type == pygame.MOUSEBUTTONDOWN:
				editorstate.curr_input.append(event.button)
			elif event.type == pygame.MOUSEBUTTONUP:
				if event.button in editorstate.curr_input:
					editorstate.curr_input.remove(event.button)

		# save if pressed S
		if 's' in editorstate.curr_input and not editorstate.recently_saved:
			savecollision(editorstate)
			editorstate.recently_saved = True
			print('Saved collision map.')

		if editorstate.recently_saved and not 's' in editorstate.curr_input:
			editorstate.recently_saved = False

		# mouse position
		screenmousepos = pygame.mouse.get_pos()
		mousedtileindex = -1

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
			elif mouse_subscreen == 'tile map':
				# if mouse in tile map and scrolling, scroll the tile map
				if InputCodes.MOUSE_SCROLLUP in editorstate.curr_input:
					editorstate.tilepickerscrolly = max(editorstate.tilepickerscrolly-1, 0)
				elif InputCodes.MOUSE_SCROLLDOWN in editorstate.curr_input:
					editorstate.tilepickerscrolly = min(
						editorstate.tilepickerscrolly+1, 
						spritebatch.tilemap_dim[1] + WIN_HEIGHT//TILE_WIDTH
					)

				mouse_rect, mousedtileindex = do_tilemap(editorstate, spritebatch.tilemap_dim[1])

			# if mouse rect, 
			if mouse_rect != None:
				# highlight it (add <rect, color, window> to list, draw later)
				# and also highlight an inner square as white, so it's visible on dark tiles
				highlighted_rects_to_draw.extend(
					get_rect_and_inner(mouse_rect, black, white, mouse_subscreen, 4)
				)

		################################################################################
		# DRAW! ########################################################################
		################################################################################

		# Start drawing
		window.fill(neutralgrey) # TODO: change this to off-black??

		## Draw Menu Options ###########################################################
		subscreen_menu.blit(font.render('Press S to save.', 0, darkred), (5, 2))
		subscreen_menu.blit(font.render('Mouse TileIndex: %d' % mousedtileindex, 0, darkred), (5, 26))

		pygame.draw.rect(subscreen_menu, darkred, subscreen_menu.get_rect(), 3)
		## End Draw Menu Options


		## Draw Tile Map Surface ####################################################
		tilemapimgs = spritebatch.draw_tilemap(editorstate)
		subscreen_tilemap.blits(tilemapimgs)

		# draw collision rects
		collisionrects = spritebatch.draw_collmap(editorstate, spritebatch.tilemap_dim[1])
		for colrectinfo in collisionrects:
			rect2draw, iscollide = colrectinfo

			if iscollide:
				pygame.draw.rect(subscreen_tilemap, lightred, rect2draw, 3)
			else:
				pygame.draw.rect(subscreen_tilemap, lightgrey, rect2draw, 1)

		pygame.draw.rect(subscreen_tilemap, darkred, subscreen_tilemap.get_rect(), 3)
		
		# highlight selected tile to paint
		if editorstate.selectedtilerect != None:
			selectedtilerects = get_rect_and_inner(
				editorstate.selectedtilerect, None, None, None
			)
			pygame.draw.rect(
				subscreen_tilemap, lightblue, selectedtilerects[0][0].get_pyrect(), 1
			)
			pygame.draw.rect(
				subscreen_tilemap, white, selectedtilerects[1][0].get_pyrect(), 1
			)
		## End Draw Tile Map Surface

		# debug just print name of subsurface mouse is on
		for highlight_info in highlighted_rects_to_draw:
			highlighted_rect, color, subscreen = highlight_info

			window_rect = highlighted_rect.copy()
			window_rect.move(SUBSCREEN_RECTS[subscreen].get_topleft())

			pygame.draw.rect(window, color, window_rect.get_pyrect(), 2)

		# Draw Debug stuff
		#subscreen_menu.blit(font.render(str(mouse_subscreen), 0, black), (5, 132))
		#subscreen_menu.blit(font.render(str(editorstate.tilepickerscrolly), 0, black), (5, 150))

		# Switch buffers
		pygame.display.flip()


	pygame.quit()

if __name__=='__main__':
	main(sys.argv[1:])