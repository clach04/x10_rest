#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""REST interface to control X10 devices

Currently implements interface that home-assistant REST switch
can interact with. For more details see
https://home-assistant.io/components/switch.rest/

Controls CM17A (Firecracker) X10 serial unit or Mochad compatible server
(for example, https://sourceforge.net/p/mochad and
https://bitbucket.org/clach04/mochad_firecracker/).

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

import x10_any
from x10_any import OFF, ON, ALL_OFF, LAMPS_OFF, LAMPS_ON


version_tuple = (0, 0, 3)
version = version_string = __version__ = '%d.%d.%d' % version_tuple

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


x10_status = {}
x10device = None

def simple_app(environ, start_response):
    global x10device

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
        x10device.x10_command(house_code, unit_num, state)

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
    global x10device

    log = default_logger
    log.setLevel(logging.INFO)
    log.setLevel(logging.DEBUG)  # DEBUG

    log.info('x10 rest version %s', version)
    # The dumbest arg processing...
    if '-m' in argv:
        argv.remove('-m')
        log.info('using Mochad')
        #x10device = x10_any.MochadDriver()  # TODO config
        x10device = x10_any.MochadDriver((mochad_host, mochad_port))
    else:
        try:
            serial_port_name = argv[1]
            log.info('Serial port provided on command line')
        except IndexError:
            # lets check environment variable X10_SERIAL_PORT
            serial_port_name = os.environ.get('X10_SERIAL_PORT')
            if serial_port_name:
                log.info('Serial port picked up from env X10_SERIAL_PORT')
        x10device = x10_any.FirecrackerDriver(serial_port_name)
        log.info('Using serial port %r', serial_port_name)

    httpd = make_server('', http_server_port, simple_app, server_class=MyWSGIServer, handler_class=MyWSGIRequestHandler)
    log.info('Serving on http://%s:%d/' % (platform.node(), http_server_port))
    log.info('CTRL-C (or CTRL-Break) to quit')
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
