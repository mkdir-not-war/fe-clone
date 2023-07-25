import json

from src.constants import *

MENUDATAPATH = './data/graphics/menu-data.json'

class MenuSceneIndex(IntEnum):
	MAINMENU 		= 0
	FREEMOVE 		= 1
	COMBATPLAYER	= 2

	TOTAL 			= 3

class MenuElementType(IntEnum):
	TEXT = 0
	IMAGE = 1

class MenuElement:
	def __init__(self, index):
		# load from file
		self.element_type = None
		self.x = 0
		self.y = 0
		self.newlinepx = 0
		self.scriptid = None
		self.autorun = False

		self.texturename = ''

		# set on load
		self.index = index
		self.renderedtext = None
		self.textwidth = 0

		# toggle on via input to run script
		self.runscript = False

	def set_text(self, text, color=COLORS['bone']):
		self.renderedtext = render_text(text, color)
		self.textwidth = get_textwidth(text)

	def get_position(self):
		position = (self.x, self.y)
		result = []
		for i in range(len(self.renderedtext)):
			result.append((position[0], position[1] + i * self.newlinepx))
		return result

	def activate(self):
		self.runscript = True

	def update(self, simstate, mapgen):
		if self.runscript or self.autorun:
			self.runscript = False
			result = SCRIPTSDICT[self.scriptid](self, simstate, mapgen)
			return result

# use to get elements for current scene out of menuhandler.allelements[]
class MenuScene:
	def __init__(self, index, length):
		self.elementindex = index
		self.length = length

class MenuHandler:
	def __init__(self):
		self.allelements = []
		self.allscenes = [None] * MenuSceneIndex.TOTAL

		self.hoveringelement_index = -1 # this isn't always set
		self.curr_sceneindex = -1
		
	def update(self, simstate, mapgen):
		for element in self.get_sceneelements():
			element.update(simstate, mapgen)

	def get_currelement(self):
		return self.allelements[self.hoveringelement_index]

	def get_currscene(self):
		return self.allscenes[self.curr_sceneindex]

	def get_sceneelements(self, sceneindex=None):
		if sceneindex == None:
			sceneindex = self.curr_sceneindex
		scene = self.allscenes[sceneindex]
		result = self.allelements[scene.elementindex : scene.elementindex+scene.length]
		return result

	def get_nextelement_indirection(self, raw_movevec):
		# do dot product, sort, remove results <0
		# if results are within some epsilon, choose the nearest
		pass

	def load(self):
		fin = open(MENUDATAPATH, 'r')
		data = json.load(fin)
		fin.close()

		self.curr_sceneindex = MenuSceneIndex[data['starting-scene']]
		numelements = 0
		for scenename in data['scenes']:
			startelementindex = numelements
			elementsinscene = 0
			for elementdata in data['scenes'][scenename]:
				self.allelements.append(MenuElement(numelements))
				self.allelements[numelements].element_type 	= MenuElementType[elementdata['element_type']]
				self.allelements[numelements].x 			= int(elementdata['x'])
				self.allelements[numelements].y 			= int(elementdata['y'])
				self.allelements[numelements].newlinepx		= int(elementdata['newlinepx'])
				self.allelements[numelements].renderedtext	= render_text(elementdata['text'], COLORS['bone'])
				self.allelements[numelements].textwidth		= get_textwidth(elementdata['text'])
				self.allelements[numelements].texturename 	= elementdata['texturename']
				self.allelements[numelements].scriptid 		= MenuElementScript[elementdata['scriptid']]
				self.allelements[numelements].autorun 		= elementdata['autorun']
				numelements += 1
				elementsinscene += 1
			self.allscenes[MenuSceneIndex[scenename]] = MenuScene(startelementindex, elementsinscene)

def render_text(text, color):
	if text == None:
		return []
	result = []
	for line in text.split('\n'):
		result.append(font_depixel16.render(line, 0, color))

	return result

def get_textwidth(text):
	if text == None:
		return 0
	result = max([len(line) for line in text.split('\n')])
	return result



########################################################################################################
##### SCRIPTS ##########################################################################################
########################################################################################################

class MenuElementScript(IntEnum):
	MM_START 		= 0
	FM_PLACARD 		= 1
	CBP_INDICATOR	= 2

## Start Scripts ############

def SCRIPT_FM_PLACARD(element, simstate, mapgen):
	element.set_text(mapgen.get_regionname())

def SCRIPT_CBP_INDICATOR(element, simstate, mapgen):
	element.set_text(mapgen.get_regionname())

## Scripts Dict

SCRIPTSDICT = {
	MenuElementScript.FM_PLACARD 		: SCRIPT_FM_PLACARD,
	MenuElementScript.CBP_INDICATOR 	: SCRIPT_CBP_INDICATOR
}
