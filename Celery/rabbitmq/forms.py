from .producer import RabbitMQBackupProducer


class CopyBaseMethods:
    
    def __init__(self):
        self.rabbitmq = RabbitMQBackupProducer()

    def send_backup(
        self,
        chat_id: int,
        formatted_time: str,
        content: str|bytes,
        caption: str
        ) -> str:
        return self.rabbitmq.send_backup_message(
            {
                "chat_id": chat_id,
                "formatted_time": formatted_time,
                "content": content,
                "caption": caption
            }
        )


class RabbitMQForms(CopyBaseMethods):
    
    def __init__(self):
        super().__init__()
