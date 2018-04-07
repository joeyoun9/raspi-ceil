raspi-ceil
==========

Simple code for connecting to and recoring messages from a ceilometer using a raspberry pi and a usb to rs232 connector.

Set the connection settings for your ceilometer (noting that this may not work perfectly if you have mulitple USB peripherals connected)

Must have a ceil.conf file in the same directory the code runs from. Requires PySerial to be installed, which should be doable with 
* `pip install pyserial`
* OR `sudo apt-get install python-serial` (might work better on the pi)

How To Run
----------

you should have a /data/ direcory in the directory raspi_ceil.py runs in. For simplicity this should just be your home directory, with ~/data/

It is recommended you add an entry in your crontab to call the script frequently

`* * * * * python raspi-ceil.py > /dev/null 2>&1`

This way it will constantly be called, and the script is able to know when another version is running.

How to manually run
-------------------
Test performance, even with the crontab configured, by running with the debug flag

`python raspi-ceil.py dev`

This will force the script to kill any other versions running, and it will dump the output to the screen, so you can see if your connection settings are correct. If they are bad, you will just see jarbled text come out when the ceilometer should be reporting. 

Updating
--------
The script is able to update itself, with a simple  terminal update flag.

run `python raspi_ceil.py update` and it will download a new version of itself, kill the old, and start.

