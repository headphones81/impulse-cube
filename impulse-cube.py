#!/usr/bin/env python

import sys, os, time, copy
import argparse
curr_dir = os.path.dirname( os.path.abspath(__file__) )
sys.path.insert(0,os.path.join(curr_dir,"deps/pyudev"))

# Bundled dependecies:
# pyudev (pure python)
# To update: 
#    just download new pyudev package from https://pypi.python.org/pypi/pyudev,
#    unpack in deps and change pyudev symlink to point to the new directory

import pyudev
try:
    import serial # external dep: pyserial; in Ubuntu: apt-get install python-serial
    from serial.serialutil import SerialException
except ImportError:
    print "please install python-serial (on Debian/Ubuntu: apt-get install python-serial)\n"
    raise
try:
    import impulse
except ImportError:
    print "Impulse module not found! Please read \"README\" for installation instructions\n"
    raise

#
# impulse stuff
#

def heights_to_leds(h):
    # h (heights) - a list of 6 heights (number between 0 and 6)
    # returns a set of tuples of 3 elements (led coordinates - side, led number, color)

    leds = set()
    # side 1 
    if h[0] >= 1:
        leds.add( (1,2,2) )
    if h[0] >= 2:
        leds.add( (1,5,2) )
    if h[0] >= 3:
        leds.add( (1,8,2) )
    if h[0] >= 4:
        leds.add( (5,6,2) )
    if h[0] >= 5:
        leds.add( (5,3,2) )

    if h[1] >= 1:
        leds.add( (1,1,2) )
    if h[1] >= 2:
        leds.add( (1,4,2) )
    if h[1] >= 3:
        leds.add( (1,7,2) )
    if h[1] >= 4:
        leds.add( (5,7,2) )
    if h[1] >= 5:
        leds.add( (5,4,2) )

    if h[2] >= 1:
        leds.add( (1,0,2) )
    if h[2] >= 2:
        leds.add( (1,3,2) )
    if h[2] >= 3:
        leds.add( (1,6,2) )
    if h[2] >= 4:
        leds.add( (5,8,2) )
    if h[2] >= 5:
        leds.add( (5,5,2) )

    # side 2 
    if h[3] >= 1:
        leds.add( (3,2,0) )
    if h[3] >= 2:
        leds.add( (3,5,0) )
    if h[3] >= 3:
        leds.add( (3,8,0) )
    if h[3] >= 4:
        leds.add( (5,8,0) )
    if h[3] >= 5:
        leds.add( (5,7,0) )

    if h[4] >= 1:
        leds.add( (3,1,0) )
    if h[4] >= 2:
        leds.add( (3,4,0) )
    if h[4] >= 3:
        leds.add( (3,7,0) )
    if h[4] >= 4:
        leds.add( (5,5,0) )
    if h[4] >= 5:
        leds.add( (5,4,0) )

    if h[5] >= 1:
        leds.add( (3,0,0) )
    if h[5] >= 2:
        leds.add( (3,3,0) )
    if h[5] >= 3:
        leds.add( (3,6,0) )
    if h[5] >= 4:
        leds.add( (5,2,0) )
    if h[5] >= 5:
        leds.add( (5,1,0) )

    return leds

def calc_heights(peak_heights,max_size,factor=1):
	ffted_array = impulse.getSnapshot( True ) # True = use fft

	l = len( ffted_array ) / 4

	n_bars = len(peak_heights)

	lower_by = int(max_size / 15)
	if lower_by < 1:
		lower_by = 1

	for i in range(0, n_bars):
		fft_index = i * (l / n_bars)
		bar_height = ffted_array[fft_index] * max_size * factor

		if bar_height >= peak_heights[ i ]:
			pass
		else:
			bar_height = peak_heights[i] - lower_by

		if bar_height < 0:
			bar_height = 0

		if bar_height > max_size:
			bar_height = max_size

		peak_heights[i] = bar_height

#
#
#

SERIAL_TIMEOUT = 0.2

CUBE_INIT = 0
CUBE_READY = 1
CUBE_DEAD = 2

# contains all Cube objects
CUBES = set()

# Bit of abstraction for Futuro Cube protocol on top of serial.Serial
class Cube(object):
    def __init__(self,dev):
        self.dev = dev
        self.state = CUBE_INIT
        self.serial = None
        while True:
            try:
                self.serial = serial.Serial(port=self.dev, timeout=SERIAL_TIMEOUT)
                break
            except SerialException as ex:
                if "resource busy" in ex.args[0]:
                    print("SerialException: %s - retrying in 5s" % ex.args[0])
                    time.sleep(5)
                else:
                    print("SerialException: %s - removing cube" % ex.args[0])
                    self.state = CUBE_DEAD
                    break
        if self.serial is not None:
            self.prep_cube()

    def build_packet(self,cmd):
        import struct
        sep = "\x00"
        data = cmd+"\r\n"
        length = struct.pack(">H",len(data)+1)
        crc = 0
        for x in data:
            crc += ord(x)
        crc = chr(crc & 0xff)
        return "SQ"+length+sep+data+crc+"q"+sep+"s"

    def prep_cube(self):
        try:
            self.write_direct("ver\r\n",True)
            self.write_direct("mplex\r\n",True)
            self.write("keepbootactive",True)
            self.write("__test_init__",True)
            self.write("echooff",True)
            self.write("promptoff",True)
            self.state = CUBE_READY
        except (SerialException, IOError, OSError):
            self.state = CUBE_DEAD

    def write_direct(self,cmd,wait=False):
        try:
            self.serial.write(cmd)
            if wait:
                self.serial.read()
        except (SerialException, IOError, OSError):
            self.state = CUBE_DEAD

    def write(self,cmd,wait=False):
        try:
            self.serial.write( self.build_packet(cmd) )
            if wait:
                self.serial.read()
        except (SerialException, IOError, OSError):
            self.state = CUBE_DEAD

    def clear(self):
        try:
            self.write("clr",True)
        except (SerialException, IOError, OSError):
            self.state = CUBE_DEAD

def callback(action, device):
    if "FUTURO_CUBE" in device.get("ID_SERIAL",""):
        #action: add, already_connected, remove
        # we don't have to handle remove - if cube has been removed, 'write' fails
        # exception is caught and state is change to CUBE_DEAD, main thread then removes
        # the Cube object from CUBES
        if action == "add" or action == "already_connected":
            CUBES.add( Cube(device.device_node) )

parser = argparse.ArgumentParser(description="Visualize audio from pulse-audio on Futuro Cube connected via USB")

parser.add_argument("-t", "--time-refresh", default=0.05, 
                    type=float, help="Sleep before cube refresh")
parser.add_argument("-f", "--factor", default=10,
                    type=float, help="Multiply audio volumes coming form pulse audio by this factor")
parser.add_argument("-s", "--source", default=0,
                    type=int, help="Pulse audio source to process")

args = parser.parse_args()

impulse.setSourceIndex( args.source )

context = pyudev.Context()
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by('tty')
observer = pyudev.MonitorObserver(monitor, callback)
observer.start()

# and get the already connected ones
for dev in context.list_devices(subsystem="tty"):
    callback("already_connected",dev)

# main loop
to_be_removed = []
peak_heights = [ 0 for i in range( 6 ) ]
prev_leds = set()
try:
    while True:
        # we are printing on a 6 by 5 grid
        # factor (multiple all numbers in peak_height by this number)
        calc_heights(peak_heights,5,args.factor)
        leds = heights_to_leds(peak_heights)

        for c in CUBES:
            if c.state == CUBE_DEAD:
                to_be_removed.append(c)
            elif c.state == CUBE_READY:
                for led in prev_leds:
                    if led not in leds:
                        # light down
                        side, index, color = led
                        c.write('pled %d %d %d %d' % (side,index,color,0))

                for led in leds:
                    if led not in prev_leds:
                        # light up
                        side, index, color = led
                        c.write('pled %d %d %d %d' % (side,index,color,250))

        prev_leds = copy.copy(leds)

        if to_be_removed:
            for c in to_be_removed:
                print("%s - removed" % c.dev)
                CUBES.remove(c)
            to_be_removed = []

        time.sleep(args.time_refresh)
finally:
    for c in CUBES:
        if c.state != CUBE_DEAD:
            try:
                c.clear()
            except:
                pass
