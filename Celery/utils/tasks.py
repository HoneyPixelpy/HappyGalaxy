import datetime

from celery import shared_task
import pytz

from .services import aggregation_pipeline, sync_copy_bd, continue_reg_mailing, auto_reject_old_quest_attempts


@shared_task(name='utils.tasks.database_backup_task', bind=True)
def database_backup_task(self):
    """
    Синхронная задача для резервного копирования
    """
    try:
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.datetime.now(tz)
        sync_copy_bd(now)
        
    except Exception as e:
        self.retry(exc=e, countdown=300, max_retries=10)


@shared_task(name='utils.tasks.continue_registration_task', bind=True)
def continue_registration_task(self):
    """
    Синхронная задача для рассылки о продолжении регистрации
    """
    try:
        continue_reg_mailing()
        
    except Exception as e:
        self.retry(exc=e, countdown=300, max_retries=10)


@shared_task(name='utils.tasks.auto_reject_old_quest_attempts_task', bind=True)
def auto_reject_old_quest_attempts_task(self):
    """
    Автоматическое отклонение попыток квестов старше 3 дней
    Запускается ежедневно через Celery Beat
    """
    try:
        auto_reject_old_quest_attempts()
        
    except Exception as e:
        self.retry(exc=e, countdown=300, max_retries=10)

@shared_task(name='utils.tasks.aggregation_pipeline_task', bind=True)
def aggregation_pipeline_task(self):
    """Ежедневный пайплайн агрегации"""
    try:
        tz = pytz.timezone('Europe/Moscow')
        now = datetime.datetime.now(tz)
        aggregation_pipeline(now)
        
    except Exception as e:
        self.retry(exc=e, countdown=300, max_retries=10)


