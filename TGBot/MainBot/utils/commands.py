from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats


async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Меню"),
        BotCommand(command="profile", description="Профиль"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="game", description="Играть"),
        BotCommand(command="quests", description="Квесты"),
        BotCommand(command="shop", description="Магазин"),
    ]

    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())


async def delete_commands(bot):
    await bot.delete_my_commands(BotCommandScopeAllPrivateChats())
