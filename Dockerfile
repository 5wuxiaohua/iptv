FROM python:3.13-alpine

WORKDIR /opt/iptv

COPY iptv_updater.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/opt/iptv/entrypoint.sh"]
