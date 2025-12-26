from MainBot.base.models import Users
from MainBot.base.orm_requests import ManagementLinksMethods


class UTMLinksForm:

    async def activate(self, user: Users, url_data: str) -> None:
        return await ManagementLinksMethods().activate(user.id, url_data)
