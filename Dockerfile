# Celery requires Python 3.10, for now
FROM python:3.10
ENV PYTHONUNBUFFERED=1 PORT=8000
EXPOSE 8000

RUN mkdir /app && useradd -d /app app && chown app:app /app
RUN apt-get -qq update \
  && apt-get install -qq -y sudo gdal-bin gettext potool restic postgresql-client ffmpeg \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /app/
COPY --chown=app:app . .

USER app
RUN ./manage.py collectstatic --noinput --ignore=*.py --ignore=*.html

CMD ["gunicorn", "serenity_qa.wsgi:application"]
