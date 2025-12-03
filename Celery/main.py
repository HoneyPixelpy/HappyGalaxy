import os
from pathlib import Path

from loguru import logger
from celery import Celery
from celery.schedules import crontab

from dotenv import load_dotenv

load_dotenv()

base_dir = Path(__file__).resolve().parent

logger.add(
    sink=f'{base_dir}/logs/debug.log',
    format="| TIME:{time:HH:mm:ss} | LVL:{level} | FILE:{file} | LINE:{line} | FUNC:{function} |\n:::{message}",
    level="DEBUG",
    rotation="1000 KB"
)

app = Celery(
    'tasks',
    broker=os.getenv('REDIS_URL'),
    backend=os.getenv('REDIS_URL'),
    include=['utils.tasks'],  # Явно указываем модуль с задачами
    timezone='Europe/Moscow'
)

DEBUG = False

# NOTE celery -A main worker -Q copy_base,continue_registration,quest_attempts,aggregation-pipeline -l info
# NOTE celery -A main beat -l info
app.conf.beat_schedule = {
    'daily-db-backup': {
        'task': 'utils.tasks.database_backup_task',
        'schedule': crontab(minute=0, hour='*'), # crontab(minute=0, hour='*') crontab(minute='*/1')
        'options': {
            'queue': 'copy_base',
            'expires': 3600  # Задача исчезнет, если не взята в работу за пол часа
        }
    },
    'continue-registration': {
        'task': 'utils.tasks.continue_registration_task',
        'schedule': crontab(minute=0, hour=15), # crontab(hour=10) crontab(minute='*/1')
        'options': {
            'queue': 'continue_registration',
            'expires': 3600  # Задача исчезнет, если не взята в работу за пол часа
        }
    },
    'quest-attempts': {
        'task': 'utils.tasks.auto_reject_old_quest_attempts_task',
        'schedule': crontab(minute=0, hour='*'), # crontab(hour=10) crontab(minute='*/1')
        'options': {
            'queue': 'quest_attempts',
            'expires': 3600  # Задача исчезнет, если не взята в работу за пол часа
        }
    },
    'aggregation-pipeline': {
        'task': 'utils.tasks.aggregation_pipeline_task',
        'schedule': crontab(minute='*/1') if DEBUG else crontab(minute=0, hour=4), # crontab(hour=10) crontab(minute='*/1')
        'options': {
            'queue': 'aggregation_pipeline',
            'expires': 3600  # Задача исчезнет, если не взята в работу за пол часа
        }
    }
}
