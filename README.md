# x10_rest

REST interface to control X10 devices for Home Automation.

Aim of this project is to hook up https://home-assistant.io/components/switch.rest/ to a CM17A, serial Firecracker X10 unit.

Other X10 device controllers could be supported by making calls to Mochad (and/or https://bitbucket.org/clach04/mochad_firecracker/) instead.

NOTE by default this accepts all remote connections, without any authentication or authorization checks. It is recommended that this only listen and accept connections from localhost!

Implemented in pure Python. Known to work with Python 2.7.

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
