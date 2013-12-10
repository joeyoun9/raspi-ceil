#!/usr/bin/env python

import serial
import time
import datetime
import logging as lg
import os
import sys
import signal



BAUDRATE = 9600  # 2400  # I have no idea where this number came from..., baud rate is 300 for the instrument, up to 1200 on demand...
BYTESIZE = 7  # I assume this is 8-bit with 1 start bit means 8-1 = 7... again, no idea here...
BOM = chr(001)  # chr(002)  # beginning of message chr(001) for CL-31
EOM = chr(004)  # chr(003)  # end of message chr(004) for CL-31
PORT = 0  # change this if you know port ttyUSB0 is taken
FILESTR = "ceil"  # unique string for the filename that will be saved

LOCATION = "/home/pi/"  # where the codes and data are located. If you change this, change the cron too!
DELAY = .5  # how long to wait between polling - larger delay reduces the number of iterations made (thus the load on the RPI)





"""
THAT SHOULD BE THE END OF THINGS THAT NEED CUSTOMIZING

THE FOLLOWING IS THE FUNCTION CALLED WHEN A NEW DATA MESSAGE IS RECEIVED
THIS WILL FIRST SAVE THE DATA WITH A TIMESTAMP. IT CAN THEN ATTEMPT TO
SEND DATA TO OUR SERVERS.
"""








def save(data, LOCATION, FILESTR):
    """
    THIS IS THE FUNCTION THAT RECEIVES A DATA MESSAGE AND SAVES IT LOCALLY
    AND THEN THE FUNCTION ATTEMPTS TO SEND THE DATA TO OUR SERVER AT MESO1
    VIA A SIMPLE PUSH COMMAND.
    """
    
    save_name = '{:%Y%m%d}_{}.dat'.format(datetime.datetime.utcnow(),FILESTR)
    save_location = LOCATION + 'data/'+save_name
    try:
        fh = open(save_location, 'a')
        fh.write(str(time.time()) + "\n")  # write the epoch time
        fh.write(data)
        fh.close()
    except:
        lg.warning('DATA NOT SAVED' + str(sys.exc_info()))
    try:
        # this is where we send thed data to the internets!
        pass
    except:
        # well, it failed. no worries, the data should sill be safe
        pass
    try:
        temp_file_name = os.listdir(LOCATION+"data/temp/")[0]
    except IndexError:
        temp_file_name = ""
    if not save_name == temp_file_name:
        # remove the old temp file, and copy in this one
        os.system('rm '+LOCATION+"data/temp/"+temp_file_name)
        os.system('cp '+save_location+" "+LOCATION+"data/temp/"+save_name)
    


def testproc(proc):
    try:
        os.kill(int(proc), 0)
        return True  # yes, process is running
    except:
        # hopefully this is not an os error
        return False

def killproc(proc):
    if testproc(proc):
        os.kill(int(proc), signal.SIGTERM)  # or SIGKILL or SIGABORT...
    return

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
        if devmode:
            killproc(pid)
        elif testproc(pid):
             print "Another listener is already running"  # useless considering nobody watches this
             exit()
    else:
        # ok, well, that's the best I can do, continue
        pass

    f = open(LOCATION + ".raspiceilpid", 'w')
    f.write(str(os.getpid()))
    f.close()
    lg.info('Starting ceilometer listener process... looking for a connection')
    if devmode:
        lg.warning("DEVMODE: no data being collected, all data printing to screen")

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
        lg.warning('No valid USB serial port identified, aborting')
        exit()


    lg.info("Connected to a USB device on {}".format(ser.port))

    if devmode:
        print """
        
            DEVMODE: PRINTING SERIAL DATA RECEIVED. 
            NOTE: GARBLED TEXT MEANS BAUD RATE AND/OR BYTE SIZE NOT ACCURATELY SPECIFIED 
        
        /////////////////////////////////////////////////////////////////////////////////
            
        """


    ob = ''
    while 1:
        time.sleep(DELAY)  # greatly reduce server load
        if ser.inWaiting() > 0:
            st = ser.read(ser.inWaiting())
            if devmode:
                print st
                continue
            ob += st
            # and then check if both begin and end control characters are present. if so, save the ob
            # WITH A TIMESTAMP!
            if BOM in ob and EOM in ob:
                save(ob, LOCATION, FILESTR)
                lg.debug('Message received')
                ob = ''
            elif EOM in ob and not BOM in ob:
                # this means the recorder started in the middle of a message, save it
                save(ob, LOCATION, FILESTR)
                ob = ''


if __name__ == "__main__":

    # use keyword 'dev' to run the code in non-recording dev/verbose mode
    devmode = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dev':
            devmode = True
        elif sys.argv[1] == 'update':
            # grab the newest version of this file from github, and replace this one
            # assuming this is running in the directory where this file is, which, is necessary
            if os.path.exists(LOCATION + ".raspiceilpid"):
                # check it
                f = open(LOCATION + ".raspiceilpid", 'r')
                pid = f.read()
                f.close()
                killproc(pid)
            # ok, we have killed the old one
            os.system('wget https://raw.github.com/joeyoun9/raspi-ceil/master/raspi-ceil.py')
            if os.path.exists('./raspi-ceil.py.1'):
                os.system('rm raspi-ceil.py')
                os.system('mv raspi-ceil.py.1 raspi-ceil.py')
            print "RASPI-CEIL SOFTWARE UPDATED FROM GITHUB"
            exit()

    main(BAUDRATE, BYTESIZE, BOM, EOM, PORT, FILESTR, LOCATION, DELAY, devmode)
