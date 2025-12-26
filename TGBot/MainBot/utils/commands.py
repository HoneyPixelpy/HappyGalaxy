from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats


async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Профиль"),
        BotCommand(command="game", description="Играть"),
        BotCommand(command="task", description="Квесты"),
        BotCommand(command="shop", description="Магазин"),
        BotCommand(command="help", description="Помощь"),
    ]

    await bot.set_my_commands(commands, BotCommandScopeAllPrivateChats())


async def delete_commands(bot):
    await bot.delete_my_commands(BotCommandScopeAllPrivateChats())
