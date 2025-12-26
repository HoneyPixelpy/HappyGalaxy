from bot.consumers.analytics import RabbitMQAnalyticsConsumer
from django.core.management.base import BaseCommand
from loguru import logger


class Command(BaseCommand):
    help = "Starts RabbitMQ consumer for user analytics"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Starting RabbitMQ analytics consumer...")
        )

        consumer = RabbitMQAnalyticsConsumer()

        try:
            self.stdout.write(self.style.SUCCESS("📊 Starting message consumption..."))
            consumer.start_consuming()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("🛑 Stopping RabbitMQ consumer..."))
            consumer.stop_consuming()
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.stdout.write(self.style.ERROR(f"❌ Consumer error: {e}"))
