from datetime import timedelta

from django.utils import timezone
from loguru import logger

from .aggregate import AdvancedStatsAggregator


class AggregateArchive:

    def pipeline(self) -> None:
        """Ежедневный пайплайн агрегации"""
        try:
            aggregation_date = timezone.now().date() - timedelta(days=7)

            return AdvancedStatsAggregator().aggregate_stats(aggregation_date)

        except Exception as e:
            logger.error(f"❌ Aggregation failed: {e}")
