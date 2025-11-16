import base64
import datetime
import os

from loguru import logger

from api.ServiceBot import FastAPIForms
from api.MainBot import MainBotForms
from api.Django.forms import UserMethods, CopyBaseMethods, QuestModerationAttemptMethods



def sync_copy_bd(
    target_time: datetime.datetime
    ) -> None:
    formatted_time = target_time.strftime('%d-%m-%Y_%H-%M')
    try:
        content = CopyBaseMethods().copy_base()
        if not content:
            raise Exception()
        
        send_result = FastAPIForms().send_backup(
            1894909159,
            formatted_time,
            base64.b64encode(content).decode('utf-8')
        )
        if not send_result:
            raise Exception()
        
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

