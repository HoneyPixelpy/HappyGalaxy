async def start_bot():
	from GPTBot.config import bot, dp

	from GPTBot.middlewares.user import UserDataSession
	from GPTBot.handlers import router
	dp.include_routers(router)
 
	dp.update.outer_middleware(UserDataSession())
		
	await bot.delete_webhook(drop_pending_updates=True)
  
	await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
