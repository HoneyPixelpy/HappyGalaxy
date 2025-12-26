from aiogram import types


def main_menu() -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🖼️ Генерация Картинок", callback_data="gen_image"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="✍️ Генерация Текста", callback_data="gen_text"
                ),
                # ],
                # [
                #     types.InlineKeyboardButton(
                #         text="🔄 Перезагрузить Диалог",
                #         callback_data="reset_dialog"
                #         ),
            ],
        ]
    )
