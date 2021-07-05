import curses
from enum import Enum

def init_curses():
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(True)
	stdscr.nodelay(True)
	return stdscr

def end_curses(stdscr):
	curses.nocbreak()
	stdscr.keypad(False)
	curses.echo()
	curses.endwin()

def dot(v1, v2):
	result = 0
	for i in list(range(v1)):
		result += v1[i] * v2[i]
	return result

def norm_dot(v1, v2, length=-1):
	if (length < 0):
		length = len(v1)
	result = dot(v1, v2)
	result /= length
	return result

class MenuOption:
	def __init__(self, name, display):
		self.name = name
		self.display = display

		self.dirs = {
			'UP' : None,
			'DOWN' : None,
			'LEFT' : None,
			'RIGHT' : None
		}

	def set_next(self, up=0, down=0, left=0, right=0):
		self.dirs['UP'] = up
		self.dirs['DOWN'] = down
		self.dirs['LEFT'] = left
		self.dirs['RIGHT'] = right

	def get_next(self, nextdir):
		return self.dirs[nextdir]

	def print(self):
		return self.display

class Menu:
	def __init__(self, spacing=4):
		self.curr_x = None
		self.curr_row = None

		self.options = []

		self.spacing = spacing

	def reset(self):
		self.curr_x = 0
		self.curr_row = 0

	def set_options(self, *options):
		self.options.clear()

		result = []
		for option in options:
			if option != '\n':
				result.append(option)
			else:
				self.options.append(result[:])
				result.clear()
		self.options.append(result[:])

	def print(self):
		result = []
		for row in range(len(self.options)):
			line = ''
			for i in range(len(self.options[row])):
				option = self.options[row][i]
				optionline = ''
				if (self.curr_x == i and self.curr_row == row):
					optionline = '> %s' % (option.print())
				else:
					optionline = '  %s' % (option.print())
				line += optionline + ' '*self.spacing
			result.append(line)
		return result

mainmenu = Menu()
mainmenu_quit = MenuOption('quit', 'Exit Program')
mainmenu_newgame = MenuOption('newgame', 'Restart Game')
mainmenu_quit.set_next(up=0, down=0)
mainmenu_newgame.set_next(up=1, down=1)
mainmenu.set_options(mainmenu_newgame, '\n', mainmenu_quit)
mainmenu.reset()

def print_mainmenu(stdscr):
	result = mainmenu.print() # only need to refresh this on input
	y_off = 0
	for line in result:
		stdscr.addstr(5+y_off, 2, line)
		y_off += 1

def main():
	stdscr = init_curses()

	pinput = 0

	while(pinput != ord('q')):
		# input
		pinput = stdscr.getch()

		# handle input

		# draw
		stdscr.clear()

		stdscr.addstr(1, 2, 'test')
		print_mainmenu(stdscr)

		stdscr.refresh()

	else:
		end_curses(stdscr)


if __name__ == '__main__':
	main()