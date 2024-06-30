#!/usr/bin/env python
## based on https://hg.sr.ht/~clach04/x10_demoweb/browse/x10_demoweb.py?rev=tip ?
## but with x10_any
# Python 3.x and 2.x
# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# x10_demoweb.py - Simple X10 web controller demo
# Copyright (C) 2014  Chris Clark
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""Trivial working web demo for CM17A (Firecracker) X10 serial unit

Uses https://bitbucket.org/cdelker/python-x10-firecracker-interface/
or http://www.averdevelopment.com/python/x10.html

Uses WSGI, see http://docs.python.org/library/wsgiref.html
"""


import logging
import os
import sys
import platform
try:
    # py2 (and <py3.8)
    from cgi import parse_qs
except ImportError:
    # py3
    from urllib.parse import parse_qs

from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server


import x10_any


logging.basicConfig()
default_logger = logging.getLogger(__name__)

# serial port name for CM17A aka Firecracker
default_serial_port_name = '/dev/ttyUSB0'  # Example Linux USB serial adapter
default_serial_port_name = 'com5'  # Windows serial port

serial_port_name = default_serial_port_name

# Hard code http port for web server
server_port = 8777


# Dumb hard coded "template"
html = """<html>
  <head>
<style type="text/css">
body {width:100%;height:100%;}
.com {height:100px; width:49%;font-size:28px}
.zone {}
.coms {width:100%;}
.zones {width:100%;}
table{cellpadding:0px;cellspacing:0px;border:0px;}
</style>
  </head>
  <body>
    <form method="post">
    <table class="zones"><tr>
            <td><input type="radio" name="zone" value="A" class="zone">A</input></td>
            <td><input type="radio" name="zone" value="B" class="zone">B</input></td>
            <td><input type="radio" name="zone" value="C" class="zone">C</input></td>
            <td><input type="radio" name="zone" value="D" class="zone">D</input></td>
            <td><input type="radio" name="zone" value="E" class="zone">E</input></td>
            <td><input type="radio" name="zone" value="F" class="zone">F</input></td>
            <td><input type="radio" name="zone" value="G" class="zone">G</input></td>
            <td><input type="radio" name="zone" value="H" class="zone">H</input></td>
        </tr><tr>
            <td><input type="radio" name="zone" value="I" class="zone">I</input></td>
            <td><input type="radio" name="zone" value="J" class="zone">J</input></td>
            <td><input type="radio" name="zone" value="K" class="zone">K</input></td>
            <td><input type="radio" name="zone" value="L" class="zone">L</input></td>
            <td><input type="radio" name="zone" value="M" class="zone">M</input></td>
            <td><input type="radio" name="zone" value="N" class="zone">N</input></td>
            <td><input type="radio" name="zone" value="O" class="zone">O</input></td>
            <td><input type="radio" name="zone" value="P" class="zone">P</input></td>
        </tr></table>
    <table class="coms">
        <tr>
            <td>
                <button name="command" value="ON_1" class="com">1 ON</button>
                <button name="command" value="OFF_1" class="com">1 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_2" class="com">2 ON</button>
                <button name="command" value="OFF_2" class="com">2 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_3" class="com">3 ON</button>
                <button name="command" value="OFF_3" class="com">3 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_4" class="com">4 ON</button>
                <button name="command" value="OFF_4" class="com">4 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_5" class="com">5 ON</button>
                <button name="command" value="OFF_5" class="com">5 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_6" class="com">6 ON</button>
                <button name="command" value="OFF_6" class="com">6 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_7" class="com">7 ON</button>
                <button name="command" value="OFF_7" class="com">7 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_8" class="com">8 ON</button>
                <button name="command" value="OFF_8" class="com">8 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_9" class="com">9 ON</button>
                <button name="command" value="OFF_9" class="com">9 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_10" class="com">10 ON</button>
                <button name="command" value="OFF_10" class="com">10 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_11" class="com">11 ON</button>
                <button name="command" value="OFF_11" class="com">11 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_12" class="com">12 ON</button>
                <button name="command" value="OFF_12" class="com">12 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_13" class="com">13 ON</button>
                <button name="command" value="OFF_13" class="com">13 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_14" class="com">14 ON</button>
                <button name="command" value="OFF_14" class="com">14 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_15" class="com">15 ON</button>
                <button name="command" value="OFF_15" class="com">15 OFF</button>
            </td>
        </tr>
        <tr>
            <td>
                <button name="command" value="ON_16" class="com">16 ON</button>
                <button name="command" value="OFF_16" class="com">16 OFF</button>
            </td>
        </tr>
<!--
** NOT implemented yet...
        <tr>
            <td>
                <button name="command" value="Bri" class="com">Brighten</button>
                <button name="command" value="Dim" class="com">Dim</button>
            </td>
        </tr>
-->
    </table>
    </form>
  </body>
</html>
"""


def to_bytes(in_str):
    # could choose to only encode for Python 3+
    return in_str.encode('utf-8')

def simple_app(environ, start_response):
    setup_testing_defaults(environ)

    status = '200 OK'
    headers = [('Content-type', 'text/html')]

    start_response(status, headers)

    ret = []

    if environ['REQUEST_METHOD'] == 'POST':
        body= ''  # b'' for consistency on Python 3.0
        try:
            length= int(environ.get('CONTENT_LENGTH', '0'))
        except ValueError:
            length = 0
        if length != 0:
            body = environ['wsgi.input'].read(length)
            log = default_logger
            log.info('DEBUG body %r', body)
            body = body.decode('utf-8')
            log.info('DEBUG body %r', body)
            parameters = parse_qs(body)
            log.info('DEBUG parameters %r', parameters)
            house_code = parameters.get('zone')
            command = parameters.get('command')
            log.info('DEBUG house_code %r', house_code)
            log.info('DEBUG command %r', command)
            if house_code:
                house_code = house_code[0]
            if command:
                command = command[0]
                if command:
                    # WARNING no sanity checks input values!
                    # Assume we have an on/off directive
                    command = command.split('_')
                    log.info('DEBUG split command %r', command)

            # Repeat WARNING no sanity checks on input values!
            unit_num = int(command[1])
            state = command[0]

            # FIXME
            dev = x10_any.FirecrackerDriver()
            #dev = x10_any.FirecrackerDriver(serial_port_name)
            #dev = x10_any.FirecrackerDriver('COM11')
            #dev = x10_any.FirecrackerDriver('/dev/ttyUSB0')
            dev.x10_command(house_code, unit_num, state)

            # Preserve which house code/zone was selected
            ret.append(to_bytes(html.replace('>%s<' % house_code, ' checked="checked">%s<' % house_code)))
    else:
        ret.append(to_bytes(html))

    return ret


def main(argv=None):
    if argv is None:
        argv = sys.argv

    global serial_port_name

    log = default_logger
    log.setLevel(logging.INFO)
    #log.setLevel(logging.DEBUG)  # DEBUG

    try:
        serial_port_name = argv[1]
        log.info('Serial port provided on command line')
    except IndexError:
        # lets check environment variable X10_SERIAL_PORT
        serial_port_name = os.environ.get('X10_SERIAL_PORT')
        if not serial_port_name:
            try:
                # pick first one in list of devices found in system
                # no heuristics used (e.g. look for "serial" or "usb" in name)
                # just the first one in the list
                import serial.tools.list_ports

                possible_serial_ports = list(serial.tools.list_ports.comports())
                serial_port_name = possible_serial_ports[0][0]
                log.info('Serial port guessed')
            except IndexError:
                # use default
                serial_port_name = default_serial_port_name
                log.info('Serial port defaulted')
        else:
            log.info('Serial port picked up from env X10_SERIAL_PORT')

    log.info('Using serial port %r', serial_port_name)

    httpd = make_server('', server_port, simple_app)
    log.info('Serving on http://%s:%d/' % (platform.node(), server_port))
    log.info('CTRL-C (or CTRL-Break) to quit')
    httpd.serve_forever()

    return 0


if __name__ == "__main__":
    sys.exit(main())
