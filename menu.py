from enum import IntEnum

class MenuEnum(IntEnum):
	MAIN = 0
	INTRO = 1

class MenuOption:
	def __init__(self, ch, name, func):
		self.ch = ch
		self.name = name
		self.func = func

class Menu:
	def __init__(self, name):
		self.options = []
		self.name = name

	def print(self):
		result = '== %s ==\n\n' % (self.name)
		for option in self.options:
			result += ' %s: %s\n' % (option.ch.upper(), option.name)
		return result

	def handle_input(self, ch, gamedata):
		for option in self.options:
			if (ch == ord(option.ch)):
				result = option.func(gamedata)
				return result # (quit, current/new menu_enum)
		return (False, None, '')

def load_menus():
	result = []

	# 0: main menu
	menu = Menu('MAIN MENU')
	menu.options.append(MenuOption('q', 'Exit Program', mainmenu_quit))
	menu.options.append(MenuOption('n', 'Restart Game', mainmenu_newgame))
	result.append(menu)

	# 1: intro

	return result

def mainmenu_quit(gamedata):
	debug = ''
	return (True, None, debug)

def mainmenu_newgame(gamedata):
	debug = 'poop'
	gamedata.reset()
	return (False, MenuEnum.MAIN, debug)