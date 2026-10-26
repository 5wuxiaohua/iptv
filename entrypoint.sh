#!/bin/sh

set -e

echo "Starting IPTV updater..."

python3 -u /opt/iptv/iptv_updater.py &

echo "Starting nginx..."

exec nginx -g 'daemon off;'
