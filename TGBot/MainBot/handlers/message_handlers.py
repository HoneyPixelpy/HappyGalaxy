from aiogram import F, Router, types
from aiogram.filters import StateFilter
from loguru import logger
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter
from MainBot.utils.Forms import Menu

texts_router = Router(name=__name__)
texts_router.message.filter(ChatTypeFilter(["private"]))


@texts_router.message(StateFilter(None), F.text)
async def text_over(message: types.Message, user: Users):
    """Все обработки с текстом"""
    logger.debug(message.text)
    try:
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=message.html_text,
            reply_markup=types.ReplyKeyboardRemove()
        )
    except: # exceptions.TelegramBadRequest
        pass
    
    await Menu().main_menu(
        message,
        user
    )
    
    # match message.text:
    #     case texts.Btns.back:
    #         """Вернуться назад"""
    #         await Menu().main_menu(
    #             message,
    #             user
    #         )
    #     case texts.Btns.help:
    #         """Раздел поддержки"""
    #         await Profile().user_help_msg(user, message)
    #     case texts.Btns.game:
    #         """Раздел игр"""
    #         if familyTies := FamilyTies(user.role_private).need:
    #             if not await familyTies.check_parent(user):
    #                 await familyTies.info_parent(user, message)
    #                 return

    #         if await Lumberjack_GameMethods().get_max_energy(user):
    #             await LumberjackGame.msg_before_game(user, message)
    #         else:
    #             await message.bot.send_message(
    #                 chat_id=user.user_id,
    #                 text=texts.Error.Notif.no_access_game
    #             )
    #     case texts.Btns.profile:
    #         """Раздел профиля"""
    #         user = await Sigma_BoostsForms().add_passive_income(user)
    #         await Profile().user_info_msg(message, user)
    #     case texts.Btns.shop:
    #         """Раздел магазина"""
    #         await Shop().catalog(user, message=message)
    #     case texts.Btns.quests:
    #         """Раздел квестов"""
    #         if familyTies := FamilyTies(user.role_private).need:
    #             if not await familyTies.check_parent(user):
    #                 await familyTies.info_parent(user, message)
    #                 return
            
    #         await Quests().viue_all(user, message=message)
        # case texts.Btns.promocodes:
        #     """Раздел промокодов"""
        #     await Promocodes().wait_promo(user, state, message=message)
    # await message.delete()
