FROM python:3.12.11

WORKDIR /Celery

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# CMD ["celery", "-A", "main", "worker", "-Q", "copy_base", "-l", "info"]
# CMD ["celery", "-A", "main", "beat", "-l", "info"]