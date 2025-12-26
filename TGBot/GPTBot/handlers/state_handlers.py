import os

import httpx
import texts
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from GPTBot.keyboards.inline import main_menu
from GPTBot.state.state import DialogStates
from GPTBot.utils import check_and_inc, is_timeout, set_timeout
from httpx_socks import AsyncProxyTransport  # Только для SOCKS5
from loguru import logger
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.MyModule import Func
from openai import AsyncOpenAI

from ..config import proxy_url

transport = AsyncProxyTransport.from_url(proxy_url)

openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(60.0)),
)

state_router = Router(name=__name__)
state_router.message.filter(ChatTypeFilter(["private"]))


@state_router.message(DialogStates.waiting_text_prompt)
async def handle_text_prompt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if is_timeout(user_id):
        await message.reply(
            "<b>⏳ Пожалуйста, подождите 20 секунд перед следующим запросом.</b>"
        )
        return

    if not check_and_inc(user_id, "text"):
        await message.reply("<b>🥲 Лимит генераций текста на сегодня исчерпан!</b>")
        return

    set_timeout(user_id)
    await message.reply("<b>⏳ Ваш текст генерируется...</b>")

    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": "Отвечай коротко, понятно и позитивно. Старайся тратить как можно меньше API токенов при ответе на запросы. Ты — универсальный помощник для пользователей из города Волжского (Россия, Волгоградская область), который разбирается во всём, всегда готов помочь со сложными задачами, предложить свои грандиозные идеи, дать хороший совет в повседневных вопросах и так далее. Помогай пользователям эффективно и самое главное правильно!",
                },
                {"role": "user", "content": message.text},
            ],
            # max_tokens=500
        )
        result = resp.choices[0].message.content.strip()
        await message.reply(result)
        await message.bot.send_message(
            chat_id=message.from_user.id,
            text="<b>Сгенерировать ещё</b>",
            reply_markup=main_menu(),
        )
        await state.clear()
    except Exception as e:
        await message.reply(texts.Error.Notif.server_error)
        await Func.send_error_to_developer(
            f"{user_id}\n<b>Ошибка генерации: {e.__class__.__name__} -> {e}</b>"
        )


@state_router.message(DialogStates.waiting_image_prompt)
async def handle_image_prompt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if is_timeout(user_id):
        await message.reply(
            "<b>⏳ Пожалуйста, подождите 20 секунд перед следующим запросом.</b>"
        )
        return

    if not check_and_inc(user_id, "image"):
        await message.reply("<b>🥲 Лимит генераций картинок на сегодня исчерпан!</b>")
        return

    set_timeout(user_id)
    await message.reply("<b>⏳ Ваша картинка генерируется...</b>")

    try:
        resp = await openai_client.images.generate(
            model="dall-e-3", prompt=message.text, n=1, size="1024x1024"
        )
        img_url = resp.data[0].url
        await message.reply_photo(photo=img_url)
        await message.bot.send_message(
            chat_id=message.from_user.id,
            text="<b>Сгенерировать ещё</b>",
            reply_markup=main_menu(),
        )
        await state.clear()
    except Exception as e:
        await message.reply(texts.Error.Notif.server_error)
        await Func.send_error_to_developer(
            f"{user_id}\n<b>Ошибка генерации: {e.__class__.__name__} -> {e}</b>"
        )
