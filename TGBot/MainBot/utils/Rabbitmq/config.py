import os

import pika


class TOPICS:
    USER_ACTIONS: str = "user-actions"
    GAME_ACTIONS: str = "game-actions"
    SHOP_ACTIONS: str = "shop-actions"
    QUEST_ACTIONS: str = "quest-actions"


class RabbitMQConfig:
    connection_params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.getenv("RABBITMQ_PORT", 5672)),
        credentials=pika.PlainCredentials(
            os.getenv("RABBITMQ_USER", "guest"), os.getenv("RABBITMQ_PASSWORD", "guest")
        ),
    )

    TOPICS = TOPICS
