import curses
from enum import IntEnum
from menu import load_menus, MenuEnum

def init_curses():
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)
	stdscr.keypad(True)
	stdscr.nodelay(True)
	return stdscr

def end_curses(stdscr):
	curses.nocbreak()
	stdscr.keypad(False)
	curses.echo()
	curses.endwin()

class GameData:
	def __init__(self):
		pass

	def reset(self):
		pass

def main():
	stdscr = init_curses()
	game_win = curses.newwin(stdscr.getmaxyx()[0]-4, 40, 2, 1)
	debug_win = curses.newwin(2, 40, 0, 1)

	gamedata = GameData()

	menus = load_menus()
	curr_menu = MenuEnum.MAIN

	pinput = 0
	quit = False

	while(1):
		# input
		pinput = stdscr.getch()

		# handle input
		quit, new_menu, debug = menus[curr_menu].handle_input(pinput, gamedata)
		if (quit):
			break
		if (new_menu != None):
			curr_menu = new_menu
		if (len(debug) > 0):
			debug_win.clear()
			debug_win.addstr(0, 0, debug)
			debug_win.refresh()

		# draw
		game_win.clear()

		game_win.addstr(5, 1, menus[curr_menu].print())

		game_win.refresh()

	else:
		end_curses(stdscr)


if __name__ == '__main__':
	main()