from typing import Optional

import texts
from aiogram import types
from MainBot.base.models import Users
from MainBot.base.orm_requests import Lumberjack_GameMethods


class KB:
    @classmethod
    async def back(cls, placeholder: Optional[str] = None) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=texts.Btns.back)]],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=placeholder,
        )

    @classmethod
    async def nickname(cls, role: str) -> types.ReplyKeyboardMarkup:
        keyboard = []
        if role != "child":
            keyboard.append([types.KeyboardButton(text=texts.Btns.select_later)])
        keyboard.append([types.KeyboardButton(text=texts.Btns.back)])
        return types.ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Введите псевдоним",
        )

    # @classmethod
    # async def start_hello(cls) -> types.ReplyKeyboardMarkup:
    #     return types.ReplyKeyboardMarkup(
    #             keyboard=[
    #                 [
    #                     types.KeyboardButton(text=texts.Start.Btns.go),
    #                     types.KeyboardButton(text=texts.Start.Btns.wait)
    #                 ]
    #             ],
    #             resize_keyboard=True,
    #             one_time_keyboard=True,
    #         )
    @classmethod
    async def start_wait(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=texts.Start.Btns.ready)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    @classmethod
    async def why_are_you(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=texts.Start.Btns.participant),
                    types.KeyboardButton(text=texts.Start.Btns.parent),
                ],
                [types.KeyboardButton(text=texts.Start.Btns.worker)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    @classmethod
    async def send_phone(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📱 Отправить номер", request_contact=True)],
                [types.KeyboardButton(text=texts.Btns.back)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    @classmethod
    async def main_menu(cls, user: Users) -> types.ReplyKeyboardMarkup:
        from MainBot.utils.Forms import FamilyTies
        keyboard = []

        if (
            FamilyTies(user.role_private).need or 
            await Lumberjack_GameMethods().get_max_energy(user)
            ):
            # Это в основном для того чтобы работник не попал в игру (можно изменить логику)
            keyboard.append([types.KeyboardButton(text=texts.Btns.game)])

        keyboard.append([types.KeyboardButton(text=texts.Btns.quests)])

        keyboard.append(
            [
                types.KeyboardButton(text=texts.Btns.shop),
                types.KeyboardButton(text=texts.Btns.profile),
            ]
        )

        # keyboard.append([
        #     types.KeyboardButton(text=texts.Btns.promocodes)
        # ])
        keyboard.append([types.KeyboardButton(text=texts.Btns.help)])
        return types.ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Главное меню",
        )

    @classmethod
    async def amdin_markup(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=texts.Admin.Btns.find_user),
                    types.KeyboardButton(text=texts.Admin.Btns.mailing),
                ],
                [
                    types.KeyboardButton(text=texts.Admin.Btns.all_tasks),
                    types.KeyboardButton(text=texts.Admin.Btns.generate_key),
                ],
                [types.KeyboardButton(text=texts.Admin.Btns.bonus_boost)],
                [types.KeyboardButton(text=texts.Admin.Btns.back_to_main)],
            ],
            resize_keyboard=True,
            input_field_placeholder="Админка",
        )

    @classmethod
    async def Pin_Mailing_markup(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=texts.Admin.Btns.yes_pin),
                    types.KeyboardButton(text=texts.Admin.Btns.no_pin),
                ],
                [types.KeyboardButton(text=texts.Admin.Btns.back_to_admin)],
            ],
            resize_keyboard=True,
        )

    @classmethod
    async def back_to_amdin_markup(
        cls,
        *,
        del_channel_btn: bool = False,
        del_personal_btn: bool = False,
        no_media_btn: bool = False
    ) -> types.ReplyKeyboardMarkup:
        keyboard_list = []

        row_buttons = []
        if del_channel_btn:
            row_buttons.append(
                types.KeyboardButton(text=texts.Admin.Btns.delete_channel)
            )
        if del_personal_btn:
            row_buttons.append(
                types.KeyboardButton(text=texts.Admin.Btns.delete_personal)
            )
        if no_media_btn:
            row_buttons.append(types.KeyboardButton(text=texts.Admin.Mailing.no_media))

        if row_buttons:
            keyboard_list.append(row_buttons)

        if no_media_btn:
            keyboard_list.append([types.KeyboardButton(text=texts.Btns.back)])
        else:
            keyboard_list.append(
                [types.KeyboardButton(text=texts.Admin.Btns.back_to_admin)]
            )

        return types.ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)

    @classmethod
    async def Confirm_Mailing_markup(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=texts.Admin.Mailing.start_mailing)],
                [types.KeyboardButton(text=texts.Btns.back)],
            ],
            resize_keyboard=True,
        )

    @classmethod
    async def type_bonus(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=texts.Admin.Bonus.scale_clicks_bonus),
                    types.KeyboardButton(text=texts.Admin.Bonus.add_starcoins_bonus),
                ],
                [
                    types.KeyboardButton(text=texts.Admin.Bonus.energy_renewal_bonus),
                ],
                [types.KeyboardButton(text=texts.Admin.Btns.back_to_admin)],
            ],
            resize_keyboard=True,
        )

    @classmethod
    async def interactive_game_reward_type(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=texts.InteractiveGame.Btns.from_all_wins)],
                [types.KeyboardButton(text=texts.InteractiveGame.Btns.to_each_winner)],
                [types.KeyboardButton(text=texts.Btns.back)],
            ],
            resize_keyboard=True,
        )

    @classmethod
    async def interactive_game_roles(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text=texts.InteractiveGame.Btns.child),
                    types.KeyboardButton(text=texts.InteractiveGame.Btns.parent),
                ],
                [
                    types.KeyboardButton(text=texts.InteractiveGame.Btns.child_parent),
                    types.KeyboardButton(text=texts.InteractiveGame.Btns.all_people),
                ],
                [types.KeyboardButton(text=texts.Btns.back)],
            ],
            resize_keyboard=True,
        )

    @classmethod
    async def interactive_game_type_game(cls) -> types.ReplyKeyboardMarkup:
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=texts.InteractiveGame.Btns.all)],
                [types.KeyboardButton(text=texts.InteractiveGame.Btns.duel)],
                [types.KeyboardButton(text=texts.Btns.back)],
            ],
            resize_keyboard=True,
        )
