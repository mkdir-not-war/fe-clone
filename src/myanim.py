from enum import IntEnum
import json

fin = open('./data/graphics/anim-data.json')
ENTITYANIMDATA = json.load(fin)
fin.close()

ANIMCACHESIZE = 20 # maybe make this bigger? probably?
ANIMCACHE = [None] * ANIMCACHESIZE
ANIMCACHELOC = {}

class AnimStyle(IntEnum):
	ONETIME = 1
	REPEAT = 2
	BOOMERANG = 3
	# maybe onetime-boomerang?

# put copy (reset) loaded animation into returnanimation object
def load_animation(returnanimation, entityname, animationname):
	if ((entityname, animationname) in ANIMCACHELOC and ANIMCACHELOC[(entityname, animationname)]):
		ANIMCACHE[ANIMCACHELOC[(entityname, animationname)]].copy_into(returnanimation)
		return True

	loadedanim = Animation()
	data = ENTITYANIMDATA[entityname][animationname]
	loadedanim.entityname = entityname
	loadedanim.animationname = animationname
	loadedanim.row = data['row']
	loadedanim.totalframes = data['frames']
	loadedanim.speed = data['speed']
	if data['style'] == 'onetime':
		loadedanim.set_style(AnimStyle.ONETIME)
	elif data['style'] == 'repeat':
		loadedanim.set_style(AnimStyle.REPEAT)
	elif data['style'] == 'boomerang':
		loadedanim.set_style(AnimStyle.BOOMERANG)

	# not in cache, so add it to cache and pop out oldest anim
	oldanim = ANIMCACHE.pop(0)
	for anim in ANIMCACHELOC:
		ANIMCACHELOC[anim] -= 1
	if (oldanim):
		ANIMCACHELOC[(oldanim.entityname, oldanim.animationname)] = None
	ANIMCACHELOC[(entityname, animationname)] = ANIMCACHESIZE-1
	ANIMCACHE.append(loadedanim)

	loadedanim.copy_into(returnanimation)

	return True

class Animation:
	def __init__(self):
		self.entityname = None
		self.animationname = None
		self.style = None
		self.row = -1
		self.totalframes = 0
		
		self.speed = 0
		self.step = 0
		self.vel = 1
		self.stepfunc = None

		self.curr_frame = 0

	# put copy into returnanim object
	def copy_into(self, returnanim):
		returnanim.entityname = self.entityname
		returnanim.animationname = self.animationname
		returnanim.style = self.style
		returnanim.row = self.row
		returnanim.totalframes = self.totalframes
		
		returnanim.speed = self.speed
		returnanim.step = 0
		if (returnanim.style == AnimStyle.ONETIME):
			returnanim.stepfunc = returnanim.step_onetime
		elif (returnanim.style == AnimStyle.REPEAT):
			returnanim.stepfunc = returnanim.step_repeat
		elif (returnanim.style == AnimStyle.BOOMERANG):
			returnanim.stepfunc = returnanim.step_boomerang

		returnanim.curr_frame = 0
		returnanim.dirty_frame = True # start with dirty frame so it draws?

		return True

	def sample(self):
		return (self.curr_frame, self.row)

	def set_style(self, style):
		self.style = style
		if (self.style == AnimStyle.ONETIME):
			self.stepfunc = self.step_onetime
		elif (self.style == AnimStyle.REPEAT):
			self.stepfunc = self.step_repeat
		elif (self.style == AnimStyle.BOOMERANG):
			self.stepfunc = self.step_boomerang

	def step_onetime(self):
		self.step += 1
		if (self.step > self.speed):
			self.curr_frame += 1
			if (self.curr_frame == self.totalframes-1): #last frame, return true
				return True

	def step_repeat(self):
		self.step += 1
		if (self.step > self.speed):
			self.step = 0
			self.curr_frame += 1
			if (self.curr_frame == self.totalframes): #past last frame, reset to start
				self.curr_frame = 0
				return False

	def step_boomerang(self):
		self.step += 1
		if (self.step > self.speed):
			self.step = 0
			self.curr_frame += self.vel
			if (self.curr_frame == self.totalframes): #past last frame, reverse and backup
				self.vel = -1
				self.curr_frame = self.totalframes-2
				return False
			if (self.curr_frame < 0): #past first frame, reverse and backup
				self.vel = 1
				self.curr_frame = 1
				return False
		