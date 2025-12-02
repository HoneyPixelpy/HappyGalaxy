import asyncio
import datetime
import json
from typing import Any, Coroutine, List, Optional, Set, Tuple, Union
import aiofiles
from aiogram import Bot, types
from loguru import logger
import pytz

from MainBot.base.models import Users
from config import BASE_DIR, file_lock
from MainBot.config import bot
from .Text import TextProcessor

# config_json_path = BASE_DIR / "Settings/config_json.json"
config_from_forwards = BASE_DIR / "Settings/config_from_forwards.json"


async def load_config_from_forwards(
    *args,
    **kwargs
    ) -> dict:
    async with file_lock:
        async with aiofiles.open(BASE_DIR / config_from_forwards, 'r', encoding='utf-8') as f:
            data = await f.read()
            return json.loads(data)


class Func:
    
    MAX_CAPTION_LENGTH = 1024  # Лимит Telegram для подписи к медиа
    MAX_MESSAGE_LENGTH = 4096  # Лимит Telegram для обычного сообщения
    
    @classmethod
    async def get_media_types(
        cls,
        form_name: str = 'all'
        ) -> Set[str]:
        if form_name == 'visible':
            return (
                'photo',
                'animation',
                'video',
                'document',
                'video_note',
                'sticker'
            )
        else:
            return (
                'photo',
                'animation',
                'video',
                'document',
                'video_note',
                'voice',
                'sticker',
                'audio'
            )

    @classmethod
    async def get_emoji_number(
        cls,
        number: int
        ) -> str:
        result = ''
        for num in str(number):
            if num == '0':
                result += '0️⃣'
            elif num == '1':
                result += '1️⃣'
            elif num == '2':
                result += '2️⃣'
            elif num == '3':
                result += '3️⃣'
            elif num == '4':
                result += '4️⃣'
            elif num == '5':
                result += '5️⃣'
            elif num == '6':
                result += '6️⃣'
            elif num == '7':
                result += '7️⃣'
            elif num == '8':
                result += '8️⃣'
            elif num == '9':
                result += '9️⃣'
        return result

    @classmethod
    async def format_tg_info(
        cls,
        uer_id: Union[str,int],
        user_name: Optional[str]
        ) -> str:
        text = f"<code>{uer_id}</code>"
        if user_name:
            text += f" | @{user_name}"
        return text

    @classmethod
    async def format_tg_names(
        cls,
        first_name: str,
        last_name: Optional[str]
        ) -> str:
        text = first_name
        if last_name:
            text += f" {last_name}"
        return text

    @classmethod
    async def format_nickname(
        cls,
        user_id: int,
        nickname: Optional[str],
        name: str,
        supername: Optional[str]
        ) -> str:
        if nickname and str(nickname) != 'None':
            return nickname
        elif supername and str(supername) != 'None':
            return f"{supername} {name}"
        else:
            return str(user_id)

    @classmethod
    async def gender_name(
        cls,
        gender: str,
        role: str
        ) -> str:
        if gender == "man":
            return "👦 Мальчик" if role == "child" else "👦 Мужчина"
        elif gender == "woman":
            return "👧 Девочка" if role == "child" else "👧 Женщина"
        else:
            return gender

    @classmethod
    async def pin_msg_delete_notification(
        cls,
        bot: Bot,
        user_id: int,
        message_id: int,
        delete_msg_add: int = 1
        ) -> None:
        """
        Закрепляем сообщение.
        """
        await bot.pin_chat_message(
            chat_id=user_id,
            message_id=message_id,
            disable_notification=True
        )
        
        notification_message_id = message_id + delete_msg_add

        try:
            await bot.delete_message(
                chat_id=user_id, 
                message_id=notification_message_id
                )
        except:
            logger.warning("Не смогли удалить сообщение")
        
    @classmethod
    async def constructor_func_to_mailing_one_msg(
        cls,
        bot: Bot,
        media_content: str,
        media_type: str,
        pin_bool: bool,
        text: str,
        reply_markup = None
        ) -> Coroutine[Any, Any, None]:
        """
        Собираем функцию для рассылки.
        """
        if media_type == 'photo':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_photo(
                    chat_id=user.user_id,
                    photo=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif media_type == 'animation':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_animation(
                    chat_id=user.user_id,
                    animation=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif media_type == 'video':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_video(
                    chat_id=user.user_id,
                    video=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif media_type == 'document':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_document(
                    chat_id=user.user_id,
                    document=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif media_type == 'video_note':
            async def mailing_func(user: Users) -> None:
                mailing_message = await bot.send_video_note(
                    chat_id=user.user_id,
                    video_note=media_content,
                    reply_markup=reply_markup
                    )
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id
                    )
            return mailing_func
        elif media_type == 'voice':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_voice(
                    chat_id=user.user_id,
                    voice=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif media_type == 'sticker':
            async def mailing_func(user: Users) -> None:
                mailing_message = await bot.send_sticker(
                    chat_id=user.user_id,
                    sticker=media_content,
                    reply_markup=reply_markup
                    )
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id
                    )
            return mailing_func
        elif media_type == 'audio':
            async def mailing_func(user: Users) -> None:
                delete_msg_add = 1
                text_parts = TextProcessor.prepare_text_parts(
                    text
                )
                mailing_message = await bot.send_audio(
                    chat_id=user.user_id,
                    audio=media_content,
                    caption=text_parts.pop(0),
                    reply_markup=reply_markup if not text_parts else None
                    )
                for part_text in text_parts:
                    if part_text or (part_text == text_parts[-1] and reply_markup):
                        await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text if part_text else "⬆️ Клавиатура ⬆️",
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                        delete_msg_add += 1
                if pin_bool:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id,
                        delete_msg_add
                    )
            return mailing_func
        elif not media_type:
            async def mailing_func(user: Users) -> None:
                text_parts = TextProcessor.prepare_text_parts(
                    text,
                    first_len=cls.MAX_MESSAGE_LENGTH
                )
                for part_text in text_parts:
                    if part_text:
                        mailing_message = await bot.send_message(
                            chat_id=user.user_id,
                            text=part_text,
                            disable_web_page_preview=True,
                            reply_markup=reply_markup if part_text == text_parts[-1] else None
                            )
                if pin_bool and mailing_message:
                    await cls.pin_msg_delete_notification(
                        bot,
                        user.user_id,
                        mailing_message.message_id
                    )
            return mailing_func
        else:
            logger.error("Неопознанный ключ!")

    @classmethod
    async def constructor_album_to_mailing_one_msg(
        cls,
        bot: Bot,
        media_content: str,
        media_type: str,
        pin_bool: bool,
        text: str,
        album_list_indices: List[int],
        reply_markup = None
        ) -> Coroutine[Any, Any, None]:
        """
        Собираем функцию для рассылки с альбомом.
        """
        album_list_medias: List[types.MediaUnion] = []
        plain_texts = []
        
        for i, album_indice in enumerate(album_list_indices):
            text_parts = TextProcessor.prepare_text_parts(
                text[album_indice]
            )
            if media_type[album_indice] == 'photo':
                media_item = types.InputMediaPhoto(
                    media=media_content[album_indice],
                    caption=text_parts.pop(0)
                )
            elif media_type[album_indice] == 'video':
                media_item = types.InputMediaVideo(
                    media=media_content[album_indice],
                    caption=text_parts.pop(0)
                )
            elif media_type[album_indice] == 'animation':
                media_item = types.InputMediaAnimation(
                    media=media_content[album_indice],
                    caption=text_parts.pop(0)
                )
            elif media_type[album_indice] == 'document':
                media_item = types.InputMediaDocument(
                    media=media_content[album_indice],
                    caption=text_parts.pop(0)
                )
            elif media_type[album_indice] == 'audio':
                media_item = types.InputMediaAudio(
                    media=media_content[album_indice],
                    caption=text_parts.pop(0)
                )
            else:
                continue
            
            # NOTE text_parts вожно будет заполнен только у одного медиа в группе максимум
            if text_parts:
                plain_texts.extend(text_parts)
            
            album_list_medias.append(media_item)

        async def func_to_mailing(user: Users) -> None:
            messages = await bot.send_media_group(
                chat_id=user.user_id,
                media=album_list_medias
            )
            delete_msg_add = len(messages)
        
            for plain_text in plain_texts:
                if plain_text:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text=plain_text,
                        disable_web_page_preview=True
                        )
                    delete_msg_add += 1
        
            if pin_bool:
                await cls.pin_msg_delete_notification(
                    bot,
                    user.user_id,
                    messages[0].message_id,  # Закрепляем первое сообщение альбома
                    delete_msg_add
                )
        
            if reply_markup:
                await messages[0].reply(
                    text="⬆️ Клавиатура ⬆️",
                    reply_markup=reply_markup
                    
                )
                
        return func_to_mailing

    @classmethod
    async def send_error_to_developer(
        cls,
        text: str,
        bot: Bot = bot
        ) -> None:
        tz = pytz.timezone('Europe/Moscow')
        text = f'{datetime.datetime.now(tz)}\n\n' + text
        await bot.send_message(chat_id=1894909159, text=text, parse_mode=None)

    @classmethod
    async def format_date(
        cls,
        data: datetime.datetime
        ) -> str:
        RUSSIAN_MONTHS = (
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        )
        return f"{data.day} {RUSSIAN_MONTHS[data.month - 1]} {data.year}"

    @classmethod
    async def parsing_message(
        cls,
        message: types.Message
    ) -> Tuple[
            Optional[str], 
            Optional[str], 
            Optional[str],
            Optional[str]
        ]:
        """
        Создает функцию рассылки на основе переданного сообщения.
        
        :param message: Сообщение для анализа
        :return: (text, content_type, media_content, media_group_id)
        """
        content_type = None
        media_content = None
        text = message.html_text
        media_group_id = message.media_group_id

        if message.photo:
            content_type = 'photo'
            media_content = message.photo[-1].file_id  # Берем самое высокое качество
        elif message.video:
            content_type = 'video'
            media_content = message.video.file_id
        elif message.document:
            content_type = 'document'
            media_content = message.document.file_id
        elif message.audio:
            content_type = 'audio'
            media_content = message.audio.file_id
        elif message.video_note:
            content_type = 'video_note'
            media_content = message.video_note.file_id
        elif message.voice:
            content_type = 'voice'
            media_content = message.voice.file_id
        elif message.animation:
            content_type = 'animation'
            media_content = message.animation.file_id
        elif message.sticker:
            content_type = 'sticker'
            media_content = message.sticker.file_id

        return text, content_type, media_content, media_group_id

    @classmethod
    async def constructor_func_to_mailing_msgs(
        cls,
        bot: Bot,
        text: List[Optional[str]],
        media_type: List[Optional[str]],
        media_content: List[Optional[str]],
        media_group_id: List[Optional[int]],
        pin_bool: bool,
        reply_markup: Optional[bool] = None
        ) -> Coroutine[Any, Any, None]:
        """
        Собираем функцию для рассылки.
        """
        result_methods = []
                
        # Проверяем совместимость типов для альбома
        album_lists_indices, separate_indices = cls._can_form_album(media_group_id)
        first_indice = 0
        last_indice = len(media_content) - 1

        if album_lists_indices:
            func_to_mailing_methods = []
            
            for album_list_indices in album_lists_indices:
                if first_indice in album_list_indices:
                    pin = pin_bool
                else:
                    pin = None
                
                if last_indice in album_list_indices:
                    markup = reply_markup
                else:
                    markup = None
            
                func_to_mailing_methods.append(
                    await cls.constructor_album_to_mailing_one_msg(
                            bot,
                            media_content,
                            media_type,
                            pin,
                            text,
                            album_list_indices,
                            markup
                        )
                    )
                
            async def result_method(user: Users) -> None:
                for func_to_mailing_method in func_to_mailing_methods:
                    await func_to_mailing_method(user)
                    await asyncio.sleep(1)
                
            result_methods.append(result_method)
        
        if separate_indices:
            one_msg_methods = []
            
            for index, _ in enumerate(media_content):
                if index in separate_indices:
                    if index == first_indice:
                        pin = pin_bool
                    else:
                        pin = None
                    
                    if index == last_indice:
                        markup = reply_markup
                    else:
                        markup = None
                        
                    one_msg_methods.append(
                        await cls.constructor_func_to_mailing_one_msg(
                            bot,
                            media_content[index],
                            media_type[index],
                            pin,
                            text[index],
                            markup
                        )
                    )
            
            async def result_method(user: Users) -> None:
                for one_msg_method in one_msg_methods:
                    await one_msg_method(user)
                    await asyncio.sleep(1)
                    
            result_methods.append(result_method)

        async def method(user: Users) -> None:
            for result_method in result_methods:
                await result_method(user)
                await asyncio.sleep(1)
        
        return method

    @classmethod
    def _can_form_album(
        cls,
        media_group_ids: List[Optional[int]]
        ) -> tuple[
            List[List[int]], 
            List[int]
            ]:
        """
        на основе собранной инфы об media_group_id
            те что не имеют этого значеня отправляются отдельно;
            те что имеют добавляются в список с теми же media_group_id
        """
        album_indices = []
        media_groups = {}
        separate_indices = []
        
        for i, group_id in enumerate(media_group_ids):
            if group_id is not None:
                if group_id not in media_groups:
                    media_groups[group_id] = []
                media_groups[group_id].append(i)
            else:
                separate_indices.append(i)
                
        else:
            for group in media_groups.values():
                album_indices.append(group)
        
        return album_indices, separate_indices

