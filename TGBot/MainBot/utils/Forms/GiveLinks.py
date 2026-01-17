import texts
from aiogram import types
from MainBot.base.models import StarcoinsPromo, Users
from MainBot.base.orm_requests import PromocodesMethods, IdempotencyKeyMethods
from MainBot.keyboards import selector


class GiveLinksForm:

    async def activate(
        self, message: types.Message, user: Users, url_data: str
    ) -> None:
        promocode = await PromocodesMethods().activate(
            user.id,
            url_data,
            idempotency_key=await IdempotencyKeyMethods.IKgenerate(
                user.user_id,
                message
            )
        )
        if isinstance(promocode, (StarcoinsPromo,)):
            text = texts.Promocodes.Text.url_starcoins.format(
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
            return True
