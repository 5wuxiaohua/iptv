FROM nginx:alpine

RUN apk add --no-cache python3 ca-certificates

ENTRYPOINT ["/opt/iptv/entrypoint.sh"]
