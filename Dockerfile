FROM python:3.10
ENV PYTHONUNBUFFERED 1

RUN apt-get -qq update \
  && apt-get install -qq -y sudo gdal-bin gettext potool restic postgresql-client ffmpeg \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

COPY . /app/
WORKDIR /app/

RUN ./manage.py collectstatic --noinput --ignore=*.py --ignore=*.html > /dev/null \
  && useradd -d /app app && chown -R app:app /app \
  && echo "app ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/user
USER app

