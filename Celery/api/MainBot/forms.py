from typing import Any, Dict, List

from .requests import MainBotService


class MainBotMethods:
    
    def __init__(self):
        self.main_bot = MainBotService()

    def mailing_continue_reg(
        self,
        user_ids: List[int]
        ) -> Any:
        return self.main_bot.send_continue_registration(
            user_ids
        )

    def mailing_old_quests(
        self,
        mailing_data: List[Dict]
        ) -> Any:
        return self.main_bot.send_old_quests(
            mailing_data
        )


class MainBotForms(MainBotMethods):
    
    def __init__(self):
        super().__init__()
