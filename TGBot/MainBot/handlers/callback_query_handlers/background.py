from aiogram import F, Router, types
from MainBot.base.models import Users
from MainBot.filters.chat_types import ChatTypeFilter

background_router = Router(name=__name__)
background_router.message.filter(ChatTypeFilter(["private"]))


@background_router.callback_query(F.data == "null")
async def null(call: types.CallbackQuery, user: Users):
    pass


@background_router.callback_query(
    F.data.in_(
        [
            F.data == "exit",
            F.data.startswith("data_validation|"),
            F.data.startswith("edit_age|"),
            F.data.startswith("success_fio|"),
            F.data.startswith("gender|"),
            F.data.startswith("sure_role|"),
        ]
    )
)
async def delete_no_state(call: types.CallbackQuery):
    await call.message.delete()


