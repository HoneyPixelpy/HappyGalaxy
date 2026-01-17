from aiogram import types

from MainBot.base.models import Users
from MainBot.base.orm_requests import ManagementLinksMethods, IdempotencyKeyMethods


class UTMLinksForm:

    async def activate(self, user: Users, message: types.Message, url_data: str) -> None:
        return await ManagementLinksMethods().activate(
            user.id,
            url_data,
            idempotency_key=await IdempotencyKeyMethods.IKgenerate(
                user.user_id,
                message
            )
        )
