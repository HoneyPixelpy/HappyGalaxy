import json
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

from loguru import logger
from redis.asyncio import Redis
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup

from config import BASE_DIR, debug
from Redis.main import RedisManager
from MainBot.utils.errors import RelevanceError


@dataclass
class MessageState:
    """Состояние сообщения в Redis"""
    chat_id: int
    message_id: int
    user_id: int
    image_key: str
    created_at: datetime


class MessageCache:
    
    redis: Optional[Redis] = None
    
    @classmethod
    async def _check(
        cls
    ) -> Any:
        if not cls.redis:
            cls.redis = await RedisManager().get_redis()
    
    @classmethod
    async def get(
        cls,
        key: str
    ) -> Any:
        await cls._check()
        return await cls.redis.get(key)
    
    @classmethod
    async def hgetall(
        cls,
        key: str
    ) -> Any:
        await cls._check()
        return await cls.redis.hgetall(key)
    
    @classmethod
    async def setex(
        cls,
        key: str,
        ttl: int,
        data: Dict
    ) -> None:
        await cls._check()
        await cls.redis.setex(key, ttl, data)

    @classmethod
    async def delete(
        cls,
        key: str
    ) -> None:
        await cls._check()
        return await cls.redis.delete(key)

    @classmethod
    async def cleanup_old_states(
        cls,
        prefix: str,
        ttl: int
    ) -> None:
        await cls._check()
        keys = await cls.redis.keys(f"{prefix}:*")
        if keys:
            pipe = cls.redis.pipeline()
            for key in keys:
                pipe.expire(key, ttl)
            await pipe.execute()


class Cache:

    def __init__(self, ttl: int = 1800):
        self.redis = MessageCache
        self.ttl_cache = 1860
        self.ttl_delete = ttl
        self.prefix = "msg_state:"

    async def _get_state(self, user_id: int, chat_id: int) -> Optional[MessageState]:
        """Из Redis"""
        key = f"{self.prefix}:{user_id}:{chat_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        state_data = json.loads(data)
        return MessageState(
            user_id=state_data["user_id"],
            chat_id=state_data["chat_id"],
            message_id=state_data["message_id"],
            image_key=state_data["image_key"],
            created_at=datetime.fromisoformat(state_data["created_at"])
        )

    async def _save_state(
        self,
        user_id: int,
        chat_id: int,
        message: Message,
        image_key: str,
        created_at: datetime
    ) -> MessageState:
        """В Redis"""
        key = f"{self.prefix}:{user_id}:{chat_id}"
        state = MessageState(
            chat_id=chat_id,
            message_id=message.message_id,
            user_id=user_id,
            image_key=image_key,
            created_at=created_at.isoformat()
        )
        await self.redis.setex(key=key, ttl=self.ttl_cache, data=json.dumps(state.__dict__))
        return state

    async def _delete_state(self, user_id: int, chat_id: int) -> None:
        """
        Удаляет состояние сообщения из Redis и само сообщение из Telegram
        """
        key = f"{self.prefix}:{user_id}:{chat_id}"
        await self.redis.delete(key)

    async def _get_geo_hunt(self, user_id: int) -> Dict:
        """
        Есть ли данные к игре ?
        """
        return await self.redis.hgetall(f"geo_hunt_session:{user_id}")

    async def _clear_geo_hunt(self, user_id: int) -> None:
        """
        Удаляем запись из redis
        которая нужна для работы геохантера
        """
        await self.redis.delete(f"geo_hunt_session:{user_id}")


class File:
    
    def __init__(self):
        self.images_path = Path(BASE_DIR / "Settings/menu_imgs.json")
        self.images_cache = self._load_images()
        self.variant = "test" if debug else "main"
    
    def _load_images(self) -> Dict[str, str]:
        """Загружает словарь изображений из JSON"""
        try:
            with open(self.images_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e: # File
            logger.error(f"Cannot load images.json: {e}")
            return {}
    
    def get_image_file_id(self, section: str) -> Optional[str]:
        """Получает file_id по ключу section/variant"""
        return self.images_cache.get(section, {}).get(self.variant)


class MessageManager:
    """
    Универсальный менеджер сообщений с edit/delete через Redis.
    Предотвращает засорение чата.
    """
    
    def __init__(self, obj: Message | CallbackQuery, user_id: int, message_id: Optional[int] = None):
        self.obj = obj
        self.bot = obj.bot
        
        if isinstance(obj, Message):
            self.chat_id = obj.chat.id
            self.message_id = obj.message_id if not message_id else message_id
        else:
            self.chat_id = obj.message.chat.id
            self.message_id = obj.message.message_id if not message_id else message_id
        
        self.user_id = user_id
        self.file = File()
        self.cache = Cache()
    
    async def send_or_edit(
        self,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        image_key: Optional[str] = None  # "menu", "profile", etc.
    ) -> Optional[Message]:
        """
        Отправляет новое или редактирует существующее
        """
        data = await self.cache._get_geo_hunt(self.user_id)
        if data:
            asyncio.create_task(
                self.cache._clear_geo_hunt(self.user_id)
                )
            if isinstance(self.obj, Message):
                try:
                    await self.obj.bot.delete_message(
                        chat_id=self.user_id,
                        message_id=data[b'message_id'].decode()
                    )
                except: # exceptions.TelegramBadRequest
                    pass
        
        old_state = await self.cache._get_state(self.user_id, self.chat_id)
        new_image_file_id = self.file.get_image_file_id(image_key) if image_key else None
        
        Stimestamp = datetime.now()
        
        try:
            new_msg = await self._create_or_edit(
                text, reply_markup, new_image_file_id, old_state, Stimestamp
            )
        except RelevanceError as e:
            logger.error(f"❌ Message was updated exceeding cache on: {e}")
            return None
        
        Etimestamp = datetime.now()
        logger.success(Etimestamp - Stimestamp)
        
        state = await self.cache._save_state(self.user_id, self.chat_id, new_msg, image_key, Etimestamp)
        
        asyncio.create_task(
            self._schedule_delete(state)
            )
        
        return new_msg

    async def _schedule_delete(self, state: MessageState) -> None:
        await asyncio.sleep(1800)

        # Получаем актуальный стейт — вдруг сообщение уже обновили
        current_state = await self.cache._get_state(state.user_id, state.chat_id)
        if not current_state:
            return None

        # Если message_id изменился, значит это уже другое (более новое) сообщение
        if current_state.created_at.isoformat() != state.created_at:
            return None

        # Удаляем сообщение и стейт
        await self._safe_delete(current_state)
        await self.cache._delete_state(state.user_id, state.chat_id)

    async def _create_or_edit(
        self,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup],
        new_image_file_id: Optional[str],
        old_state: Optional[MessageState],
        timestamp: datetime
    ) -> Message:
        """Создаёт новое или редактирует сообщение с умной логикой изображений"""
        if old_state and old_state.message_id:
            old_state = await self._check_current_message(
                old_state
            )
            try:
                # Проверяем, нужно ли менять изображение
                if (
                    new_image_file_id and 
                    new_image_file_id != old_state.image_key
                ):
                    return await self._edit_image(
                        new_image_file_id,
                        old_state.chat_id,
                        old_state.message_id,
                        text,
                        reply_markup
                    )
                else:
                    return await self._edit_text(
                        new_image_file_id,
                        old_state.chat_id,
                        old_state.message_id,
                        text,
                        reply_markup
                    )
                
            except Exception as e: # exceptions.TelegramBadRequest
                logger.error(f"Cannot edit {old_state.message_id}: {e}")
                
                old_state = await self.cache._get_state(self.user_id, self.chat_id)
                
                if old_state.created_at > timestamp:
                    # Значит мы работаем уже с более молодым сообщением
                    raise RelevanceError(timestamp, old_state.created_at)
                
                await self._safe_delete(old_state)
        
        # Создаём новое сообщение
        return await self._send_new(text, reply_markup, new_image_file_id)

    async def _check_current_message(
        self,
        old_state: MessageState
    ) -> MessageState:
        """
        При несоответствии message_id из кеша и текущего нужно удалить старое
        """
        if self.message_id != old_state.message_id:
            
            try:
                await self.bot.delete_message(self.chat_id, old_state.message_id)
            except: # exceptions.TelegramBadRequest
                logger.error("Нету сообщения для удаления")
                
            old_state.message_id = self.message_id
            
        return old_state

    async def _edit_text(
        self,
        new_image_file_id: str,
        chat_id: int,
        message_id: int,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup]
    ) -> Message:
        logger.debug(f"Edited message {message_id}")
        if new_image_file_id:
            return await self.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=text,
                reply_markup=reply_markup
            )
        else:
            return await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
    
    async def _edit_image(
        self,
        new_image_file_id: str,
        chat_id: int,
        message_id: int,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup]
    ) -> Message:
        return await self.bot.edit_message_media(
            media=InputMediaPhoto(
                media=new_image_file_id,
                caption=text
            ),
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    async def _send_new(
        self,
        text: Optional[str],
        reply_markup: Optional[InlineKeyboardMarkup],
        image_file_id: Optional[str]
    ) -> Message:
        """Отправляет новое сообщение"""
        if image_file_id:
            msg = await self.bot.send_photo(
                chat_id=self.chat_id,
                photo=image_file_id,
                caption=text,
                reply_markup=reply_markup
            )
        else:
            msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                reply_markup=reply_markup
            )
        logger.debug(f"Sent new message {msg.message_id}")
        return msg
    
    async def _safe_delete(self, state: MessageState):
        """Безопасное удаление"""
        try:
            await self.bot.delete_message(state.chat_id, state.message_id)
        except Exception as e: # exceptions.TelegramBadRequest
            logger.error(f"Cannot delete {state.message_id}: {e}")
    

