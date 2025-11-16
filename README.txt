# 🌌 Galaxy Project

Многосервисное Django приложение для управления ботами и пользователями.

## 📦 Состав проекта

- **Django** - основной бэкенд и админ-панель
- **PostgreSQL** - основная база данных  
- **Redis** - кэширование и брокер для Celery
- **Celery** - фоновые и периодические задачи
- **Celery Beat** - планировщик задач
- **Telegram Bots** - боты для взаимодействия с пользователями
- **FastAPI** - API для бота с уведомлениями
- **Nginx** - веб-сервер и reverse proxy
- **Gunicorn** - WSGI сервер для Django

## 🛠 Технологии

- Python 3.12
- Django 5.1.7
- Django REST Framework
- Django Jazzmin (кастомизированная админ-панель)
- PostgreSQL 15
- Redis
- Celery
- FastAPI
- Gunicorn
- Nginx
- Docker & Docker Compose

## ⚡ Быстрый старт

### Предварительные требования

- Docker
- Docker Compose

### Запуск в development

```bash
# Клонировать репозиторий
git clone <repository-url>
cd Galaxy

# Запустить все сервисы
docker-compose up -d

# Применить миграции
docker-compose exec django python manage.py migrate

# Создать суперпользователя
docker-compose exec django python manage.py createsuperuser

# Собрать статические файлы
docker-compose exec django python manage.py collectstatic --noinput
