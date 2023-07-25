from enum import IntEnum
from pygame import font, Color

TILE_WIDTH = 32
GAMEMAP_TILES_WIDE = 19
GAMEMAP_TILES_HIGH = 15
GAMEMAP_SIZE = GAMEMAP_TILES_HIGH * GAMEMAP_TILES_WIDE

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

MAX_COMBAT_ENEMIES = 14

# colors
COLORS = {
	'neutralgrey' 	: Color(150, 150, 160),
	'darkgrey' 		: Color(50, 50, 65),
	'darkred' 		: Color(80, 0, 0),
	'lightred' 		: Color(250, 100, 100),
	'lightblue' 	: Color(100, 100, 250),
	'bone' 			: Color(227, 218, 201),
	'black' 		: Color('black'),
	'white' 		: Color('white')
}


# fonts
font.init()
font_arial16 = font.Font('./data/fonts/ARI.ttf', 16)
font_depixel16 = font.Font('./data/fonts/DePixelBreit.ttf', 16)

# enums
class InputMoveDir(IntEnum):
	RIGHT 		= 0
	RIGHT_UP 	= 1
	UP 			= 2
	LEFT_UP 	= 3
	LEFT 		= 4
	LEFT_DOWN 	= 5
	DOWN 		= 6
	RIGHT_DOWN 	= 7

	NONE 		= 8

def get_oppdirection(direction):
	result = (direction.value + 8) % 8
	return result