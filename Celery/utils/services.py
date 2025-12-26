import datetime

from api.Django.forms import (AggregatorMethods, CopyBaseMethods,
                              QuestModerationAttemptMethods, UserMethods)
from api.MainBot import MainBotForms
from loguru import logger
from rabbitmq import RabbitMQForms


def sync_copy_bd(
    target_time: datetime.datetime
    ) -> None:
    formatted_time = target_time.strftime('%d-%m-%Y_%H-%M')
    try:
        content: bytes = CopyBaseMethods().copy_base()
        if not content:
            raise Exception()
        
        # Отправляем в RabbitMQ
        RabbitMQForms().send_backup(
            chat_id=1894909159,
            formatted_time=formatted_time,
            content=content.decode(),
            caption=f"Копия базы данных на {formatted_time}"
        )
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise  # Для retry в Celery

def continue_reg_mailing(*args, **kwargs) -> None:
    try:
        user_ids = UserMethods().unregistered_users()
        if not user_ids:
            logger.warning(
                "Некому писать о проделжении регистрации"
            )
            return
        
        MainBotForms().mailing_continue_reg(
            user_ids
        )
        
    except Exception as e:
        logger.error(f"Mailing failed: {e}")
        raise

def auto_reject_old_quest_attempts(*args, **kwargs) -> None:
    try:
        mailing_data = QuestModerationAttemptMethods().old_quest_attempts()
        logger.debug(mailing_data)
        if not mailing_data:
            logger.warning(
                "Некому писать о просроченных квестах"
            )
            return
        
        MainBotForms().mailing_old_quests(
            mailing_data
        )
    except Exception as e:
        logger.error(f"Deleted Old Quests failed: {e}")
        raise

def aggregation_pipeline(
    target_time: datetime.datetime
    ) -> None:
    """Ежедневный пайплайн агрегации"""
    formatted_time = target_time.strftime('%d-%m-%Y_%H-%M')
    try:
        content = AggregatorMethods().aggregate_data()
        if not content:
            raise Exception()
        
        # Отправляем в RabbitMQ
        RabbitMQForms().send_backup(
            chat_id=1894909159,
            formatted_time=formatted_time,
            content=content.decode(),
            caption=f"Копия данных активности пользователей {formatted_time}"
        )
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise  # Для retry в Celery
