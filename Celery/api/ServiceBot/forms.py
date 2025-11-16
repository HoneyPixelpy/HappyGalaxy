from .requests import SendBaseRequests


class CopyBaseMethods:
    
    def __init__(self):
        self.fastapi = SendBaseRequests()

    def send_backup(
        self,
        chat_id: int,
        formatted_time: str,
        content: str|bytes
        ) -> str:
        return self.fastapi.send_backup(
            user_data = {
                "chat_id": chat_id,
                "formatted_time": formatted_time,
                "content": content
            }
        )


class FastAPIForms(CopyBaseMethods):
    
    def __init__(self):
        super().__init__()
