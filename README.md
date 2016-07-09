# x10_rest

REST interface to control X10 devices for Home Automation.

### Table of Contents
* [Information](#information)
* [Getting Started](#getting-started)
* [Design notes](#design-notes)


## Information

Aim of this project is to hook up https://home-assistant.io/components/switch.rest/ to a CM17A, serial Firecracker X10 unit.

Other X10 device controllers could be supported by making calls to Mochad (and/or https://bitbucket.org/clach04/mochad_firecracker/) instead.

NOTE by default this accepts all remote connections, without any authentication or authorization checks. It is recommended that this only listen and accept connections from localhost!

Implemented in pure Python. Known to work with:

  * Python 2.7
  * Python 3.5

## Getting Started

To get started:

    pip install -r requirements.txt

And manually get an X10 library, example:

    wget https://bitbucket.org/cdelker/python-x10-firecracker-interface/raw/46b300343d3faa148e17479487581a28ebdfac0e/firecracker.py


### Permissions under Linux

Under Linux most users do not have serial port permissions,
either:

  * give user permission (e.g. add to group "dialout") - RECOMMENDED
  * run this demo as root - NOT recommended!

Giver user dialout (serial port) access:

    # NOTE requires logout/login to take effect
    sudo usermod -a -G dialout $USER

### Running

Start x10 rest server via:

    x10_rest.py SERIAL_PORT_NAME

Example, Windows:

    x10_rest.py COM5

Example, Linux:

    x10_rest.py /dev/ttyUSB0


### Configuration of Home Assistant

Edit `configuration.yaml`, sample additions:

    # https://home-assistant.io/components/switch.rest/
    # X10 switches via https://github.com/clach04/x10_rest
    switch:
      - platform: rest
        resource: http://localhost:1234/x10/C/6
        name: "C6 Switch"
      - platform: rest
        resource: http://localhost:1234/x10/C/5
        name: "C5 Switch"
      - platform: rest
        resource: http://localhost:1234/x10/C/4
        name: "C4 Switch"
      - platform: rest
        resource: http://localhost:1234/x10/C
        name: "C - all switches"

This will control house code C, units 4, 5, and 6.
  * All LAMP units in house C can be switched ON via all switches.
  * All units (not just LAMPS) in house C can be switched OFF via all switches.

NOTE CM17A Firecracker devices are controllers only, state can not be read so x10_rest emulates this as best it can. State can easily get out of sync with reality and so two presses may be required via HA.

See `gen_sample_config.py` for a quick way to generate config suitable for copy/paste and then editing.

## Design notes

Why another REST interface to x10?

  * All the ones at the time this was written did not supply a REST interface that https://home-assistant.io/components/switch.rest/ could use. Either the URL included the ON/OFF state or the REQUEST_METHOD was incompatible (e.g. PUT instead of GET/POST).

What's next?

  * Support other X10 interfaces/controllers
      * a bridge to another protocol like Mochad https://sourceforge.net/p/mochad (note mochad supports a limited number of controllers but https://bitbucket.org/clach04/mochad_firecracker/ supports an additional controller).
        E.g. see:
          * https://github.com/jpardobl/hautomation_x10 - known to work with https://bitbucket.org/clach04/mochad_firecracker/
          * https://github.com/mtreinish/pymochad
          * https://github.com/SensorFlare/mochad-python/blob/master/mochad_python.py
      * Using a different direct control module like https://github.com/glibersat/python-x10 - this module supports addition X10 controllers but the CM17A support does not work
