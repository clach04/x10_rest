# x10_rest

REST interface to control X10 devices for Home Automation.

### Table of Contents
* [Information](#information)
* [Getting Started](#getting-started)
* [Design notes](#design-notes)


## Information

Aim of this project is to hook up https://home-assistant.io/components/switch.rest/ to a CM17A, serial Firecracker X10 unit.

Other X10 device controllers could be supported by making calls to Mochad (and/or https://hg.sr.ht/~clach04/mochad_firecracker/) instead.

NOTE by default this accepts all remote connections, without any authentication or authorization checks. It is recommended that this only listen and accept connections from localhost!

Implemented in pure Python. Known to work with:

  * Python 2.7
  * Python 3.5

## Getting Started

To get started:

    pip install -r requirements.txt


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

    # CM17A Firecracker
    x10_rest.py SERIAL_PORT_NAME

    # Mochad server (localhost on default port)
    x10_rest.py -m

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


### REST interface


REST interface implemented is completely influenced by
https://home-assistant.io/components/switch.rest/ behavior
so only ON and OFF is supported.

URL form:

    /x10/{house code}/{optional_unit_number}

if `{optional_unit_number}` is omitted means all units in `{house code}`.

Examples:

  * /x10/A
  * /x10/A/1
  * /x10/A/2
  * /x10/B/1
  * ...

#### Demo

    > curl http://localhost:1234/x10/C/4
    OFF
    > curl --data ON http://localhost:1234/x10/C/4

    > curl http://localhost:1234/x10/C/4
    ON
    > curl --data OFF http://localhost:1234/x10/C/4


### Notes

Why another REST interface to x10?

  * All the ones at the time this was written did not supply a REST interface that https://home-assistant.io/components/switch.rest/ could use. Either the URL included the ON/OFF state or the REQUEST_METHOD was incompatible (e.g. PUT instead of GET/POST).

Also see x10_demoweb.py - non REST api, GET with side effects and GET (with side effects) simple web application, behaves like an X10 big remote.

What's next?

  * Support other X10 interfaces/controllers?
  * Remove the need for this and implement X10 support as a
    [Home Assistant Component](https://home-assistant.io/components). See https://github.com/clach04/home-assistant-x10
