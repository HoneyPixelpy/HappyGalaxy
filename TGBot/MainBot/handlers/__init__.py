__all__ = ("router",)

from aiogram import Router

from .admin_handlers import admin_router
from .callback_query_handlers import callback_router
from .command_handlers import command_router
from .message_handlers import texts_router
from .state_handlers import state_router

router = Router(name=__name__)

router.include_routers(
    command_router,
    state_router,
    admin_router,
    callback_router,
)

# this one has to be the last!
router.include_router(texts_router)
