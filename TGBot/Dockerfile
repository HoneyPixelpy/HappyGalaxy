FROM python:3.12.11 as base

WORKDIR /TGBot

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

FROM base as main-bot
CMD ["python", "-m", "main"]

FROM base as gpt-bot  
CMD ["python", "-m", "main_gpt"]
