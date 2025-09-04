FROM python:3.12-slim


WORKDIR /app


RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt ./


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV SECRET_KEY="django-insecure-2a*r$gzo0e7_)du043#m6t-+tj2x1gff9(&y&1febgjj@&7f*r"
ENV CELERY_BROKER_URL="redis://redis:6379/0"
ENV CELERY_BACKEND="redis://redis:6379/0"


RUN mkdir -p /app/static /app/staticfiles /app/media


EXPOSE 8000


CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]