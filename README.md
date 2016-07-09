# x10_rest

REST interface to control X10 devices for Home Automation.

Aim of this project is to hook up https://home-assistant.io/components/switch.rest/ to a CM17A, serial Firecracker X10 unit.

Other X10 device controllers could be supported by making calls to Mochad (and/or https://bitbucket.org/clach04/mochad_firecracker/) instead.


Implemented in pure Python. Known to work with Python 2.7.

To get started:

    pip install -r requirements.txt

And manually get an X10 library, example:

    wget https://bitbucket.org/cdelker/python-x10-firecracker-interface/raw/46b300343d3faa148e17479487581a28ebdfac0e/firecracker.py


Permissions under Linux
=======================

Under Linux most users do not have serial port permissions,
either:

  * give user permission (e.g. add to group "dialout") - RECOMMENDED
  * run this demo as root - NOT recommended!

Giver user dialout (serial port) access:

    # NOTE requires logout/login to take effect
    sudo usermod -a -G dialout $USER

Start x10 rest server via:

    x10_rest.py SERIAL_PORT_NAME

Example, Windows:

    x10_rest.py COM5

Example, Linux:

    x10_rest.py /dev/ttyUSB0

