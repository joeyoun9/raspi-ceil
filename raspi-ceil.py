#!/usr/bin/env python

import serial
import time
import datetime
import logging as lg
import os
import sys
import signal
import gzip



"""
THAT SHOULD BE THE END OF THINGS THAT NEED CUSTOMIZING

THE FOLLOWING IS THE FUNCTION CALLED WHEN A NEW DATA MESSAGE IS RECEIVED
THIS WILL FIRST SAVE THE DATA WITH A TIMESTAMP. IT CAN THEN ATTEMPT TO
SEND DATA TO OUR SERVERS.
"""



def read_config(config):
    """
    read a simple config file, and set the attributes for operation
    
    default filename is ceil.conf, and is in the local directory. 
    """
    selections = {
              "BAUDRATE":9600,
              "BYTESIZE":7,
              "BOM":1,
              "EOM":4,
              "PORT":0,
              "FILESTR":"UUCL1",
              "DATEFMT":"%Y%m%d"
              "LOCATION":"/home/pi",
              "DELAY":.5

              }
    try:
        f = open("ceil.conf", 'r')
    except IOError:
        return selections

    for line in f:
        p = line.split(":")
        if p[0].strip() in selections.keys():
            selections[p[0].strip()] = p[1].strip()
    f.close()
    return selections





def save(data, LOCATION, FILESTR, DATEFMT):
    """
    THIS IS THE FUNCTION THAT RECEIVES A DATA MESSAGE AND SAVES IT LOCALLY
    AND THEN THE FUNCTION ATTEMPTS TO SEND THE DATA TO OUR SERVER AT MESO1
    VIA A SIMPLE PUSH COMMAND.
    """

    save_name = '{fid}.{dt:'+DATEFMT+'}.dat.gz'.format{dt=datetime.datetime.utcnow(), fid=FILESTR)

    save_location = LOCATION + 'data/' + save_name
    try:
        with gzip.open(save_location, 'a') as fh:
             fh.write("\n" + str(time.time()) + "\n")  # write the epoch time
             fh.write(data)
    except:
        lg.warning('DATA NOT SAVED' + str(sys.exc_info()))

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

def main(BAUDRATE, BYTESIZE, BOM, EOM, PORT, FILESTR, LOCATION, DATEFMT, DELAY, devmode=False):
    """
    The main loop for listening to a Vaisala ceilometer connected via USB
    
    """

    logfilename = LOCATION + "log/raspi-ceil.log"
    if devmode:
        logfilename = None
    lg.basicConfig(filename=logfilename, filemode='a',
                  format="%(asctime)s %(levelname)s: %(message)s", level=lg.INFO)






    # this block of code checks if there is already a process
    # running that is performing this task
    process_file_name = LOCATION + ".raspiceilpid" + FILESTR

    if os.path.exists(process_file_name):
        # check it
        f = open(process_file_name, 'r')
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

    f = open(process_file_name, 'w')
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
        
            DEVMODE: PRINTING SERIAL DATA RECEIVED. (data may still be getting recorded)
            NOTE: GARBLED TEXT MEANS BAUD RATE AND/OR BYTE SIZE NOT ACCURATELY SPECIFIED 
        
        /////////////////////////////////////////////////////////////////////////////////
            
        """


    ob = ''
    while 1:
        ln = ser.readline()
        time.sleep(DELAY)  # greatly reduce server load
        if not ln:
            continue
        if devmode:
            print ln,
            #continue
        ob += ln
        # and then check if both begin and end control characters are present. if so, save the ob
        # WITH A TIMESTAMP!
        if BOM in ob and EOM in ob:
            ob = ob[ob.find(BOM):ob.find(EOM) + 1]  # remove any rogue newlines
            save(ob, LOCATION, FILESTR, DATEFMT)
            lg.debug('Message received')
            ob = ''
        elif EOM in ob and not BOM in ob:
            # this means the recorder started in the middle of a message, save it
            save(ob, LOCATION, FILESTR, DATEFMT)
            ob = ''


if __name__ == "__main__":

    # use keyword 'dev' to run the code in non-recording dev/verbose mode
    devmode = False
    config_file = "./ceil.conf"
    arglen = len(sys.argv)
    #
    #	Handle any arguments passed
    #
    if arglen > 1:
        if sys.argv[1] == 'dev':
            devmode = True
        elif sys.argv[1] == 'update':
            # grab the newest version of this file from github, and replace this one
            # assuming this is running in the directory where this file is, which, is necessary
            if os.path.exists(LOCATION + ".raspiceilpid" + FILESTR):
                # check it
                f = open(LOCATION + ".raspiceilpid" + FILESTR, 'r')
                pid = f.read()
                f.close()
                killproc(pid)
            # ok, we have killed the old one
            os.system('wget https://raw.github.com/joeyoun9/raspi-ceil/master/raspi-ceil.py')
            if os.path.exists('./raspi-ceil.py.1'):
                os.system('rm raspi-ceil.py')
                os.system('mv raspi-ceil.py.1 raspi-ceil.py')
            print "restarting with the new version"
            if arglen > 2:
                # the second parameter is the location of the config file
                os.system("python raspi-ceil.py restart {} &".format(sys.argv[2]))
            else:
                os.system('python raspi-ceil.py restart &')

            print "RASPI-CEIL SOFTWARE UPDATED FROM GITHUB"
            exit()
        elif sys.argv[1] == 'restart':
            if os.path.exists(LOCATION + ".raspiceilpid" + FILESTR):
                # check it
                f = open(LOCATION + ".raspiceilpid" + FILESTR, 'r')
                pid = f.read()
                f.close()
                killproc(pid)
            if arglen > 2:
                # then a config file was passed, read it!
                config_file = sys.argv[2]
        else:
            # then the first argument was the config file!
            config_file = sys.argv[1]

    settings = read_config(config_file)
    BAUDRATE = int(settings['BAUDRATE'])
    BYTESIZE = int(settings['BYTESIZE'])
    BOM = chr(int(settings['BOM']))
    EOM = chr(int(settings['EOM']))
    PORT = int(settings['PORT'])
    FILESTR = settings['FILESTR']
    LOCATION = settings['LOCATION']
    DATEFMT = settings['DATEFMT']
    if not LOCATION[-1] == "/": LOCATION += "/"
    DELAY = float(settings['DELAY'])


    main(BAUDRATE, BYTESIZE, BOM, EOM, PORT, FILESTR, LOCATION, DATEFMT, DELAY, devmode)
