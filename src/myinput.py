from enum import IntEnum
from src.getmath import *
from math import pi, tan, sqrt
import pygame

# constants
JOYSTICK_DEADZONE_EPSILON = 0.30
DEGREE_WINDOW_DIAGONAL = 25
HALFRAD_WINDOW_DIAGONAL = deg2rad(DEGREE_WINDOW_DIAGONAL/2)
DIAG_SMALL_SLOPE = tan(pi / 4 - HALFRAD_WINDOW_DIAGONAL)
DIAG_LARGE_SLOPE = tan(pi / 4 + HALFRAD_WINDOW_DIAGONAL)

class InputMoveDir(IntEnum):
	NONE = 0
	RIGHT = 1
	RIGHT_UP = 2
	UP = 3
	LEFT_UP = 4
	LEFT = 5
	LEFT_DOWN = 6
	DOWN = 7
	RIGHT_DOWN = 8

class InputDataIndex(IntEnum):
	STICK_X = 0
	STICK_Y = 1
	RT = 2
	LT = 3
	A = 4
	B = 5
	START = 6

class BaseInputHandler:
	def __init__(self):
		pass
	def handle_input(self, simstate):
		pass

class IH_MovingAround(BaseInputHandler):
	def handle_input(self, simstate):
		player_entity = simstate.get_active_player()
		inputdata = simstate.inputdata

		# player acceleration directly affected by input
		movedir = (inputdata.get_var(InputDataIndex.STICK_X), inputdata.get_var(InputDataIndex.STICK_Y))
		player_entity.input_ddp = movedir

		# swap players with LT
		if (inputdata.get_var(InputDataIndex.LT) > 0.5 and inputdata.get_var(InputDataIndex.LT, 1) <= 0.5):
			simstate.swap_active_player()

		'''
		## move directions ############
		movedir = inputdata.get_var(InputDataIndex.STICK)
		if (movedir == InputMoveDir.LEFT):
			player_entity.set_target((-1, 0))
		elif (movedir == InputMoveDir.RIGHT):
			player_entity.set_target((1, 0))
		elif (movedir == InputMoveDir.UP):
			player_entity.set_target((0, -1))
		elif (movedir == InputMoveDir.DOWN):
			player_entity.set_target((0, 1))
		# diagonals
		elif (movedir == InputMoveDir.LEFT_UP):
			player_entity.set_target((-1, -1))
		elif (movedir == InputMoveDir.RIGHT_UP):
			player_entity.set_target((1, -1))
		elif (movedir == InputMoveDir.LEFT_DOWN):
			player_entity.set_target((-1, 1))
		elif (movedir == InputMoveDir.RIGHT_DOWN):
			player_entity.set_target((1, 1))
		## end move direction
		'''


MAXINPUTQUEUELEN = 5

class InputDataBuffer:
	def __init__(self):
		self.queuelength = 0

		self.vars = []

		# append in order of input data index enum
		for inputtype in InputDataIndex:
			self.vars.append([])

		self.button_mapping = {
			pygame.K_SPACE : InputDataIndex.A, # counter
			pygame.K_s : InputDataIndex.B, # switch
			pygame.K_f : InputDataIndex.RT, # light attack
			pygame.K_d : InputDataIndex.LT # heavy attack
		}

	def newinput(self, joystick):
		if (self.queuelength == MAXINPUTQUEUELEN):
			for varlist in self.vars:
				varlist.pop(0)
		else:
			self.queuelength += 1

		# put in default values
		for varlist in self.vars:
			varlist.append(0)

		moveinputvecx, moveinputvecy = (0, 0)

		# TODO: what about HAT? Pokken controller? SNES?
		# joystick directions
		if (abs(joystick.axis[0]) > JOYSTICK_DEADZONE_EPSILON):
			moveinputvecx = joystick.axis[0] #sign(joystick.axis[0])
		if (abs(joystick.axis[1]) > JOYSTICK_DEADZONE_EPSILON):
			moveinputvecy = joystick.axis[1] #sign(joystick.axis[1])

		'''
		JOSTICK AXES:
			0	- left stick X
			1	- left stick Y
			2	- right stick X
			3	- right stick Y
			4	- left trigger
			5	- right trigger
		'''

		if (joystick.axis[4] > JOYSTICK_DEADZONE_EPSILON):
			self.set_var(InputDataIndex.LT, joystick.axis[4])
		if (joystick.axis[5] > JOYSTICK_DEADZONE_EPSILON):
			self.set_var(InputDataIndex.RT, joystick.axis[5])
			

		# TODO: maybe use this instead of stick in some cases? Pokken controller?
		## joystick.hat[event.hat] = event.value

		# button mapping
		for button in joystick.button:
			if button in self.button_mapping:
				self.set_var(self.button_mapping[button], True)

		# continuous thumbstick directions
		self.set_var(InputDataIndex.STICK_X, moveinputvecx)
		self.set_var(InputDataIndex.STICK_Y, moveinputvecy)

		# TODO(grid): holding the stick feels too quick right now...

		'''
		# discrete thumbstick/keyboard directions
		if moveinputvecx > 0:
			if moveinputvecx**2 > moveinputvecy**2:
				self.set_var(InputDataIndex.STICK, InputMoveDir.RIGHT)
			elif moveinputvecy < 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
			elif moveinputvecy > 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
		elif moveinputvecx < 0:
			if moveinputvecx**2 > moveinputvecy**2:
				self.set_var(InputDataIndex.STICK, InputMoveDir.LEFT)
			elif moveinputvecy < 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
			elif moveinputvecy > 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
		else:
			if moveinputvecy > 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
			elif moveinputvecy < 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
		'''

		'''
		if moveinputvecx > 0:
			slope = moveinputvecy/moveinputvecx
			if (slope <= -DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
			elif (slope > -DIAG_LARGE_SLOPE and slope < -DIAG_SMALL_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.RIGHT_UP)
			elif (slope >= -DIAG_SMALL_SLOPE and slope <= DIAG_SMALL_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.RIGHT)
			elif (slope > DIAG_SMALL_SLOPE and slope < DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.RIGHT_DOWN)
			elif (slope >= DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
		elif moveinputvecx < 0:
			slope = moveinputvecy/moveinputvecx
			if (slope <= -DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
			elif (slope > -DIAG_LARGE_SLOPE and slope < -DIAG_SMALL_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.LEFT_DOWN)
			elif (slope >= -DIAG_SMALL_SLOPE and slope <= DIAG_SMALL_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.LEFT)
			elif (slope > DIAG_SMALL_SLOPE and slope < DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.LEFT_UP)
			elif (slope >= DIAG_LARGE_SLOPE):
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
		else:
			if moveinputvecy > 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.DOWN)
			elif moveinputvecy < 0:
				self.set_var(InputDataIndex.STICK, InputMoveDir.UP)
		'''

	def set_var(self, var_idi, val):
		self.vars[var_idi][self.queuelength-1] = val
		return val

	def get_var(self, var_idi, queuei=0):
		if (self.queuelength-1-queuei < 0):
			return None
		result = self.vars[var_idi][self.queuelength-1-queuei]
		return result

class JoystickHandler(object):
    def __init__(self, id):
        self.id = id
        self.joy = pygame.joystick.Joystick(id)
        self.name = self.joy.get_name()
        self.joy.init()
        self.numaxes    = self.joy.get_numaxes()
        self.numballs   = self.joy.get_numballs()
        self.numbuttons = self.joy.get_numbuttons()
        self.numhats    = self.joy.get_numhats()

        self.axis = []
        for i in range(self.numaxes):
            self.axis.append(self.joy.get_axis(i))

        self.ball = []
        for i in range(self.numballs):
            self.ball.append(self.joy.get_ball(i))

        self.button = []
        for i in range(self.numbuttons):
            self.button.append(self.joy.get_button(i))

        self.hat = []
        for i in range(self.numhats):
            self.hat.append(self.joy.get_hat(i))