#!/usr/bin/env python
#
#	 impulse-cli modified from impulse by Lukas Vacek lucas.vacek@gmail.com
#
#	 Original impulse:
#+   Copyright (c) 2009 Ian Halpern
#@   http://impulse.ian-halpern.com
#
#    This file is part of Impulse.
#
#    Impulse is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Impulse is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Impulse.  If not, see <http://www.gnu.org/licenses/>.


import os, sys
from time import sleep
from subprocess import call
try:
	import curses
	import _curses
except ImportError:
	curses = None
import impulse

def draw_cli(peak_heights):
	print( chr(27) + "[2J" ) # clear screen
	for i,height in enumerate(peak_heights):
		print ( "%02d: %s" % (i+1,'|'*int(height)) )

# mode: where and how to draw
#	(type, x-pos, y-pos)
#	type can be either 'vertical' or 'horizontal'
#		'horizontal' supports any combination of:
#			x-pos: 'left','right,'center'
#			y-pos: 'top', 'bottom'
#		'vertical' supports:
#			x-pos: 'center'
#			y-pos: 'top', 'bottom'
#	example: ('horizontal','center','top')
def draw_curses(stdscr,peak_heights,mode):
	stdscr.clear()
	screen_size = stdscr.getmaxyx()
	maxy,maxx = screen_size
	for i,height in enumerate(peak_heights):
		if height > maxx-5:
			height = maxx-5
		try:
			if mode[0] == 'horizontal':
				draw_horizontal_column(stdscr,screen_size,mode,i,height)
			else:	
				draw_vertical_column(stdscr,screen_size,mode,i,height)
		except _curses.error:
			# if the terminal window is resized, we need to recalculate
			# maxx and all - so just return and do it next time round
			return
	stdscr.refresh()

# used by draw_curses - draw one horizontal column
def draw_horizontal_column(stdscr,screen_size,mode,i,height):
	maxy,maxx = screen_size
	column = '|'*int(height)
	# mode dependent
	if mode[1] == "right":
		column += " :%02d" % (i+1)
		startx = maxx - len(column) -1 # -1 because of cursor
	elif mode[1] == "left":
		column = "%02d: " % (i+1) + column
		startx = 0
	elif mode[1] == "center":
		startx = maxx/2 - len(column)/2

	if mode[2] == 'top':
		starty = 0
	else:
		starty = maxy-32
	#
	stdscr.addstr(i+starty,startx,column)

# used by draw_curses - draw one vertical column
def draw_vertical_column(stdscr,screen_size,mode,i,height):
	maxy,maxx = screen_size
	height = int(height)
	startx = maxx/2 - 32
	if mode[2] == "top":
		starty = 0
	if mode[2] == "bottom":
		starty = maxy - height
	for j in range(0,height):
		stdscr.addstr(starty+j,startx+(i*2),"##")

def get_mode_curses(stdscr,curr_mode):
	curr_mode = list(curr_mode) # make it modifiable ..
	key = stdscr.getch()

	if key == curses.KEY_LEFT:
		# vertical doesnt support x-axis movements
		if curr_mode[0] != "vertical":
			if curr_mode[1] == "right":
				curr_mode[1] = "center"
			else:
				curr_mode[1] = "left"
	elif key == curses.KEY_RIGHT:
		# vertical doesnt support x-axis movements
		if curr_mode[0] != "vertical":
			if curr_mode[1] == "left":
				curr_mode[1] = "center"
			else:
				curr_mode[1] = "right"

	elif key == curses.KEY_UP:
		if curr_mode[2] == "bottom":
			curr_mode[2] = "top"
	elif key == curses.KEY_DOWN:
		if curr_mode[2] == "top":
			curr_mode[2] = "bottom"

	elif key == ord(" "):
		if curr_mode[0] == "vertical":
			curr_mode[0] = 'horizontal'
		elif curr_mode[0] == "horizontal":
			curr_mode[0] = 'vertical'
			curr_mode[1] = 'center'
	return tuple(curr_mode) # .. and return as a tuple
	
def calc_heights(peak_heights,max_size):
	ffted_array = impulse.getSnapshot( True ) # True = use fft

	l = len( ffted_array ) / 4

	# start drawing spectrum
	n_bars = 32

	# no idea what this does - just taken from impulse :-)
	for i in range( 1, l, l / n_bars ):
		peak_index = int( ( i - 1 ) / ( l / n_bars ) )

		bar_amp_norm = ffted_array[ i ]
		bar_height = bar_amp_norm * max_size

		if bar_height > peak_heights[ peak_index ]:
			peak_heights[ peak_index ] = bar_height
		else:
			peak_heights[ peak_index ] -= int(max_size/20)

		if peak_heights[ peak_index ] < 0:
			peak_heights[ peak_index ] = 0

def main(args):
	index = args.source
	impulse.setSourceIndex( index )

	peak_heights = [ 0 for i in range( 32 ) ]
	if curses:
		try:
			stdscr = curses.initscr()
			curses.noecho()
			curses.cbreak()
			curses.curs_set(0)
			stdscr.keypad(1)
			stdscr.nodelay(1) # make getch non-blocking

			draw_mode = ('horizontal','left','top') # default mode for draw_curses
			while True:
				calc_heights(peak_heights,args.size)

				draw_mode = get_mode_curses(stdscr,draw_mode)

				draw_curses(stdscr,peak_heights,draw_mode)
				curses.napms(int(args.sleep*1000))

		finally:
			curses.nocbreak(); stdscr.keypad(0); curses.echo()
			curses.curs_set(1)
			curses.endwin()
	else:
		while True:
			calc_heights(peak_heights,args.size)
			draw_cli(peak_heights)
			sleep(args.sleep)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description="pulse audio command line visualizer\n"+
		"(curses interface controls: arrow keys,space bar)")
	parser.add_argument("-s","--source",type=int,default=0,
		help="source to visualize (default: 0)")
	parser.add_argument("-t","--sleep",type=float,default=0.05,
		help="refresh every n seconds (default 0.05)")
	parser.add_argument("-x","--size",type=int,default=70,
		help="max size of a column in characters (default 70)")
	parser.add_argument("-n","--no-curses",action='store_true',
		help="don't use curses interface")

	print('\n') # seperate impulse init message from args help
	args = parser.parse_args()

	if args.no_curses:
		curses = None

	main( args )
