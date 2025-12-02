FROM python:3.12.11

WORKDIR /NotificationService

# Копируем requirements.txt первым для кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

# Запускаем consumer
CMD ["python", "backup_consumer.py"]
