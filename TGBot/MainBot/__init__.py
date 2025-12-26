async def start_bot():
    from MainBot.config import bot, dp
    from MainBot.utils.commands import delete_commands, set_commands

    await delete_commands(bot)
    await set_commands(bot)

    from MainBot.handlers import router
    from MainBot.middlewares.user import UserDataSession

    dp.include_routers(router)

    dp.update.outer_middleware(UserDataSession())

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
