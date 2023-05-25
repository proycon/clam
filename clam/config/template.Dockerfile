FROM alpine:latest

#(adapt and enable this):
#LABEL org.opencontainers.image.authors="Your name <your@mail.com>"
#(adapt this:)
LABEL description="A webservice powered by CLAM" 

ENV UWSGI_UID=100
ENV UWSGI_GID=100
ENV UWSGI_PROCESSES=2
ENV UWSGI_THREADS=2

#Set to 1 to enable development version of CLAM
ARG CLAM_DEV=0

# See *config.yml for CLAM configuration variables you can set using environment variables

# Install all global dependencies (adapt this to add extra dependencies your system might need)
RUN apk update && apk add git runit curl ca-certificates nginx uwsgi uwsgi-python3 py3-pip py3-yaml py3-lxml py3-requests py3-wheel

# Prepare environment
RUN mkdir -p /etc/service/nginx /etc/service/uwsgi

# Patch to set proper mimetype for CLAM's logs
RUN sed -i 's/txt;/txt log;/' /etc/nginx/mime.types &&\
    sed -i 's/xml;/xml xsl;/' /etc/nginx/mime.types

# Temporarily add the sources of this webservice
COPY . /usr/src/webservice

# Configure webserver and uwsgi server
RUN echo -e '#!/bin/sh\nln -sf /dev/stdout /var/log/nginx/access.log\nnginx -g "daemon off; error_log /dev/stdout info;"' > /etc/service/nginx/run &&\
    echo -e '#!/bin/sh\numask 007\nuwsgi --plugin python3 --uid ${UWSGI_UID:100} --gid ${UWSGI_GID:100} --master --socket "127.0.0.1:8888" --wsgi-file /etc/clam_webservice.wsgi --processes ${UWSGI_PROCESSES:-2} --threads ${UWSGI_THREADS:-2} --manage-script-name' > /etc/service/uwsgi/run &&\
    chmod a+x /etc/service/uwsgi/run /etc/service/nginx/run &&\
    cp "/usr/src/webservice/{sys_id}/{sys_id}.wsgi" /etc/clam_webservice.wsgi &&\
    chmod a+x /etc/clam_webservice.wsgi &&\
    echo 'server {\
    listen 80 default_server;\
    listen [::]:80 default_server;\
\
    client_max_body_size 125m;\
\
    location /static { alias /opt/clam/static; }\
    location / {\
        uwsgi_param  QUERY_STRING       $query_string;\
        uwsgi_param  REQUEST_METHOD     $request_method;\
        uwsgi_param  CONTENT_TYPE       $content_type;\
        uwsgi_param  CONTENT_LENGTH     $content_length;\
\
        uwsgi_param  REQUEST_URI        $request_uri;\
        uwsgi_param  PATH_INFO          $document_uri;\
        uwsgi_param  DOCUMENT_ROOT      $document_root;\
        uwsgi_param  SERVER_PROTOCOL    $server_protocol;\
        uwsgi_param  REQUEST_SCHEME     $scheme;\
        uwsgi_param  HTTPS              $https if_not_empty;\
\
        uwsgi_param  REMOTE_ADDR        $remote_addr;\
        uwsgi_param  REMOTE_PORT        $remote_port;\
        uwsgi_param  SERVER_PORT        $server_port;\
        uwsgi_param  SERVER_NAME        $server_name;\
\
        uwsgi_pass 127.0.0.1:8888;\
    }\
\
    location = /404.html {\
        internal;\
    }\
}' > /etc/nginx/http.d/default.conf

# Install the service itself, will also pull in CLAM and all other dependencies
RUN if [ $CLAM_DEV -eq 1 ]; then pip install git+https://github.com/proycon/clam.git; fi &&\
    cd /usr/src/webservice && pip install . && rm -Rf /usr/src/webservice &&\
    ln -s /usr/lib/python3.*/site-packages/clam /opt/clam

VOLUME ["/data"]
EXPOSE 80
WORKDIR /

ENTRYPOINT ["runsvdir","-P","/etc/service"]
