import abc
from typing import Any, Dict, List, Optional
from aiogram import Bot, types
from loguru import logger

from MainBot.base.models import Users
from MainBot.base.orm_requests import RatingMethods
from MainBot.base.models import Users
from MainBot.keyboards import inline
from MainBot.utils.MyModule.message import MessageManager
import texts


class AbstractRatingType:
    @abc.abstractmethod
    async def get_word(self):
        """
        Получаем нужное слово с правильным окончанием
        """
    @abc.abstractmethod
    async def data(self):
        """
        Возвращаем данные по данному рейтингу
        """


class DailyLogin(AbstractRatingType):

    def __init__(self):
        self.head = texts.Rating.Text.daily_login_head
        self.dot = "..."

    def get_word(self, count: int) -> str:
        """
        Возвращает правильную форму слова "день" в зависимости от числа.
        1 день, 2 дня, 5 дней
        """
        if 10 <= count % 100 <= 19:
            return " дней"
        elif count % 10 == 1:
            return " день"
        elif 2 <= count % 10 <= 4:
            return " дня"
        return " дней"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().daily_login(user.user_id)


class CollectStarcoins(AbstractRatingType):

    def __init__(self):
        self.head = texts.Rating.Text.collect_starcoins_head
        self.dot = ""

    def get_word(self, *args, **kwargs) -> str:
        return "★"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().collect_starcoins(user.user_id)


class GuessCountry(AbstractRatingType):

    def __init__(self):
        self.head = texts.Rating.Text.guess_country_head
        self.dot = "..."

    def get_word(self, count: int) -> str:
        """
        Возвращает правильную форму слова "флаг" в зависимости от числа.
        1 флаг, 2 флага, 5 флагов
        """
        if 10 <= count % 100 <= 19:
            return " флагов"
        elif count % 10 == 1:
            return " флаг"
        elif 2 <= count % 10 <= 4:
            return " флага"
        return " флагов"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().guess_country(user.user_id)


class MakeClicks(AbstractRatingType):

    def __init__(self):
        self.head = texts.Rating.Text.make_clicks_head
        self.dot = "..."

    def get_word(self, count: int) -> str:
        """
        Возвращает правильную форму слова "клик" в зависимости от числа.
        1 клик, 2 клика, 5 кликов
        """
        if 10 <= count % 100 <= 19:
            return " кликов"
        elif count % 10 == 1:
            return " клик"
        elif 2 <= count % 10 <= 4:
            return " клика"
        return " кликов"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().make_clicks(user.user_id)


class CompletedQuests(AbstractRatingType):

    def __init__(self):
        self.head = texts.Rating.Text.completed_quests_head
        self.dot = "..."

    def get_word(self, count: int) -> str:
        """
        Возвращает правильную форму слова "квест" в зависимости от числа.
        1 квест, 2 квеста, 5 квестов
        """
        if 10 <= count % 100 <= 19:
            return " квестов"
        elif count % 10 == 1:
            return " квест"
        elif 2 <= count % 10 <= 4:
            return " квеста"
        return " квестов"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().completed_quests(user.user_id)


class InvitedFriends(AbstractRatingType):
    
    def __init__(self):
        self.head = texts.Rating.Text.invited_friends_head
        self.dot = "..."
    
    def get_word(self, count: int) -> str:
        """
        Возвращает правильную форму слова "друг" в зависимости от числа.
        1 друг, 2 друга, 5 друзей
        """
        if 10 <= count % 100 <= 19:
            return " друзей"
        elif count % 10 == 1:
            return " друг"
        elif 2 <= count % 10 <= 4:
            return " друга"
        else:
            return " друзей"

    async def data(
        self,
        user: Users
    ) -> Optional[Dict]:
        return await RatingMethods().invited_friends(user.user_id)


class RatingForms:

    async def main(
        self,
        user: Users,
        call: types.CallbackQuery
    ) -> None:
        """
        Выдаем меню с рейтингом
        """
        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            texts.Rating.Text.main,
            await inline.rating_menu(),
            "rating"
        )

    async def text(
        self,
        obj: AbstractRatingType,
        data: List[Dict]
    ) -> str:
        text = obj.head
        
        top = len(data) < 4
        
        tail_text = ""
        for i, d in enumerate(data):
            count_use_name = obj.get_word(d["value"])
            
            if d["my"]:
                if top:
                    tail_text = texts.Rating.Text.top_tail.format(
                        place=d["place"]
                    )
                else:
                    difference_name = obj.get_word(d["difference"])
                    tail_text = texts.Rating.Text.tail.format(
                        nick=d["nickname"],
                        place=d["place"],
                        count_use=f"{d["value"]}{count_use_name}",
                        next_place=d["next_place"],
                        difference=f"{d["difference"]}{difference_name}",
                        dot=obj.dot
                    )
            
            text_form: Optional[str] = texts.Rating.Text.body[i]
            if text_form:
                text += text_form.format(
                    nick=d["nickname"],
                    count_use=f"{d["value"]}{count_use_name}"
                )
        
        return text + tail_text

    async def section(
        self,
        user: Users,
        call: types.CallbackQuery,
        chapter: str
    ) -> None:
        """
        Даем инфу по определенному разделу
        """
        match chapter:
            case "daily_login":
                obj = DailyLogin()
            case "collect_starcoins":
                obj = CollectStarcoins()
            case "guess_country":
                obj = GuessCountry()
            case "make_clicks":
                obj = MakeClicks()
            case "completed_quests":
                obj = CompletedQuests()
            case "invited_friends":
                obj = InvitedFriends()
            case _:
                await call.answer(
                    texts.Error.Notif.undefined_error
                )
                return

        data = await obj.data(user)
        logger.debug(data)

        if not data:
            await call.answer(
                texts.Error.Notif.undefined_error
            )
            return

        text = await self.text(obj, data)

        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            text,
            await inline.rating_back(),
            "rating"
        )



