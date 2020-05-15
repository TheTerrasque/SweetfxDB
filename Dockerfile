FROM python:3.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client nginx python-pip \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/fastcgi.conf /etc/nginx/fastcgi_params \
    && rm -f /etc/nginx/snippets/fastcgi-php.conf /etc/nginx/snippets/snakeoil.conf /etc/nginx/sites-enabled/*

WORKDIR /usr/src/app
RUN pip install --upgrade pip
COPY reqs.txt ./
RUN pip install -r reqs.txt
COPY . .
RUN mv dockerfiles/supervisord.conf /etc/supervisord.conf && mkdir -p /etc/uwsgi/ && mv dockerfiles/uwsgi.ini /etc/uwsgi/wsgi.ini && mv dockerfiles/nginx.conf /etc/nginx/sites-enabled/sfx.site && mkdir -p data && mkdir -p media && chown www-data data && chown www-data media
RUN python manage.py collectstatic

EXPOSE 80
CMD ["bash", "launch.sh"]