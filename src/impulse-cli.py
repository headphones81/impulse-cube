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

def draw_curses(stdscr,peak_heights):
	stdscr.clear()
	maxy,maxx = stdscr.getmaxyx()
	for i,height in enumerate(peak_heights):
		if height > maxx-5:
			height = maxx-5
		column = '|'*int(height)
		column += " :%02d" % (i+1)
		startx = maxx - len(column) -1 # -1 because of cursor
		try:
			stdscr.addstr(i,startx,column)
		except _curses.error:
			# if the terminal window is resized, we need to recalculate
			# maxx and all - so just return and do it next time round
			return
		stdscr.refresh()

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

			while True:
				calc_heights(peak_heights,args.size)
				draw_curses(stdscr,peak_heights)
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
