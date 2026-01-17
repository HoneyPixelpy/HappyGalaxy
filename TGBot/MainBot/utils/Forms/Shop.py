import math
from datetime import datetime
from typing import Optional, Tuple, Union
from collections import namedtuple

import pytz
from Redis.aggregator import ShopAggregator
import texts
from aiogram import types, exceptions
from aiogram.fsm.context import FSMContext
from config import debug, hg_chat, shop_chat
from loguru import logger
from MainBot.base.models import Pikmi_Shop, Users
from MainBot.base.orm_requests import IdempotencyKeyMethods, Pikmi_ShopMethods, PurchasesMethods, UserMethods
from MainBot.keyboards import inline, selector
from MainBot.state.state import Offer
from MainBot.utils.MyModule import Func
from MainBot.utils.MyModule.message import MessageManager
from MainBot.utils.Rabbitmq import RabbitMQ
from MainBot.utils.errors import ListLengthChangedError
from Redis.main import RedisManager
from MainBot.utils.Forms.Menu import Menu


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
        except Exception as e: # Redis
            logger.error(f"Redis error in get_page_number: {e}")
            return 1

    async def set_page_number(self, user: Users, pagination: int):
        """Установить номер страницы с TTL"""
        try:
            redis_client = await self.redis.get_redis()
            key = f"{self.base_key}:{user.user_id}"

            # Устанавливаем на 1 час (3600 сек)
            await redis_client.setex(key, 3600, pagination)

        except Exception as e: # Redis
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
                except: # exceptions.TelegramBadRequest
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
                    text=texts.Btns.back, callback_data="main_menu|back"
                )
            ]
        )

        await MessageManager(
            call if call else message,
            user.user_id
        ).send_or_edit(
            text,
            keyboard,
            "shop"
        )

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
                reply_markup=await selector.main_menu(user),
            )
        else:
            text = texts.Shop.Texts.product.format(
                title=product.title,
                description=product.description,
                price=product.price,
                quantity=product.quantity,
            )
            
            await MessageManager(
                message,
                user.user_id
            ).send_or_edit(
                text,
                await inline.buy_product(
                    product.id,
                    "1" if product.delivery_instructions else ""
                ),
                "shop"
            )

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
        instructions: Optional[str] = None,
        delivery_data: Optional[str] = None,
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
            delivery_data=delivery_data,
            idempotency_key=await IdempotencyKeyMethods.IKgenerate(
                user.user_id,
                message
            )
        )
        if purchases:
            await message.delete()
            
            user_text = texts.Shop.Texts.buy_head.format(
                    title=product.title
                )
            if not delivery_data:
                user_text += texts.Shop.Texts.buy_no_delivery_data.format(
                    description=product.description
                )
                keyboard = None
            else:
                user_text += texts.Shop.Texts.buy_delivery_data
                keyboard = await inline.success_buy(purchases_id=purchases.id)
            
            await message.bot.send_message(
                chat_id=user.user_id,
                text=user_text
            )

            text=texts.Shop.Texts.log_buy.format(
                tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                title_product=product.title,
                description=product.description,
                starcoins=product.price,
                quantity=product.quantity,
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
                referral_count=await UserMethods().get_referral_count(user.user_id)
            )
            
            if instructions and delivery_data:
                if "@" not in delivery_data:
                    delivery_data = "<code>" + delivery_data + "</code>"
                text += texts.Shop.Texts.log_buy_delivery_data.format(
                    instructions=instructions,
                    delivery_data=delivery_data
                )
            
            log_msg = await message.bot.send_message(
                chat_id=shop_chat,
                text=text,
                reply_markup=keyboard
            )
            
            await Menu().main_menu(
                message,
                user
            )
            
            await RabbitMQ().track_shop(user.user_id, product.id)
            
            await PurchasesMethods().add_message_id(purchases_id=purchases.id, message_id=log_msg.message_id)
        else:
            try:
                await message.answer(texts.Shop.Error.no_product)
            except: # exceptions.TelegramBadRequest
                await message.bot.send_message(
                    chat_id=user.user_id, text=texts.Shop.Error.no_product
                )

    async def write_offer(
        self, call: types.CallbackQuery, user: Users, state: FSMContext
    ) -> None:
        """
        Предложение на отправку предложения.
        """
        await MessageManager(
            call,
            user.user_id
        ).send_or_edit(
            texts.Shop.Texts.write_offer,
            await inline.back("all_products"),
            "shop"
        )
        # await call.message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=texts.Shop.Texts.write_offer,
        #     reply_markup=await reply.back(),
        # )
        # await call.message.delete()
        await state.set_state(Offer.shop)

    async def send_offer(
        self, message: types.Message, state: FSMContext, user: Users
    ) -> None:
        """
        Отправляем предложение.
        """
        await message.bot.send_message(
            chat_id=hg_chat if hg_chat else user.user_id,
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
        await MessageManager(
            message,
            user.user_id
        ).send_or_edit(
            texts.Shop.Texts.send_offer,
            await selector.main_menu(user),
            "menu"
        )
        # await message.bot.send_message(
        #     chat_id=user.user_id,
        #     text=texts.Shop.Texts.send_offer,
        #     reply_markup=await selector.main_menu(user),
        # )
        # await message.delete()
        await state.clear()

    async def view_instructions(
        self, call: types.CallbackQuery, state: FSMContext, user: Users, product_id: str
    ) -> None:
        """
        Выдаем пользователю инструкцию к выдаче товара
        """
        product: Pikmi_Shop = await Pikmi_ShopMethods().get_by_id(product_id)
        if product.delivery_instructions:
            await MessageManager(
                call,
                user.user_id
            ).send_or_edit(
                texts.Shop.Texts.instructions.format(
                    title=product.title,
                    instructions=product.delivery_instructions
                ),
                await inline.back(f"get_product|{product_id}"),
                "shop"
            )
            # await call.bot.send_message(
                
            #     chat_id=user.user_id,
            #     text=texts.Shop.Texts.instructions.format(
            #         title=product.title,
            #         instructions=product.delivery_instructions
            #     ),
            #     reply_markup=await inline.back(f"get_product|{product_id}")
            # )
            # await call.message.delete()
            
            await state.set_state(Offer.instruction)
            await state.update_data(
                message_id=call.message.message_id,
                title=product.title,
                product_id=product_id,
                instructions=product.delivery_instructions
            )
        else:
            await call.answer(
                texts.Error.Notif.undefined_error,
                show_alert=True
            )

    async def confirm_buy(
        self, message: types.Message, state: FSMContext, user: Users, delivery_data: str
    ) -> None:
        """
        Подтверждаем покупку.
        """
        data = await state.get_data()
        
        await state.set_state(Offer.confirm)
        await state.update_data(
            delivery_data=delivery_data
        )
        
        message_id = data.get("message_id")
        if message_id:
            try:
                await message.bot.delete_message(
                    chat_id=user.user_id,
                    message_id=message_id
                )
            except: # exceptions.TelegramBadRequest
                pass
            await MessageManager(
                message,
                user.user_id
            ).send_or_edit(
                texts.Shop.Texts.confirm_buy.format(title=data["title"]),
                await inline.confirm_buy(),
                "shop"
            )
        
        else:
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Texts.confirm_buy.format(title=data["title"]),
                reply_markup=await inline.confirm_buy()
            )

    async def cancel_buy(
        self, call: types.CallbackQuery, user: Users, purchases_id: str
    ) -> None:
        """
        Отменяем покупку.
        """
        purchase = await PurchasesMethods().cancel_buy(purchases_id)
        if purchase:
            await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Texts.cancel_buy.format(
                    title=purchase.title,
                    starcoins=purchase.cost
                )
            )
            await call.answer(
                texts.Shop.Admin.cancel_buy
            )
            await call.message.react(
                reaction=[
                    types.ReactionTypeEmoji(emoji="👎")
                ]
            )
            await call.message.delete_reply_markup()
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
        purchase = await PurchasesMethods().success_buy(purchases_id)
        if purchase:
            success_msg = await call.message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Shop.Texts.success_buy.format(
                    title=purchase.title
                )
            )
            
            await PurchasesMethods().product_message_id(
                answer_message_id=call.message.message_id,
                msg_ids=[success_msg.message_id]
                )
            
            await call.answer(
                texts.Shop.Admin.success_buy
            )
            await call.message.react(
                reaction=[
                    types.ReactionTypeEmoji(emoji="❤️")
                ]
            )
            await call.message.edit_reply_markup(
                reply_markup=await inline.rollback_buy(purchase.id)
            )
        else:
            await call.answer(
                texts.Error.Notif.undefined_error,
                show_alert=True
            )

    async def answer_buy(
        self, message: types.Message, state: FSMContext, answer_message_id: int
    ) -> None:
        """
        Отвечаем на покупку.
        """
        try:
            purchase = await PurchasesMethods().answer_buy(answer_message_id)
            
            if purchase:
                """Отправляем сообщение пользователю"""
                msg_datas = await ShopAggregator().add_message(
                    message,
                    state
                )
                
                send_msg = await Func.constructor_func_to_mailing_msgs(
                    message.bot,
                    msg_datas["text"],
                    msg_datas["content_type"],
                    msg_datas["media_content"],
                    msg_datas["media_group_id"],
                    False
                )
                
                user = namedtuple('User', ['user_id'])
                user.user_id = purchase.user.user_id
                
                msg_ids = await send_msg(user)
                if not isinstance(msg_ids, list):
                    msg_ids = [msg_ids]
                
                # await message.bot.send_message(
                #     chat_id=shop_chat,
                #     text=texts.Shop.Admin.answer_buy
                # )
                
                success_msg = await message.bot.send_message(
                    chat_id=user.user_id,
                    text=texts.Shop.Texts.success_buy.format(
                        title=purchase.title
                    )
                )
                msg_ids.append(success_msg.message_id)
                
                await PurchasesMethods().product_message_id(
                    answer_message_id=answer_message_id, msg_ids=msg_ids
                    )
                
                """Ставим реакцию на заявку"""
                await message.bot.set_message_reaction(
                    chat_id=shop_chat,
                    message_id=answer_message_id,
                    reaction=[
                        types.ReactionTypeEmoji(emoji="❤️")
                    ]
                )
                
                try:
                    """Изменяем клаву на заявке"""
                    await message.bot.edit_message_reply_markup(
                        chat_id=shop_chat,
                        message_id=answer_message_id,
                        reply_markup=await inline.rollback_buy(purchase.id)
                    )
                except exceptions.TelegramBadRequest:
                    pass
                
            else:
                await message.bot.send_message(
                    chat_id=shop_chat,
                    text=texts.Error.Notif.undefined_error
                )
        except ListLengthChangedError:
            pass

    async def rollback_buy(
        self, call: types.CallbackQuery, user: Users, purchases_id: str
    ) -> None:
        """
        Подтверждаем покупку.
        """
        purchases, product = await PurchasesMethods().rollback_buy(purchases_id)
        logger.debug(purchases)
        logger.debug(product)
        if purchases:
            try:
                if purchases.product_ids:
                    await call.message.bot.delete_messages(
                        chat_id=purchases.user.user_id,
                        message_ids=purchases.product_ids
                    )
                else:
                    logger.warning(
                        "Ошибка при удалении сообщения «{0}»".format(purchases.product_ids)
                    )
            except: # exceptions.TelegramBadRequest
                logger.warning(
                    "Ошибка при удалении сообщения «{0}»".format(purchases.product_ids)
                )
            
            log_msg = await call.bot.send_message(
                chat_id=shop_chat,
                text=texts.Shop.Texts.log_buy.format(
                    tg_info=await Func.format_tg_info(user.user_id, user.tg_username),
                    title_product=product.title,
                    description=product.description,
                    starcoins=product.price,
                    quantity=product.quantity,
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
                    instructions=product.delivery_instructions if product.delivery_instructions else "",
                    delivery_data=purchases.delivery_data if purchases.delivery_data else "",
                ),
                reply_markup=await inline.success_buy(purchases_id=purchases.id)
            )

            await PurchasesMethods().add_message_id(purchases_id=purchases.id, message_id=log_msg.message_id)

            await call.answer(
                texts.Shop.Admin.rollback_buy
            )
            await call.message.react(
                reaction=[
                    types.ReactionTypeEmoji(emoji="🍌")
                ]
            )
            await call.message.delete_reply_markup()
        else:
            await call.answer(
                texts.Error.Notif.undefined_error,
                show_alert=True
            )

