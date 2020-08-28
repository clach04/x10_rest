#
#   docker build . -t test-x10_rest
#   docker images  
# Ensure correct device name is used!
#   docker run --rm --device=/dev/ttyUSB0 -p 1234:1234  test-x10_rest
# FIXME document cgroup notes at http://marc.merlins.org/perso/linux/post_2018-12-20_Accessing-USB-Devices-In-Docker-_ttyUSB0_-dev-bus-usb-_-for-fastboot_-adb_-without-using-privileged.html


FROM python:3.8-slim

COPY requirements.txt .
COPY x10_rest.py .

RUN pip install -r requirements.txt


CMD [ "python3", "x10_rest.py" ]

