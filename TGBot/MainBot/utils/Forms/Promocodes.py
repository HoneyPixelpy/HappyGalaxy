import texts
from aiogram import types
from aiogram.fsm.context import FSMContext
from MainBot.base.models import Users
from MainBot.base.orm_requests import PromocodesMethods, IdempotencyKeyMethods
from MainBot.keyboards import reply, selector
from MainBot.state.state import SPromocodes
from MainBot.utils.MyModule import Func


class Promocodes:

    async def wait_promo(
        self,
        user: Users,
        state: FSMContext,
        *,
        call: types.CallbackQuery = None,
        message: types.Message = None,
    ) -> None:
        if call:
            message = call.message
            await message.delete()

        await message.bot.send_message(
            chat_id=user.user_id,
            text=texts.Promocodes.Text.wait,
            reply_markup=await reply.back("Введите промокод"),
        )

        await state.set_state(SPromocodes.wait)

    async def activate(
        self, message: types.Message, state: FSMContext, user: Users
    ) -> None:
        promocode = await PromocodesMethods().activate(
            user.id,
            message.text,
            idempotency_key=await IdempotencyKeyMethods.IKgenerate(
                user.user_id,
                message
            )
        )
        if isinstance(promocode, str):
            if promocode == "server_error":
                await Func.send_error_to_developer(
                    text=(
                        "Пользователь не смог активировать промокод\n"
                        f"{user.user_id} {user.tg_username}\n"
                        f"Promocode: {message.text}"
                    )
                )
            await message.bot.send_message(
                chat_id=user.user_id,
                text=texts.Promocodes.Errors.__dict__[promocode],
                reply_markup=await reply.back("Введите промокод"),
            )
        else:
            text = texts.Promocodes.Text.promo_starcoins.format(
                name=(
                    f"{promocode.title}\n\n{promocode.description}"
                    if promocode.description
                    else promocode.title
                ),
                reward_starcoins=promocode.reward_starcoins,
            )
            await message.bot.send_message(
                chat_id=user.user_id,
                text=text,
                reply_markup=await selector.main_menu(user),
                disable_web_page_preview=True,
            )
            await message.delete()
            await state.clear()
