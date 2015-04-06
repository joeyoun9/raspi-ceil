raspi-ceil
==========

Simple code for connecting to and recoring messages from a ceilometer using a raspberry pi and a usb to rs232 connector.

Set the connection settings for your ceilometer (noting that this may not work perfectly if you have mulitple USB peripherals connected)

Must have a ceil.conf file in the same directory the code runs from

How To Run
==========

It is recommended you add an entry in your crontab to call the script frequently

  * * * * * python raspi_ceil.py > /dev/null 2>&1

This way it will constantly be called, and the script is able to know when another version is running.
