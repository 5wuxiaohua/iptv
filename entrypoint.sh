#!/bin/sh

set -e

echo "Starting IPTV updater..."
exec python3 -u /opt/iptv/iptv_updater.py
