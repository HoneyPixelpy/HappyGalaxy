import asyncio
from datetime import datetime
import json
import math
import random
from typing import Optional, Tuple, Union
from collections import namedtuple

from aiogram.fsm.context import FSMContext
from aiogram import Bot, types
from loguru import logger
import pytz

from MainBot.base.models import SubscribeQuest, Users, Quests, IdeaQuests, DailyQuests
from MainBot.state.state import Daily, Idea
from MainBot.utils.errors import ListLengthChangedError, NoDesiredTypeError
from Redis.aggregator import QuestAggregator
from Redis.main import RedisManager
import texts, config
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.base.orm_requests import QuestsMethods, UseQuestsMethods, UserMethods
from MainBot.utils.MyModule import Func
from VKBot import VKForms
from MainBot.config import bot


lock = asyncio.Lock()

class QuestPagination:

    def __init__(self):
        self.redis = RedisManager()
        self.base_key = "quest_pagination"

    async def get_page_number(
        self,
        user: Users
        ) -> int:
        """Получить номер страницы с преобразованием в int"""
        try:
            redis_client = await self.redis.get_redis()
            key = f"{self.base_key}:{user.user_id}"
            
            page_number = await redis_client.get(key)
            return int(page_number) if page_number else 1
            
        except (ValueError, TypeError):
            return 1
        except Exception as e:
            logger.error(f"Redis error in get_page_number: {e}")
            return 1
                
    async def set_page_number(
        self,
        user: Users,
        pagination: int
        ):
        """Установить номер страницы с TTL"""
        try:
            redis_client = await self.redis.get_redis()
            key = f"{self.base_key}:{user.user_id}"
            
            # Устанавливаем на 1 час (3600 сек)
            await redis_client.setex(key, 3600, pagination)
            
        except Exception as e:
            logger.error(f"Redis error in set_page_number: {e}")
            

class DailyQuest:
    
    async def get_daily_quest(
        self,
        message: types.Message,
        user: Users,
        quest_id: int
        ) -> None:
        quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            await message.delete()
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Quests.Error.no_quest,
                reply_markup=await reply.main_menu(user)
            )
        else:
            daily_quest: DailyQuests = quest.quest_data
            
            text = texts.Quests.Texts.idea_quest.format(
                    title=daily_quest.title,
                    description=daily_quest.description,
                    price=daily_quest.reward_starcoins
                )
            try:
                await message.edit_text(
                    text=text,
                    reply_markup=await inline.daily_quest(quest.id),
                    disable_web_page_preview=True
                )
            except:
                await message.bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=await inline.daily_quest(quest.id),
                    disable_web_page_preview=True
                )
                await message.delete()
    
    async def action_daily_quest(
        self,
        call: types.CallbackQuery,
        state: FSMContext,
        user: Users,
        quest_id: int
        ) -> Optional[bool]:
        quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            await call.message.delete()
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Quests.Error.no_quest,
                reply_markup=await reply.main_menu(user)
            )
        else:
            daily_quest: DailyQuests = quest.quest_data
            
            logger.debug(daily_quest.type.value)
            
            if daily_quest.type.value == "button":
                return await self.fast_success(
                    call,
                    user,
                    quest_id
                )
            elif daily_quest.type.value == "content":
                text = texts.Quests.Texts.idea_call_action.format(
                        call_action=daily_quest.call_action
                    )
                try:
                    await call.message.edit_text(
                        text=text,
                        reply_markup=await reply.back(daily_quest.title),
                        disable_web_page_preview=True
                    )
                except:
                    await call.message.bot.send_message(
                        chat_id=user.user_id,
                        text=text,
                        reply_markup=await reply.back(daily_quest.title),
                        disable_web_page_preview=True
                    )
                    await call.message.delete()
                
                await state.set_state(
                    Daily.wait
                )
                await state.update_data(
                    id=quest.id,
                    success_admin=quest.success_admin,
                    type_quest=quest.type_quest.value,
                    title=daily_quest.title,
                    content=daily_quest.content
                )

    async def check_daily_quest(
        self,
        message: types.Message,
        state: FSMContext,
        user: Users,
        **kwargs
        ) -> None:
        try:
            if config.debug:
                logger.debug(message)

                if not kwargs.get("state_data"):
                    state_data: dict = await state.get_data()
                else:
                    state_data = kwargs["state_data"]
                    
                logger.debug(state_data)
                
                # msg_datas = await QuestAggregator().add_message(
                #     user.user_id,
                #     message,
                #     state,
                #     state_data
                # )
                if not kwargs.get("msg_datas"):
                    msg_datas = await QuestAggregator().add_message(
                        user.user_id,
                        message,
                        state,
                        state_data
                    )
                else:
                    msg_datas = kwargs["msg_datas"]
                    
                logger.debug(msg_datas)
                
                # if not kwargs.get("test"):
                #     num_test = random.randint(100000, 999999)
                #     del state_data['user']
                #     with open(config.BASE_DIR / "test.json", "r", encoding="utf-8") as file:
                #         file_str = file.read()
                #         file_dict = json.loads(file_str)
                    
                #     file_dict[num_test] = {
                #             "message": message.model_dump_json(exclude={'datetime', 'link_preview_options', 'default', 'link_preview_prefer_small_media'}),
                #             "user": user.model_dump_json(),
                #             "state_data": state_data,
                #             "msg_datas": msg_datas
                #             }
                        
                #     with open(config.BASE_DIR / "test.json", "w", encoding="utf-8") as file:
                #         file.write(json.dumps(file_dict, indent=2, ensure_ascii=False))
                        
            else:
                state_data: dict = await state.get_data()
                msg_datas = await QuestAggregator().add_message(
                    user.user_id,
                    message,
                    state,
                    state_data
                )
            
            success_admin = state_data['success_admin']
            logger.debug(
                f"{success_admin} -> {user.user_id}"
            )

            send_message = await Func.constructor_func_to_mailing_msgs(
                message.bot,
                msg_datas['text'],
                msg_datas['content_type'],
                msg_datas['media_content'],
                msg_datas['media_group_id'],
                False,
                reply_markup=await inline.verif_idea_admin(
                    state_data['id'],
                    user.user_id
                ) if success_admin else None
            )
            
            # NOTE это для того чтобы написать в чат с логами имитируя объект Users
            User = namedtuple('User', ['user_id'])
            local_chat_id = config.smm_chat if "SMM" in state_data['title'] else config.quests_chat
            user_obj = User(user_id=local_chat_id)
            
            await message.bot.send_message(
                chat_id=local_chat_id,
                text=texts.Quests.Texts.log_idea_success.format(
                    tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                    title_quest=state_data['title'],
                    role=user.role_name,
                    gender=await Func.gender_name(user.gender, user.role_private),
                    age=(datetime.now(pytz.timezone('Europe/Moscow')) - user.age).days // 365,
                    title="Имя" if user.role_private == "child" else "ФИО",
                    supername=user.supername,
                    name=user.name,
                    nickname=user.nickname,
                    phone=user.phone,
                    created_at=await Func.format_date(user.created_at),
                    referral_count=await UserMethods().get_referral_count(user.user_id)
                )
            )
            await state.clear()
            
            reward_starcoins_bool = await UseQuestsMethods().create_idea_daily(
                user.id,
                state_data['id']
            )

            await send_message(
                user_obj
            )

            if type(reward_starcoins_bool) in [float,int]:
                await message.answer(
                    text=texts.Quests.Texts.fast_approve.format(
                        starcoins=reward_starcoins_bool
                        ),
                    reply_markup=await reply.main_menu(user)
                )
            else:
                """ NOTE
                Вот тут мы отправляем на проверку
                """
                await message.answer(
                    text=texts.Quests.Texts.idea_send_admins,
                    reply_markup=await reply.main_menu(user)
                )

        except ListLengthChangedError:
            pass
        except NoDesiredTypeError:
            await state.set_state(Daily.wait)
        except:
            logger.exception("Неизвестная ошибка")
            await message.answer(
                text=texts.Error.Notif.undefined_error
            )
            return

    async def fast_success(
        self,
        call: types.CallbackQuery,
        user: Users,
        quest_id: str
        ) -> Optional[bool]:
        target_user = await UserMethods().get_by_user_id(user.user_id)
        
        reward_starcoins = await UseQuestsMethods().create_idea_daily(target_user.id, quest_id)
        try:
            await call.answer(
                text=f"✅ +{reward_starcoins}★ ✅"
                )
        except:
            pass
        return True
            
    
class IdeaQuest:

    async def get_idea_quest(
        self,
        message: types.Message,
        user: Users,
        quest_id: int
        ) -> None:
        quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            await message.delete()
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Quests.Error.no_quest,
                reply_markup=await reply.main_menu(user)
            )
        else:
            idea_quest: IdeaQuests = quest.quest_data
            
            text = texts.Quests.Texts.idea_quest.format(
                    title=idea_quest.title,
                    description=idea_quest.description,
                    price=idea_quest.reward_starcoins
                )
            try:
                await message.edit_text(
                    text=text,
                    reply_markup=await inline.idea_quest(quest.id),
                    disable_web_page_preview=True
                )
            except:
                await message.bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=await inline.idea_quest(quest.id),
                    disable_web_page_preview=True
                )
                await message.delete()
            
    async def action_idea_quest(
        self,
        call: types.CallbackQuery,
        state: FSMContext,
        user: Users,
        quest_id: int
        ) -> None:
        quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            await call.message.delete()
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Quests.Error.no_quest,
                reply_markup=await reply.main_menu(user)
            )
        else:
            idea_quest: IdeaQuests = quest.quest_data
            
            text = texts.Quests.Texts.idea_call_action.format(
                    call_action=idea_quest.call_action
                )
            try:
                await call.message.edit_text(
                    text=text,
                    reply_markup=await reply.back(idea_quest.title),
                    disable_web_page_preview=True
                )
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=await reply.back(idea_quest.title),
                    disable_web_page_preview=True
                )
                await call.message.delete()
            
            await state.set_state(
                Idea.wait
            )
            await state.update_data(
                id=quest.id,
                success_admin=quest.success_admin,
                type_quest=quest.type_quest.value,
                title=idea_quest.title,
                content=idea_quest.content
            )

    async def check_idea_quest(
        self,
        message: types.Message,
        state: FSMContext,
        user: Users,
        **kwargs
        ) -> None:
        try:
            if config.debug:
                logger.debug(message)

                if not kwargs.get("state_data"):
                    state_data: dict = await state.get_data()
                else:
                    state_data = kwargs["state_data"]
                    
                logger.debug(state_data)
                
                # msg_datas = await QuestAggregator().add_message(
                #     user.user_id,
                #     message,
                #     state,
                #     state_data
                # )
                if not kwargs.get("msg_datas"):
                    msg_datas = await QuestAggregator().add_message(
                        user.user_id,
                        message,
                        state,
                        state_data
                    )
                else:
                    msg_datas = kwargs["msg_datas"]
                    
                logger.debug(msg_datas)
                
                # if not kwargs.get("test"):
                #     num_test = random.randint(100000, 999999)
                #     del state_data['user']
                #     with open(config.BASE_DIR / "test.json", "r", encoding="utf-8") as file:
                #         file_str = file.read()
                #         file_dict = json.loads(file_str)
                    
                #     file_dict[num_test] = {
                #             "message": message.model_dump_json(exclude={'datetime', 'link_preview_options', 'default', 'link_preview_prefer_small_media'}),
                #             "user": user.model_dump_json(),
                #             "state_data": state_data,
                #             "msg_datas": msg_datas
                #             }
                        
                #     with open(config.BASE_DIR / "test.json", "w", encoding="utf-8") as file:
                #         file.write(json.dumps(file_dict, indent=2, ensure_ascii=False))
                        
            else:
                state_data: dict = await state.get_data()
                msg_datas = await QuestAggregator().add_message(
                    user.user_id,
                    message,
                    state,
                    state_data
                )

            success_admin = state_data['success_admin']
            logger.debug(
                f"{success_admin} -> {user.user_id}"
            )
            
            send_message = await Func.constructor_func_to_mailing_msgs(
                message.bot,
                msg_datas['text'],
                msg_datas['content_type'],
                msg_datas['media_content'],
                msg_datas['media_group_id'],
                False,
                reply_markup=await inline.verif_idea_admin(
                    state_data['id'],
                    user.user_id
                ) if success_admin else None
            )
            
            # NOTE это для того чтобы написать в чат с логами имитируя объект Users
            User = namedtuple('User', ['user_id'])
            local_chat_id = config.smm_chat if "SMM" in state_data['title'] else config.quests_chat
            user_obj = User(user_id=local_chat_id)
            
            await message.bot.send_message(
                chat_id=local_chat_id,
                text=texts.Quests.Texts.log_idea_success.format(
                    tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                    title_quest=state_data['title'],
                    role=user.role_name,
                    gender=await Func.gender_name(user.gender, user.role_private),
                    age=(datetime.now(pytz.timezone('Europe/Moscow')) - user.age).days // 365,
                    title="Имя" if user.role_private == "child" else "ФИО",
                    supername=user.supername,
                    name=user.name,
                    nickname=user.nickname,
                    phone=user.phone,
                    created_at=await Func.format_date(user.created_at),
                    referral_count=await UserMethods().get_referral_count(user.user_id)
                )
            )
            await state.clear()
            
            reward_starcoins_bool = await UseQuestsMethods().create_idea_daily(
                user.id,
                state_data['id']
            )

            await send_message(
                user_obj
            )
            
            if type(reward_starcoins_bool) in [float,int]:
                await message.answer(
                    text=texts.Quests.Texts.fast_approve.format(
                        starcoins=reward_starcoins_bool
                        ),
                    reply_markup=await reply.main_menu(user)
                )
            else:
                """ NOTE
                Вот тут мы отправляем на проверку
                """
                await message.answer(
                    text=texts.Quests.Texts.idea_send_admins,
                    reply_markup=await reply.main_menu(user)
                )

        except ListLengthChangedError:
            pass
        except NoDesiredTypeError:
            await state.set_state(Idea.wait)
        except:
            logger.exception("Неизвестная ошибка")
            await message.answer(
                text=texts.Error.Notif.undefined_error
            )

    async def success_idea(
        self,
        call: types.CallbackQuery,
        user: Users,
        quest_id: str,
        user_id: str
        ) -> None:
        target_user = await UserMethods().get_by_user_id(user_id)
        logger.debug(f"success_idea {user.user_id=} {user_id=} {quest_id=}")
                    
        reward_starcoins = await UseQuestsMethods().success_idea_daily(target_user, quest_id)
        logger.debug(f"success_idea {reward_starcoins=}")

        if reward_starcoins:
            await call.message.bot.send_message(
                chat_id=target_user.user_id,
                text=texts.Quests.Texts.idea_approve.format(
                    starcoins=reward_starcoins
                )
            )
            await call.answer(
                text="✅ Все сделано ✅"
                )
        else:
            await call.answer(
                text=texts.Quests.Texts.already
                )

        await asyncio.sleep(1)
        
        try:
            await call.message.delete_reply_markup()
        except:
            await call.answer(
                text="💡Клавиатура не удалится💡"
                )
        
    async def delete_idea(
        self,
        call: types.CallbackQuery,
        user: Users,
        quest_id: str,
        user_id: str
        ) -> None:
        target_user = await UserMethods().get_by_user_id(user_id)
        logger.debug(f"delete_idea {user.user_id=} {user_id=} {quest_id=}")
        
        quest_data: dict = await UseQuestsMethods().delete(
            target_user.id,
            int(quest_id)
        )
        logger.debug(f"delete_idea {quest_data=}")
        
        if quest_data and not quest_data.get("error"):
            await bot.send_message(
                chat_id=target_user.user_id,
                text=texts.Quests.Texts.idea_deny.format(quest_data['title']),
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=texts.Quests.Btns.go_activate,
                                callback_data="get_quest|{}|{}".format(
                                    quest_data['type_quest'],
                                    quest_id
                                )
                            )
                        ]
                    ]
                )
            )
        else:
            await Func.send_error_to_developer(
                f"user_id={user_id} quest_id={quest_id}\nНажали на кноку отклонить но связи юзера и квеста НЕТ\n{quest_data}"
            )
            await call.answer(
                text="❗️Квест уже выполнен у пользователя❗️"
                )
            await asyncio.sleep(1)

        try:
            await call.message.delete_reply_markup()
        except:
            await call.answer(
                text="💡Клавиатура не удалится💡"
                )
            await asyncio.sleep(1)
        
        await call.answer(
            text="❌ Отклонено ❌"
            )
        

class SubscribeQuests:

    async def get_sub_quest(
        self,
        call: types.CallbackQuery,
        state: FSMContext,
        user: Users,
        quest_id: int
        ) -> None:
        """
        Отправляем сообщение с информацией о конкретном задании
        """
        quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            await call.message.delete()
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Quests.Error.no_quest,
                reply_markup=await reply.main_menu(user)
            )
        else:
            """NOTE
            вот тут разделение на тг и ВК
            причем когда все для провери ВК будет готово надо вернуться сюда
            от сюда вывод: две проверки, на тип и возможность проверить
            """
            sub_quest: SubscribeQuest = quest.quest_data
            
            if sub_quest.type.value in ["tg", "vk"]:
                text = texts.Quests.Texts.sub_quest.format(
                        title=sub_quest.title if not sub_quest.description else f"{sub_quest.title}\n\n{sub_quest.description}",
                        price=sub_quest.reward_starcoins
                    )
                try:
                    await call.message.edit_text(
                        text=text,
                        reply_markup=await inline.check_sub(quest.id),
                        disable_web_page_preview=True
                    )
                except:
                    await call.message.bot.send_message(
                        chat_id=user.user_id,
                        text=text,
                        reply_markup=await inline.check_sub(quest.id),
                        disable_web_page_preview=True
                    )
                    await call.message.delete()
                
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=sub_quest.url
                )
            else:
                logger.error(f"{sub_quest.type=} <- как это сюда попало?")

    async def check_subscribe_quest(
        self,
        call: types.CallbackQuery, 
        state: FSMContext,
        user: Users,
        quest_id: int
        ) -> Tuple[bool, Union[str,Quests]]:
        """
        Проверка юзера в нужном чате
        """
        try:
            quest: Quests = await QuestsMethods().get_by_id(user.user_id, quest_id)
            if not quest:
                return False, texts.Quests.Error.no_quest
            
            sub_quest = quest.quest_data

            if sub_quest.type.value == "tg":
                if (
                    quest.type_quest.value != "subscribe" or
                    not isinstance(sub_quest, SubscribeQuest)
                    ):
                    return False, texts.Error.Notif.undefined_error
                
                try:
                    # Проверяем статус пользователя в чате
                    chat_member = await call.bot.get_chat_member(
                        chat_id=sub_quest.chat_id_name,
                        user_id=user.user_id
                    )
                    
                    # Проверяем, что пользователь не покинул чат
                    if chat_member.status in ('left', 'kicked', 'restricted'):
                        return False, texts.Error.Notif.dont_subscribe
                        
                    return True, quest
                except:
                    logger.exception("chat_member = await bot.get_chat_member(sub_quest.chat_id_name, user.user_id)")
                    return False, texts.Error.Notif.dont_subscribe
            elif sub_quest.type.value == "vk":
                if (
                    quest.type_quest.value != "subscribe" or
                    not isinstance(sub_quest, SubscribeQuest)
                    ):
                    return False, texts.Error.Notif.undefined_error

                if not user.vk_id:
                    text, keyboard = await VKForms.get_vk_profile_link(state, quest.id)
                    try:
                        await call.message.edit_text(
                            text=text,
                            reply_markup=keyboard,
                            disable_web_page_preview=True
                        )
                    except:
                        await call.message.bot.send_message(
                            chat_id=user.user_id,
                            text=text,
                            reply_markup=keyboard,
                            disable_web_page_preview=True
                        )
                        await call.message.delete()
                        
                    return False, False

                result: bool = await VKForms.verif_vk_chat(
                    user.vk_id,
                    sub_quest.chat_id_name,
                    sub_quest.group_token
                )
                
                if result:
                    return True, quest
                else:
                    return False, texts.Quests.VK.no_sub
        except:
            logger.exception("Ошибка проверки подписки")
            return False, texts.Error.Notif.undefined_error

    async def verif_vk_profile_link(
        self,
        state: FSMContext,
        user: Users,
        url: str
        ) -> Tuple[
            Tuple[str],
            Tuple[Optional[
                Union[
                    types.ReplyKeyboardMarkup,
                    types.InlineKeyboardMarkup
                    ]
                ]
            ]
        ]:
        user_name_or_id = await VKForms.strip_url(url)
        logger.debug(user_name_or_id)
        
        state_data = await state.get_data()
        quest_id = state_data['quest_id']
        
        quest = await QuestsMethods().get_by_id(user.user_id, quest_id)
        if not quest:
            return ((texts.Shop.Error.no_quest,), (None,))
        
        sub_quest = quest.quest_data
        
        vk_id = await VKForms.get_user_id(
            user_name_or_id,
            sub_quest.group_token
        )
        
        if not vk_id:
            return (
                (
                    texts.Quests.VK.uncorrect_url.format(
                        user_name_or_id=user_name_or_id
                        ),
                    ),
                (await reply.back(),)
            )
        else:
            result = await UserMethods().update_vk_id(
                user,
                vk_id
            )
            if not result:
                return (
                    (texts.Quests.VK.user_exists,),
                    (await reply.back(),)
                )
                
            await state.clear()
            
            return (
                (
                    texts.Quests.Texts.sub_quest.format(
                        title=sub_quest.title if not sub_quest.description else f"{sub_quest.title}\n\n{sub_quest.description}",
                        price=sub_quest.reward_starcoins
                        ),
                    sub_quest.url
                    ),
                (await inline.check_sub(quest_id),await reply.main_menu(user))
                )

    async def success_subscribe_quest(
        self,
        call: types.CallbackQuery,
        user: Users,
        quest: Quests
        ) -> None:
        """
        Покупка товара
        """
        async with lock:
            if await UseQuestsMethods().get_connection(user, quest):
                try:
                    await call.message.delete()
                except:
                    pass
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=texts.Quests.Texts.already
                )
                return
            
        sub_quest = await UseQuestsMethods().create_quest(user, quest)

        try:
            await call.message.delete()
        except:
            pass
        
        await call.message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Quests.Texts.sub_success.format(
                title=sub_quest.title,
                description=sub_quest.description,
                starcoins=sub_quest.reward_starcoins
            )
        )

        await call.message.bot.send_message(
            chat_id=config.quests_chat if config.quests_chat else user.user_id,
            text=texts.Quests.Texts.log_sub_success.format(
                tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                title_quest=sub_quest.title,
                description=sub_quest.description,
                starcoins=sub_quest.reward_starcoins,
                role=user.role_name,
                gender=await Func.gender_name(user.gender, user.role_private),
                age=(datetime.now(pytz.timezone('Europe/Moscow')) - user.age).days // 365,
                title="Имя" if user.role_private == "child" else "ФИО",
                supername=user.supername,
                name=user.name,
                nickname=user.nickname,
                phone=user.phone,
                created_at=await Func.format_date(user.created_at),
                referral_count=await UserMethods().get_referral_count(user.user_id)
            )
        )


class Quests(SubscribeQuests, IdeaQuest, DailyQuest, QuestPagination):
    
    def __init__(self):
        super().__init__()
        self.line_btns = 4

    async def viue_all(
        self,
        user: Users,
        *,
        call: types.CallbackQuery = None,
        message: types.Message = None,
        pagination: Optional[int] = None
        ) -> None:
        """
        Отправляем сообщение с информацией о заданиях
        """
        active_quests = await QuestsMethods().get_active_quests(user)
        
        available_quests = []
        for quest in active_quests:
            if quest.role is None or quest.role == user.role_private:
                available_quests.append(quest)

        last_page = math.ceil(len(available_quests) / self.line_btns)
        
        if pagination is None:
            pagination = await self.get_page_number(user)
        else:
            await self.set_page_number(user, pagination)
            
        pagination = min(pagination, last_page)
        
        catalog_data = dict()
        last_index = pagination * self.line_btns
        start_index = last_index - self.line_btns
        for index, quest in enumerate(available_quests):
            if (
                index >= start_index and
                index < last_index
                ):
                sub_quest = quest.quest_data
                catalog_data[sub_quest.title] = (
                    f"get_quest|{quest.type_quest.value}|{quest.id}"
                )

        if len(catalog_data) < 1:
            if message:
                await message.bot.send_message(
                    chat_id=user.user_id,
                    text=texts.Quests.Error.no_quests
                )
            else:
                try:
                    await call.answer(
                        texts.Quests.Error.no_quests,
                    )
                    await call.message.delete()
                except:
                    pass
            return
        
        text = texts.Quests.Texts.catalog
        keyboard: types.InlineKeyboardMarkup = await inline.catalog(catalog_data)
        pagination_kb = await inline.pagination(
            "all_quests",
            pagination,
            last_page
        )
        
        keyboard.inline_keyboard.extend(pagination_kb.inline_keyboard)
        keyboard.inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.back,
                    callback_data="back_to_profile"
                )
            ]
        )

        if message:
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=keyboard
            )
        else:
            try:
                await call.message.edit_text(
                    text=text,
                    reply_markup=keyboard
                )
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=keyboard
                )
                await call.message.delete()

    async def action_daily_quest(
        self,
        call: types.CallbackQuery,
        state: FSMContext,
        user: Users,
        quest_id: int
        ) -> Optional[bool]:
        if await super().action_daily_quest(call,state,user,quest_id):
            await self.viue_all(
                user,
                call=call
            )
