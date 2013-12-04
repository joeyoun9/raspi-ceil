#!/usr/bin/env python

import serial
import time
import datetime
import logging as lg
import os
import sys



BAUDRATE = 2400  # I have no idea where this number came from..., baud rate is 300 for the instrument, up to 1200 on demand...
BYTESIZE = 7  # I assume this is 8-bit with 1 start bit means 8-1 = 7... again, no idea here...
BOM = chr(002)  # beginning of message chr(001) for CL-31
EOM = chr(003)  # end of message chr(004) for CL-31
PORT = 0  # change this if you know port ttyUSB0 is taken
FILESTR = "ceil"  # unique string for the filename that will be saved

LOCATION = "/home/pi/"  # where the codes and data are located. If you change this, change the cron too!
DELAY = .5  # how long to wait between polling - larger delay reduces the number of iterations made





"""
THAT SHOULD BE THE END OF THINGS THAT NEED CUSTOMIZING

THE FOLLOWING IS THE FUNCTION CALLED WHEN A NEW DATA MESSAGE IS RECEIVED
THIS WILL FIRST SAVE THE DATA WITH A TIMESTAMP. IT CAN THEN ATTEMPT TO
SEND DATA TO OUR SERVERS.
"""








def save(data):
    """
    THIS IS THE FUNCTION THAT RECEIVES A DATA MESSAGE AND SAVES IT LOCALLY
    AND THEN THE FUNCTION ATTEMPTS TO SEND THE DATA TO OUR SERVER AT MESO1
    VIA A SIMPLE PUSH COMMAND.
    """
    try:
        fh = open(LOCATION + 'data/{%Y%m%d}_{}.dat'.format(datetime.datetime.utcnow(), FILESTR), 'a')
        fh.write(str(time.time()))  # write the epoch time
        fh.write(data)
        fh.close()
    except:
        l.warning('DATA NOT SAVED')
    try:
        # this is where we send thed data to the internets!
        pass
    except:
        # well, it failed. no worries, the data should sill be safe
        pass



def main(BAUDRATE, BYTESIZE, BOM, EOM, PORT, FILESTR, LOCATION, DELAY, devmode=False):
    """
    The main loop for listening to a Vaisala ceilometer connected via USB
    
    """

    logfilename = LOCATION + "log/raspi-ceil.log"
    if devmode:
        logfilename = None
    lg.basicConfig(filename=logfilename, filemode='a',
                  format="%(asctime)s %(levelname)s: %(message)s", level=lg.DEBUG)






    # this block of code checks if there is already a process
    # running that is performing this task
    if os.path.exists(LOCATION + ".raspiceilpid"):
        # check it
        f = open(LOCATION + ".raspiceilpid", 'r')
        pid = f.read()
        f.close()
        try:
            #  os.kill sends a signal to a process, signal 0 ilicits no response, so this does not actually kill anything
            os.kill(int(pid), 0)
            print "Another listener is already running"
            if not devmode:
                exit()
            else:
                import signal
                print 'DEVMODE: killing current process'
                os.kill(int(pid), signal.SIGTERM)  # or SIGKILL or SIGABORT...
        except OSError:
            pass
        # ok, that process is not running, so continue

    else:
        # ok, well, that's the best I can do, continue
        pass

    f = open(LOCATION + "/.raspiceilpid", 'w')
    f.write(str(os.getpid()))
    f.close()
    lg.info('Beginning active data collection')
    if devmode:
        print "DEVMODE: no data being collected, all data printing to screen"

    ser = serial.Serial()
    ser.baudrate = BAUDRATE
    ser.bytesize = BYTESIZE



    # FIXME - UTILIZE THE LIST_PORTS.COMPORTS() TO GET IDS!
    # #ser.timeout=1
    port = PORT
    while port < 20:
        # loop through all likely ports...
        try:
            ser.port = '/dev/ttyUSB%i' % port
            if not os.path.exists(ser.port):
                port += 1
                continue
            ser.open()
            break  # try no more!
        except serial.serialutil.SerialException as e:
            print e
            port += 1
    if port == 20:
        l.warning('No valid USB serial port identified, aborting')
        exit()


    lg.info("Connected to a USB device on {}".format(ser.port))

    print """
    
        DEVMODE: PRINTING SERIAL DATA RECEIVED. 
        NOTE: GARBLED TEXT MEANS BAUD RATE AND/OR BYTE SIZE NOT ACCURATELY SPECIFIED 
    
    /////////////////////////////////////////////////////////////////////////////////
        
    """


    ob = ''
    while 1:
        time.sleep(DELAY)  # greatly reduce server load
        if ser.inWaiting() > 0:
            l = ser.read(ser.inWaiting())
            if devmode:
                print l
                continue
            ob += l
            # and then check if both begin and end control characters are present. if so, save the ob
            # WITH A TIMESTAMP!
            if BOM in ob and EOM in ob:
                save(ob)
                l.debug('Message received')
                ob = ''
            elif EOM in ob and not BOM in ob:
                # this means the recorder started in the middle of a message, save it
                save(ob)
                ob = ''


if __name__ == "__main__":

    # use keyword 'dev' to run the code in non-recording dev/verbose mode
    devmode = False
    if len(sys.argv) > 1 and sys.argv[1] == 'dev':
        devmode = True

    main(BAUDRATE, BYTESIZE, BOM, EOM, PORT, FILESTR, LOCATION, DELAY, devmode)
