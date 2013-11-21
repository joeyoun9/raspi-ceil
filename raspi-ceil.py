#!/usr/bin/env python
import serial
import time
import os

BAUDRATE = 2400 # I have no idea where this number came from..., baud rate is 300 for the instrument, up to 1200 on demand...
BYTESIZE = 7
BOM = chr(002) # beginning of message
EOM = chr(003) # end of message

# THAT SHOULD BE THE END OF THINGS THAT NEED CUSTOMIZING

# this block of code checks if there is already a process
# running that is performing this task
if os.path.exists("./.ceilprocessid"):
	# check it
	f=open("./.ceilprocessid",'r')
	pid = f.read()
	f.close()
	try:
		os.kill(int(pid),0)
		print "Another listener is already running"
		exit()
	except OSError:
		pass
	# ok, that process is not running, so continue
	
else:
	# ok, well, that's the best I can do, continue
	pass

f=open("./.ceilprocessid",'w')
f.write(str(os.getpid()))
f.close()


ser = serial.Serial()
ser.port = '/dev/ttyUSB0'
ser.baudrate =  BAUDRATE
ser.bytesize = BYTESIZE

def save(data):
	print data
	fh = open('./arch.dat','a')
	fh.write(str(time.time())) # write the epoch time
	fh.write(data)
	fh.close()
	

##ser.timeout=1
ser.open()
ob = ''
while 1:
	time.sleep(1) # greatly reduce server load
	if ser.inWaiting() > 0:
		l= ser.read(ser.inWaiting())
		ob += l
		# and then check if both begin and end control characters are present. if so, save the ob
		# WITH A TIMESTAMP!
		if BOM in ob and EOM in ob:
			save(ob)
			ob = ''
		elif EOM in ob and not BOM in ob:
			# this means the recorder started in the middle of a message, save it
			save(ob)
			ob=''
