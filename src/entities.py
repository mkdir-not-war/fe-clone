from enum import IntEnum
from src.mymath import *
import src.myanim as myanim
from src.myinput import *
from src.constants import *
from src.mapgen import ExitDirection

class Entity:
	def __init__(self):
		self.active = True # dont draw or collide when inactive

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
		self.coll_box = Rect((0, 0), (self.coll_width*2, self.coll_height*2))

	def get_prevpos(self):
		return (self.prev_x, self.prev_y)

	def get_collrect(self):
		result = self.coll_box.translate((self.x-self.coll_width, self.y-self.coll_height))
		result.set_dim(self.coll_width*2, self.coll_height*2)
		return result

	def set_col(self, w, h):
		self.coll_width = w
		self.coll_height = h
		self.coll_box.set_dim(w, h)

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
		self.active = False
		
		if (exitdirection == ExitDirection.NORTH or exitdirection == ExitDirection.BUILDING):
			myanim.load_animation(self.curr_animation, 'exit', 'north')
		elif (exitdirection == ExitDirection.SOUTH):
			myanim.load_animation(self.curr_animation, 'exit', 'south')
		elif (exitdirection == ExitDirection.EAST):
			myanim.load_animation(self.curr_animation, 'exit', 'east-west')
		elif (exitdirection == ExitDirection.WEST):
			myanim.load_animation(self.curr_animation, 'exit', 'east-west')
			self.flipanimhorz = True

class PlayerAnimState(IntEnum):
	IDLE = 0
	WALK = 1

class CombatActionIndex(IntEnum):
	DEFEND 	= 0
	SKILL1 	= 1
	SKILL2 	= 2
	SKILL3 	= 3
	SKILL4 	= 4
	SKILL5 	= 5

	TOTAL 	= 6

class CombatEntity:
	def __init__(self):
		self.max_hp = 0
		self.curr_hp = 0
		self.speed = 0

		self.actionids = [None] * CombatActionIndex.TOTAL
		self.actionmodids = [None] * CombatActionIndex.TOTAL

class PlayerCharacterIndex(IntEnum):
	# all characters are members of the secret cabal of exorcists
	SLOANE	= 0		# bearded, stoic, former general turned assassin
	EIRWEN	= 1		# tanned, boisterous, competent
	BLAYNO 	= 2		# boisterous, pale, snake eyed soldier

class PlayerCharacter:
	def __init__(self):
		self.nametext = ''
		self.characterindex = -1

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

		self.set_col(TILE_WIDTH * 0.4, TILE_WIDTH * 0.2)

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
			self.facing_direction = v2_to_leftright(self.facing_direction, self.input_ddp)
		else:
			self.facing_direction = v2_to_leftright(self.facing_direction, vec2player)

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