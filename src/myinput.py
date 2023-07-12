import pygame

from math import pi, tan, sqrt
from enum import IntEnum

from src.mymath import *
from src.constants import *

# constants
JOYSTICK_DEADZONE_EPSILON = 0.30
DEGREE_WINDOW_DIAGONAL = 25
HALFRAD_WINDOW_DIAGONAL = deg2rad(DEGREE_WINDOW_DIAGONAL/2)
DIAG_SMALL_SLOPE = tan(pi / 4 - HALFRAD_WINDOW_DIAGONAL)
DIAG_LARGE_SLOPE = tan(pi / 4 + HALFRAD_WINDOW_DIAGONAL)
BUTTONHOLDTIME_TRIGGER = 2.5 # seconds

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

def v2_to_facingdirection(currdirection, v2, onlyleftright=False):
	result = currdirection

	if v2 != (0, 0):
		dpx, dpy = v2
		# discrete thumbstick/keyboard directions
		if dpx > 0:
			if onlyleftright:
				result = InputMoveDir.RIGHT
			elif dpx**2 > dpy**2:
				result = InputMoveDir.RIGHT
			elif dpy < 0:
				result = InputMoveDir.RIGHT_UP
			elif dpy > 0:
				result = InputMoveDir.RIGHT_DOWN
		elif dpx < 0:
			if onlyleftright:
				result = InputMoveDir.LEFT
			elif dpx**2 > dpy**2:
				result = InputMoveDir.LEFT
			elif dpy < 0:
				result = InputMoveDir.LEFT_UP
			elif dpy > 0:
				result = InputMoveDir.LEFT_DOWN
		else: # no x-direction, default facing right
			if onlyleftright:
				result = InputMoveDir.RIGHT
			elif dpy > 0:
				result = InputMoveDir.RIGHT_DOWN
			elif dpy < 0:
				result = InputMoveDir.RIGHT_UP

	return result

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
		player_entity = simstate.entities[simstate.activeplayer]
		inputdata = simstate.inputdata

		# player acceleration directly affected by input
		movedir = (inputdata.get_var(InputDataIndex.STICK_X), inputdata.get_var(InputDataIndex.STICK_Y))
		player_entity.input_ddp = movedir

		# swap players with RT
		if (inputdata.get_var(InputDataIndex.LT) > 0.5 and inputdata.get_var(InputDataIndex.RT, 1) <= 0.5):
			simstate.swap_active_player()

class IH_PreFight(BaseInputHandler):
	def handle_input(self, simstate):
		# hold A to start combat
		if inputdata.get_var(InputDataIndex.A):
			simstate.buttonholdtimer += PHYSICS_TIME_STEP
			if simstate.buttonholdtimer > BUTTONHOLDTIME_TRIGGER:
				simstate.begin_combat()
		else:
			simstate.buttonholdtimer = 0.0

MAXINPUTQUEUELEN = 5

class InputDataBuffer:
	def __init__(self):
		self.queuelength = 0

		self.vars = []

		# append in order of input data index enum
		for inputtype in InputDataIndex:
			self.vars.append([])

		self.button_mapping = {
			pygame.K_SPACE : InputDataIndex.A,
			pygame.K_s : InputDataIndex.B,
			pygame.K_f : InputDataIndex.RT,
			pygame.K_d : InputDataIndex.LT
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