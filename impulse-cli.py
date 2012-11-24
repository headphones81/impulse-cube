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
import impulse

def draw_cli(peak_heights):
	ffted_array = impulse.getSnapshot( True ) # True = use fft

	l = len( ffted_array ) / 4

	# start drawing spectrum
	n_bars = 32

	print( chr(27) + "[2J" ) # clear screen
	for i in range( 1, l, l / n_bars ):
		peak_index = int( ( i - 1 ) / ( l / n_bars ) )

		bar_amp_norm = ffted_array[ i ]
		bar_height = bar_amp_norm * 100

		if bar_height > peak_heights[ peak_index ]:
			peak_heights[ peak_index ] = bar_height
		else:
			peak_heights[ peak_index ] -= 5

		if peak_heights[ peak_index ] < 0:
			peak_heights[ peak_index ] = 0

		print ( "%02d: %s" % (peak_index+1,'|'*int(bar_height) ) )

def main(args):
	index = args.source
	impulse.setSourceIndex( index )

	peak_heights = [ 0 for i in range( 32 ) ]
	while True:
		draw_cli(peak_heights)
		sleep(args.sleep)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser("pulse audio command line visualizer")
	parser.add_argument("-s","--source",type=int,default=0)
	parser.add_argument("-t","--sleep",type=float,default=0.05)

	args = parser.parse_args()
	main( args )
