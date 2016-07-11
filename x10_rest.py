#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""REST interface to control X10 devices

Currently implements interface that home-assistant REST switch
can interact with. For more details see
https://home-assistant.io/components/switch.rest/

Controls CM17A (Firecracker) X10 serial unit.
Could/should be extended to use Mochad https://sourceforge.net/p/mochad
or a Mochad compatible server such as
https://bitbucket.org/clach04/mochad_firecracker/.

Uses WSGI, see http://docs.python.org/library/wsgiref.html

Python 2 or Python 3 for this script, x10 modules untested with Python 3.

REST interface implemented is completely influenced by
https://home-assistant.io/components/switch.rest/ behavior
so only ON and OFF is supported.

URL form:

    /x10/{house code}/{optional_unit_number}

if {optional_unit_number} is omitted means all units in {house code}.

Examples:

  * /x10/A
  * /x10/A/1
  * /x10/A/2
  * /x10/B/1
  * ...
"""

import cgi
import logging
import mimetypes
import os
import platform
from pprint import pprint
import socket
try:
    import SocketServer
except ImportError:
    # Python 3
    import socketserver as SocketServer
import sys
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler


firecracker = None
x10 = None
mochad = None  # FIXME make this config, currently hacky command line option

if mochad is None:
    try:
        import  x10  # http://www.averdevelopment.com/python/x10.html
    except ImportError:
        import firecracker  # https://bitbucket.org/cdelker/python-x10-firecracker-interface/
        # WARNING all on/off not supported with this module :-(


version_tuple = (0, 0, 2)
version = version_string = '%d.%d.%d' % version_tuple

logging.basicConfig()
default_logger = logging.getLogger(__name__)

http_server_port = 1234

# TODO allow config for three items below
mochad_host = 'localhost'
mochad_port = 1099
mochad_type = 'rf'  # or 'pl'


def to_bytes(in_str):
    # could choose to only encode for Python 3+
    # could simple use latin1
    return in_str.encode('utf-8')

def to_string(in_str):
    # could choose to only decode for Python 3+
    # could simple use latin1
    return in_str.decode('utf-8')


def netcat(hostname, port, content, log=None):
    log = log or default_logger
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.debug("Trying connection to: %s:%s" % (hostname, port))
        s.connect((hostname, port))

        log.debug("Connected to: %s:%s" % (hostname, port))
        s.sendall(b"%s\n" % content)
        log.debug("sent: %s" % content)
        s.shutdown(socket.SHUT_WR)
        buff = ""

        while True:
            data = s.recv(1024)
            if data == "":
                break
            buff = "%s%s" % (buff, data)
        log.debug("Received: %s" % repr(buff))
        s.close()
        log.debug("Connection closed.")
        return repr(buff)
    except Exception as ex:
        log.error("ERROR: %s" % ex)
        raise ex


def scale_255_to_8(x):
    """Scale x from 0..255 to 0..7
    0 is considered OFF
    8 is considered fully on
    """
    factor = x / 255.0
    return 8 - int(abs(round(8 * factor)))

def scale_31_to_8(x):
    """Scale x from 0..31 to 0..7
    0 is considered OFF
    8 is considered fully on
    """
    factor = x / 31.0
    return 8 - int(abs(round(8 * factor)))

# Mochad command constants - TODO make these an enum?
ALL_OFF = 'all_units_off'
LAMPS_OFF = 'all_lights_off'
LAMPS_ON = 'all_lights_on'
ON = 'ON'
OFF = 'OFF'

# Mappings from Mochad command to https://bitbucket.org/cdelker/python-x10-firecracker-interface/
x10_mapping = {
    ALL_OFF: 'ALL OFF',
    LAMPS_OFF: 'Lamps Off',
    LAMPS_ON: 'Lamps On',
}

def x10_command(serial_port_name, house_code, unit_num, state, log=None):
    """Send X10 command to Firecracker serial unit, attempts to
    normalize API irrespective of which x10 (serial) module is used.

    @param serial_port_name - Windows example='COM6', Linux example='/dev/ttyUSB0'
    @param house_code (A-P) - example='A'
    @param unit_num (1-16)- example=1 (or None to impact entire house code)
    @param state - Mochad command/state, See
            https://sourceforge.net/p/mochad/code/ci/master/tree/README
            examples=OFF, 'OFF', 'ON', ALL_OFF, 'all_units_off', 'xdim 128', etc.
    @param log - Python logging object, if None a default log will be used

    Examples:

        x10_command('COM6', 'A', '1', 'ON')
        x10_command('/dev/ttyUSB0', 'A', '1', 'ON')
        x10_command(serial_port_name, 'A', None, ON)
        x10_command(serial_port_name, 'A', None, OFF)
        x10_command(serial_port_name, 'A', None, 'all_lights_off')
        x10_command(serial_port_name, 'A', None, 'all_units_off')
        x10_command(serial_port_name, 'A', None, ALL_OFF)
        x10_command(serial_port_name, 'A', None, 'all_lights_on')
        x10_command(serial_port_name, 'A', 1, 'xdim 128')
    """

    log = log or default_logger

    if unit_num is not None:
        unit_num = int(unit_num)
    else:
        # Assume some sort of 'ALL' command.
        if firecracker:
            log.error('using python-x10-firecracker-interface NO support for all ON/OFF')
    state = state.lower()

    if mochad:
        if state.startswith('xdim') or state.startswith('dim') or state.startswith('bright'):
            raise NotImplementedError('xdim/dim/bright %r' % ((house_code, unit_num, state),))
        else:
            if unit_num is not None:
                house_and_unit = '%s%d' % (house_code, unit_num)
            else:
                raise NotImplementedError('mochad all ON/OFF %r' % ((house_code, unit_num, state),))
                house_and_unit = house_code
            mochad_cmd = b"%s %s %s\n" % (mochad_type, house_and_unit, state)
            log.debug('mochad send: %r', mochad_cmd)
            netcat(mochad_host, mochad_port, mochad_cmd)
    elif firecracker:
        log.debug('firecracker send: %r', (serial_port_name, house_code, unit_num, state))
        firecracker.send_command(serial_port_name, house_code, unit_num, state)
    else:
        if unit_num is not None:
            if state.startswith('xdim') or state.startswith('dim') or state.startswith('bright'):
                dim_count = int(state.split()[-1])
                if state.startswith('xdim'):
                    dim_count = scale_255_to_8(dim_count)
                else:
                    # assumed dim or bright
                    dim_count = scale_31_to_8(dim_count)
                dim_str = ', %s dim' % (house_code, )
                dim_list = []
                for _ in range(dim_count):
                    dim_list.append(dim_str)
                dim_str =  ''.join(dim_list)
                if dim_count == 0:
                    # No dim
                    x10_command_str = '%s%s %s' % (house_code, unit_num, 'on')
                else:
                    # If lamp is already dimmed, need to turn it off and then back on
                    x10_command_str = '%s%s %s, %s%s %s%s' % (house_code, unit_num, 'off', house_code, unit_num, 'on', dim_str)
            else:
                x10_command_str = '%s%s %s' % (house_code, unit_num, state)
        else:
            # Assume a command for house not a specific unit
            state = x10_mapping[state]

            x10_command_str = '%s %s' % (house_code, state)
        log.debug('x10_command_str send: %r', x10_command_str)
        x10.sendCommands(serial_port_name, x10_command_str)


def not_found(environ, start_response):
    """serves 404s."""
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [to_bytes('''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL /??????? was not found on this server.</p>
</body></html>''')]


# serial port name for CM17A aka Firecracker
default_serial_port_name = '/dev/ttyUSB0'  # Example Linux USB serial adapter
default_serial_port_name = 'com5'  # Windows serial port

serial_port_name = default_serial_port_name

x10_status = {}
OFF = 'OFF'
ON = 'ON'

def simple_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    result= []

    path_info = environ['PATH_INFO']

    # naive URL parsing
    if not path_info:
        # not sure how this could happen but....
        return not_found(environ, start_response)
    if not path_info.startswith('/x10/'):
        return not_found(environ, start_response)
    url_split = path_info.split('/')
    house_code = url_split[2]  # TODO try/except
    try:
        unit_num = url_split[3]
    except IndexError:
        unit_num = None
    print('house_code: %r' % house_code)
    print('unit_num: %r' % unit_num)
    # TODO checks after this should probably not be 404 errors..
    house_code = house_code.upper()
    if unit_num is not None:
        unit_num = int(unit_num)

    if environ['REQUEST_METHOD'] == 'GET':
        house_status = x10_status.get(house_code)
        if house_status is None:
            result.append(to_bytes(OFF))
        else:
            device_status = house_status.get(unit_num)
            if device_status is None:
                result.append(to_bytes(OFF))
            else:
                result.append(to_bytes(device_status))
    elif environ['REQUEST_METHOD'] == 'POST':
        # the environment variable CONTENT_LENGTH may be empty or missing
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
        # Read POST body
        request_body = environ['wsgi.input'].read(request_body_size)
        request_body = to_string(request_body)
        state = request_body
        # FIXME normalize state
        if unit_num is None:
            # assume whole house
            # could update HA configuration.yaml with custom body_on/body_off
            # I _think_ this is easier and understandable for X10 users
            # albeit all lamps on/all off (i.e. not just lamps) is unintuitive for non-X10 users
            if state.upper() == ON:
                state = LAMPS_ON
            else:
                # just assume all off
                state = ALL_OFF
        # now send x10 command
        x10_command(serial_port_name, house_code, unit_num, state)

        # Now update state for GET
        if state == LAMPS_ON:
            state = ON
            house_status = {}
            for temp_unit_num in range(1, 16+1):
                house_status[temp_unit_num] = state
            x10_status[house_code] = house_status
            # NOTE whilst status is internally correct, delay for HA client to read new status
        elif state == ALL_OFF:
            state = OFF
            if x10_status.get(house_code):
                del x10_status[house_code]
                # NOTE whilst status is internally correct, delay for HA client to read new status
        house_status = x10_status.get(house_code)
        if house_status is None:
            house_status = {}
            x10_status[house_code] = house_status
        house_status[unit_num] = state
    else:
        return not_found(environ, start_response)  # FIXME not 404

    start_response(status, headers)
    return result


class MyWSGIRequestHandler(WSGIRequestHandler):
    """Do not perform Fully Qualified Domain Lookup.
    One networks with missing (or poor) DNS, getfqdn can take over 5 secs
    EACH network IO"""

    def address_string(self):
        """Return the client address formatted for logging.

        This version looks up the full hostname using gethostbyaddr(),
        and tries to find a name that contains at least one dot.

        """

        host, port = self.client_address[:2]
        return host  # socket.getfqdn(host)


class MyWSGIServer(WSGIServer):
    """Avoid default Python socket server oddities.

     1) Do not perform Fully Qualified Domain Lookup.
        On networks with missing (or poor) DNS, getfqdn() can take over
        5 secs EACH network IO.
     2) Do not allow address re-use.
        On machines where something is already listening on the requested
        port the default Windows socket setting for Python SocketServers
        is to allow the bind to succeed (even though it can't then service
        any requests).
        One possible workaround for Windows is to set the
        DisableAddressSharing registry entry:
        (HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\services\Afd\Parameters)
        and reboot. This registry setting prevents multiple sockets from binding
        to the same port and is essentially enabling SO_EXCLUSIVEADDRUSE on
        all sockets. See Java bug 6421091.
    """

    allow_reuse_address = False  # Use SO_EXCLUSIVEADDRUSE,  True only makes sense for testing

    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = host  # socket.getfqdn(host)  i.e. use as-is do *not* perform reverse lookup
        self.server_port = port
        self.setup_environ()


def main(argv=None):
    if argv is None:
        argv = sys.argv

    global serial_port_name
    global mochad

    log = default_logger
    log.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)  # DEBUG

    log.info('x10 rest version %s', version)
    # The dumbest arg processing...
    if '-m' in argv:
        mochad = True
        argv.remove('-m')
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

    httpd = make_server('', http_server_port, simple_app, server_class=MyWSGIServer, handler_class=MyWSGIRequestHandler)
    log.info('Serving on http://%s:%d/' % (platform.node(), http_server_port))
    log.info('CTRL-C (or CTRL-Break) to quit')
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
