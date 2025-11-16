
from aiogram import types, exceptions
from aiogram.utils.keyboard import InlineKeyboardBuilder

from MainBot.base.models import Lumberjack_Game, Users
import texts
from MainBot.base.forms import Lumberjack_GameForms
from MainBot.base.orm_requests import Lumberjack_GameMethods
from MainBot.keyboards.inline import IKB as inline
from MainBot.utils.MyModule import Func

class LumberjackGame:

    row = 4
    col = 5

    @classmethod
    async def msg_before_game(
        cls,
        message: types.Message
        ) -> None:
        """
        Отправляет сообщение перед игрой
        """
        await message.bot.send_message(
            chat_id=message.chat.id,
            text=texts.Game.Texts.before_game,
            reply_markup=await inline.before_game()
            )

    @classmethod
    async def create_game_text(
        cls,
        user: Users,
        game: Lumberjack_Game,
        success_or_income: float = 0
        ) -> None:
        """
        Создаем текст для сообщения с игрой
        """
        return texts.Game.Texts.info.format(
            starcoins=round(user.starcoins + success_or_income, 2),
            left_energe=game.current_energy
            )

    @classmethod
    async def create_game_keyboard(
        cls,
        user: Users
        ) -> tuple[InlineKeyboardBuilder, Lumberjack_Game]:
        """
        Создает игровое поле 4x5 с кнопками
        """
        game_user: Lumberjack_Game = await Lumberjack_GameMethods().get_by_user(
            user=user
            )
        
        # Если нужно новое поле или оно пустое
        if not game_user.current_grid:
            game_user: Lumberjack_Game = await Lumberjack_GameForms().generate_new_grid(
                game_user,
                cls.row,
                cls.col
                )
        
        builder = InlineKeyboardBuilder()
        
        # Создаем кнопки поля
        for row in range(cls.row):
            for col in range(cls.col):
                if game_user.current_grid[row][col] == 1:
                    emoji = "⭐️" 
                elif isinstance(game_user.current_grid[row][col], str):
                    emoji = f"+{game_user.current_grid[row][col]}" 
                else:
                    emoji = "🌑"
                builder.button(
                    text=emoji, 
                    callback_data=f"lumberjack_click|{row}|{col}"
                )
        
        # Добавляем кнопки управления
        builder.button(
            text=texts.Game.Btns.refresh, 
            callback_data="lumberjack_refresh"
            )
        builder.button(
            text=texts.Game.Btns.boosts, 
            callback_data="boosts"
            )
        builder.button(
            text=texts.Btns.back, 
            callback_data="games"
            )
        
        builder.adjust(5, 5, 5, 5, 1, 1)  # 4 ряда по 5 кнопок + 2 кнопки управления
        
        return builder.as_markup(), game_user

    @classmethod
    async def send_call_game(
        cls,
        call: types.CallbackQuery, 
        user: Users,
        success_or_income: float = 0
        ) -> None:
        """
        Обрабатывает клик по ячейке
        """
        keyboard, game_user = await cls.create_game_keyboard(user)
        energy_text = await cls.create_game_text(user, game_user, success_or_income)

        try:
            await call.message.edit_text(
                text=energy_text,
                reply_markup=keyboard
                )
        except exceptions.TelegramBadRequest:
            await call.message.bot.send_message(
                chat_id=call.message.chat.id,
                text=energy_text,
                reply_markup=keyboard
                )
            try:
                await call.message.delete()
            except:
                pass

    # @classmethod
    # async def send_msg_game(
    #     cls,
    #     message: types.Message, 
    #     user: Users
    #     ) -> None:
    #     """
    #     Отправляет новое игровое поле
    #     """
    #     keyboard, game = await cls.create_game_keyboard(user)
    #     energy_text = await cls.create_game_text(user, game)
        
    #     await message.bot.send_message(
    #         chat_id=message.chat.id,
    #         text=energy_text,
    #         reply_markup=keyboard
    #     )
        
    @classmethod
    async def handle_click(
        cls,
        call: types.CallbackQuery, 
        user: Users
        ) -> None:
        """
        Обрабатывает клик по ячейке
        """
        _, row, col = call.data.split("|")
        row, col = int(row), int(col)
        
        data: dict = await Lumberjack_GameMethods().refresh_energy(
            user=user
            )
        game_user = data['game_user']

        if data['force_update_energy']:
            from MainBot.utils.Games import LumberjackManager
            await LumberjackManager().force_update_energy(user, game_user)
            await Func.send_error_to_developer(
                "Энергия пользователя {user_id} {tg_username} не восстановилось после истечения времени".format(
                    user_id=user.user_id,
                    tg_username=f"@{str(user.tg_username)}" if user.tg_username else "-"
                ))
        
        # Проверяем энергию
        if game_user.current_energy <= 0:
            await call.answer(texts.Game.Error.no_energy.format(
                left_time=data['time_str']
            ),
            show_alert=True
            )
            return
        
        # Обрабатываем клик
        success_or_income = await Lumberjack_GameForms().click_cell(user, game_user, row, col)
        if success_or_income:
            try:
                await call.answer(f"+{success_or_income}")
            except:
                pass
            
            await cls.send_call_game(call, user, success_or_income)
        else:
            await call.answer(texts.Game.Error.miss)
        
        if data['first_click']:
            from MainBot.utils.Games import LumberjackManager
            await LumberjackManager().schedule_energy_update(user)

    @classmethod
    async def handle_refresh(
        cls,
        call: types.CallbackQuery, 
        user: Users
        ) -> None:
        """
        Обновляет игровое поле
        """
        data: dict = await Lumberjack_GameMethods().refresh_energy(
            user=user
            )
        game_user = data['game_user']
        
        if data['force_update_energy']:
            from MainBot.utils.Games import LumberjackManager
            await LumberjackManager().force_update_energy(user, game_user)
            await Func.send_error_to_developer(
                "Энергия пользователя {user_id} {tg_username} не восстановилось после истечения времени".format(
                    user_id=user.user_id,
                    tg_username=f"@{str(user.tg_username)}" if user.tg_username else "-"
                ))

        if game_user.current_energy <= 0:
            await call.answer(texts.Game.Error.no_energy.format(
                    left_time=data['time_str']
                ),
                show_alert=True
            )
            return
        await Lumberjack_GameForms().generate_new_grid(
            game_user,
            cls.row,
            cls.col
            )
        
        await cls.send_call_game(call, user)

