#
#   docker build . -t test-x10_rest
#   docker images  
# Ensure correct device name is used!
# Based on https://stackoverflow.com/a/62758958
#   docker run --rm -v /dev:/dev --device-cgroup-rule='c 188:* rmw' -p 1234:1234  test-x10_rest
# determine major number (in example above) via:
#   ls -la /dev/ttyUSB0 | awk '{print $5}'
# For interactive testing:
#   docker run --rm  -it --entrypoint=/bin/bash  -v /dev:/dev --device-cgroup-rule='c 188:* rmw' -p 1234:1234  test-x10_rest


FROM python:3.8-slim

COPY requirements.txt .
COPY x10_rest.py .

RUN pip install -r requirements.txt


CMD [ "python3", "x10_rest.py" ]

