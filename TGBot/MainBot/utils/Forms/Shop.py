import math
from datetime import datetime
from typing import Optional, Tuple, Union
from collections import namedtuple

import pytz
import texts
from aiogram import types
from aiogram.fsm.context import FSMContext
from config import debug, log_chat, shop_chat
from loguru import logger
from MainBot.base.models import Pikmi_Shop, Users
from MainBot.base.orm_requests import Pikmi_ShopMethods, PurchasesMethods, UserMethods
from MainBot.keyboards.inline import IKB as inline
from MainBot.keyboards.reply import KB as reply
from MainBot.state.state import Offer
from MainBot.utils.MyModule import Func
from MainBot.utils.Rabbitmq import RabbitMQ
from Redis.main import RedisManager


class ShopPagination:

    def __init__(self):
        self.redis = RedisManager()
        self.base_key = "shop_pagination"

    async def get_page_number(self, user: Users) -> int:
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

    async def set_page_number(self, user: Users, pagination: int):
        """Установить номер страницы с TTL"""
        try:
            redis_client = await self.redis.get_redis()
            key = f"{self.base_key}:{user.user_id}"

            # Устанавливаем на 1 час (3600 сек)
            await redis_client.setex(key, 3600, pagination)

        except Exception as e:
            logger.error(f"Redis error in set_page_number: {e}")


class Shop(ShopPagination):

    def __init__(self):
        super().__init__()
        self.line_btns = 4

    async def catalog(
        self,
        user: Users,
        *,
        call: types.CallbackQuery = None,
        message: types.Message = None,
        pagination: Optional[int] = None,
    ) -> None:
        """
        Отправляем сообщение с информацией о каталоге
        """
        all_products = await Pikmi_ShopMethods().get_all_products()

        available_products = []
        for product in all_products:
            if product.quantity <= 0:
                continue
            if product.role is None or product.role == user.role_private:
                available_products.append(product)

        last_page = math.ceil(len(available_products) / self.line_btns)

        if pagination is None:
            pagination = await self.get_page_number(user)
        else:
            await self.set_page_number(user, pagination)

        pagination = min(pagination, last_page)

        catalog_data = dict()
        last_index = pagination * self.line_btns
        start_index = last_index - self.line_btns
        for index, product in enumerate(available_products):
            if index >= start_index and index < last_index:
                catalog_data[product.title] = f"get_product|{product.id}"

        if len(catalog_data) < 1:
            if message:
                await message.bot.send_message(
                    chat_id=user.user_id, text=texts.Shop.Error.no_products
                )
            else:
                try:
                    await call.answer(
                        texts.Shop.Error.no_products,
                    )
                    await call.message.delete()
                except:
                    pass
            return

        text = texts.Shop.Texts.catalog.format(
            type_name=user.role_name,
            nickname=await Func.format_nickname(
                user.user_id, user.nickname, user.name, user.supername
            ),
            starcoins=user.starcoins,
        )
        keyboard: types.InlineKeyboardMarkup = await inline.catalog(catalog_data)
        pagination_kb = await inline.pagination("all_products", pagination, last_page)

        keyboard.inline_keyboard.extend(pagination_kb.inline_keyboard)
        keyboard.inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.write_offer, callback_data="write_offer|shop"
                )
            ]
        )
        keyboard.inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.back, callback_data="back_to_profile"
                )
            ]
        )

        if message:
            await message.bot.send_message(
                chat_id=user.user_id, text=text, reply_markup=keyboard
            )
        else:
            try:
                await call.message.edit_text(text=text, reply_markup=keyboard)
            except:
                await call.message.bot.send_message(
                    chat_id=user.user_id, text=text, reply_markup=keyboard
                )
                await call.message.delete()

    async def get_product(
        self, message: types.Message, user: Users, product_id: int
    ) -> None:
        """
        Отправляем сообщение с информацией о конкретном товаре
        """
        product: Pikmi_Shop = await Pikmi_ShopMethods().get_by_id(product_id)
        if not product and product.quantity > 0:
            await message.delete()
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Error.no_product,
                reply_markup=await reply.main_menu(user),
            )
        else:
            text = texts.Shop.Texts.product.format(
                title=product.title,
                description=product.description,
                price=product.price,
                quantity=product.quantity,
            )
            try:
                await message.edit_text(
                    text=text, reply_markup=await inline.buy_product(
                        product.id,
                        "1" if product.delivery_instructions else ""
                        )
                )
            except:
                await message.bot.send_message(
                    chat_id=user.user_id,
                    text=text,
                    reply_markup=await inline.buy_product(
                        product.id,
                        "1" if product.delivery_instructions else ""
                        )
                )
                await message.delete()

    async def check_possibility_purchase(
        self, user: Users, product_id: int
    ) -> Tuple[bool, Union[str, Pikmi_Shop]]:
        """
        Проверка на возможность покупки товара
        """
        product: Pikmi_Shop = await Pikmi_ShopMethods().get_by_id(product_id)
        if not product:
            return False, texts.Shop.Error.no_product

        if product.quantity == 0:
            return False, texts.Shop.Error.no_quantity

        if not debug:
            if user.starcoins < product.price:
                return False, texts.Shop.Error.not_enough_starcoins

        return True, product

    async def buy_product(
        self,
        message: types.Message,
        user: Users,
        product: Pikmi_Shop,
        delivery_data: Optional[str] = None
    ) -> None:
        """
        Покупка товара
        """
        purchases = await PurchasesMethods().create(
            user=user,
            title=product.title,
            description=product.description,
            cost=product.price,
            product_id=product.id,
            delivery_data=delivery_data
        )
        if purchases:
            await message.delete()
            
            user_text = texts.Shop.Texts.buy_head.format(
                    title=product.title, description=product.description
                )
            if not delivery_data:
                user_text += texts.Shop.Texts.buy_no_delivery_data
                keyboard = None
            else:
                user_text += texts.Shop.Texts.buy_delivery_data.format(
                    delivery_data=delivery_data
                )
                keyboard = await inline.success_buy(purchases_id=purchases.id)
            
            await message.bot.send_message(
                chat_id=user.user_id,
                text=user_text
            )

            log_msg = await message.bot.send_message(
                chat_id=shop_chat,
                text=texts.Shop.Texts.log_buy.format(
                    tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                    title_product=product.title,
                    description=product.description,
                    starcoins=product.price,
                    quantity=product.quantity,
                    delivery_data=delivery_data if delivery_data else "Нет",
                    role=user.role_name,
                    gender=await Func.gender_name(user.gender, user.role_private),
                    age=(datetime.now(pytz.timezone("Europe/Moscow")) - user.age).days
                    // 365,
                    title="Имя" if user.role_private == "child" else "ФИО",
                    supername=user.supername,
                    name=user.name,
                    nickname=user.nickname,
                    phone=user.phone,
                    created_at=await Func.format_date(user.created_at),
                    referral_count=await UserMethods().get_referral_count(user.user_id),
                ),
                reply_markup=keyboard
            )

            await RabbitMQ().track_shop(user.user_id, product.id)
            
            await PurchasesMethods().add_message_id(purchases_id=purchases.id, message_id=log_msg.id)
        else:
            try:
                await message.answer(texts.Shop.Error.no_product)
            except:
                await message.bot.send_message(
                    chat_id=user.user_id, text=texts.Shop.Error.no_product
                )

    async def write_offer(
        self, call: types.CallbackQuery, user: Users, state: FSMContext
    ) -> None:
        """
        Предложение на отправку предложения.
        """
        await call.message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Shop.Texts.write_offer,
            reply_markup=await reply.back(),
        )
        await call.message.delete()
        await state.set_state(Offer.shop)

    async def send_offer(
        self, message: types.Message, state: FSMContext, user: Users
    ) -> None:
        """
        Отправляем предложение.
        """
        await message.bot.send_message(
            chat_id=log_chat if log_chat else user.user_id,
            text=texts.Shop.Texts.log_offer.format(
                tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                role=user.role_name,
                gender=await Func.gender_name(user.gender, user.role_private),
                age=(datetime.now(pytz.timezone("Europe/Moscow")) - user.age).days
                // 365,
                title="Имя" if user.role_private == "child" else "ФИО",
                supername=user.supername,
                name=user.name,
                nickname=user.nickname,
                phone=user.phone,
                created_at=await Func.format_date(user.created_at),
                referral_count=await UserMethods().get_referral_count(user.user_id),
                offer=message.html_text,
            ),
        )
        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Shop.Texts.send_offer,
            reply_markup=await reply.main_menu(user),
        )
        await message.delete()
        await state.clear()

    async def view_instructions(
        self, call: types.CallbackQuery, state: FSMContext, user: Users, product_id: str
    ) -> None:
        """
        Выдаем пользователю инструкцию к выдаче товара
        """
        product: Pikmi_Shop = await Pikmi_ShopMethods().get_by_id(product_id)
        await call.bot.send_message(
            chat_id=user.user_id,
            text=texts.Shop.Texts.instructions.format(
                title=product.title,
                instructions=product.instructions
            ),
            reply_markup=await reply.back()
        )
        
        await state.set_state(Offer.instruction)
        await state.update_data(
            product_id=product_id
        )
        await call.message.delete()

    async def cancel_buy(
        self, call: types.CallbackQuery, user: Users, purchases_id: str
    ) -> None:
        """
        Отменяем покупку.
        """
        purchase = await PurchasesMethods().cancel_buy(user, purchases_id)
        if purchase:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Texts.cancel_buy.format(
                    title=purchase.title,
                    starcoins=purchase.cost
                )
            )
            await call.answer(
                texts.Shop.Admin.cancel_buy,
                show_alert=True
            )
        else:
            await call.answer(
                texts.Error.Notif.undefined_error,
                show_alert=True
            )

    async def success_buy(
        self, call: types.CallbackQuery, user: Users, purchases_id: str
    ) -> None:
        """
        Подтверждаем покупку.
        """
        purchase = await PurchasesMethods().success_buy(user, purchases_id)
        if purchase:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Texts.success_buy.format(
                    title=purchase.title
                )
            )
            await call.answer(
                texts.Shop.Admin.success_buy,
                show_alert=True
            )
        else:
            await call.answer(
                texts.Error.Notif.undefined_error,
                show_alert=True
            )

    async def answer_buy(
        self, message: types.Message, answer_message_id: int
    ) -> None:
        """
        Отвечаем на покупку.
        """
        buyer_message_id = await PurchasesMethods().answer_buy(answer_message_id)
        
        if buyer_message_id:
            # NOTE туту надо еще поработать с медиафайлами
            text, content_type, media_content, media_group_id = \
                await Func.parsing_message(message)
            
            if media_group_id:
                send_msg = await Func.constructor_func_to_mailing_msgs(
                    bot=message.bot,
                    text=text,
                    media_type=content_type,
                    media_content=media_content,
                    media_group_id=media_group_id,
                    pin_bool=False
                )
            else:
                send_msg = await Func.constructor_func_to_mailing_one_msg(
                    bot=message.bot,
                    media_content=media_content,
                    media_type=content_type,
                    pin_bool=False,
                    text=text
                )
            
            user = namedtuple('User', ['user_id'])
            user.user_id = buyer_message_id
            
            await send_msg(user)
            
            await message.answer(
                chat_id=message.from_user.id,
                text=texts.Shop.Admin.answer_buy
            )
        else:
            await message.answer(
                chat_id=message.from_user.id,
                text=texts.Error.Notif.undefined_error
            )

        