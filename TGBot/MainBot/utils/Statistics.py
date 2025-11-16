from typing import Any
from asgiref.sync import sync_to_async

from django.db.models import Count, F, ExpressionWrapper, IntegerField, Avg, Case, When, Value, CharField, Max, DurationField, Sum
from django.db.models.functions import ExtractYear, Now, TruncDate
from loguru import logger

from MainBot.base.models import Family_Ties, Purchases, Sigma_Boosts, SubscribeQuest, Users


class DemographicStatistics:
    """
    Демографическая статистика
    """
    
    def __init__(self):
        pass

    async def _by_roles(self) -> list[dict]:
        """
        Делаем подсчет по ролям.
        """
        return await sync_to_async(list)(
            Users.objects.values('_role').annotate(count=Count('id'))
        )

    async def _gender_distribution(self) -> list[dict]:
        """
        Делаем подсчет по гендеру.
        """
        return await sync_to_async(list)(
            Users.objects.values('gender').annotate(count=Count('id'))
        )

    async def _age_group(self, role: str) -> list[dict]:
        """
        Делаем подсчет по возрасту.
        # {
        #     'child': [{'age': 7, 'count': 3}, {'age': 8, 'count': 5}, ...],
        #     'parent': [{'age': 35, 'count': 12}, {'age': 36, 'count': 8}, ...],
        #     ...
        # }
        """
        return await sync_to_async(list)(
            Users.objects.filter(_role=role).annotate(
                age=ExpressionWrapper(
                    ExtractYear(Now()) - ExtractYear('_age'),
                    output_field=IntegerField()
                )
            ).values('age').annotate(
                count=Count('id')
            ).order_by('age')
        )
    
    # async def _age_groups(self) -> dict[str:list[dict]]:
    #     """
    #     Делаем подсчет по возрасту для всех ролей
    #     """
    #     return {
    #         role: await self._age_group(role)
    #         for role in roles.keys()
    #     }
    
    async def get_demographics(self) -> None:
        """
        Стата по демографике.
        """
        roles = await self._by_roles()
        gender_distribution = await self._gender_distribution()
        # age_groups = await self._age_groups()

        logger.info(roles)
        logger.info(gender_distribution)
        # logger.info(age_groups)


class Lumberjack_GameStatistics:
    """
    Игровая аналитика (Дровосек)
    """
    
    def __init__(self):
        pass
    
    def _top_starcoins_players(self) -> Any:
        """
        Топ игроков по старкоинам
        """
        return list(Users.objects.order_by('-all_starcoins')[:10])

    def _average_earnings_game(self) -> Any:
        """
        Средний заработок в игре
        """
        return Users.objects.aggregate(avg_starcoins=Avg('all_starcoins'))

    async def _boost_activity(self) -> Any:
        """
        Активность по бустам
        """
        boost_stats = await sync_to_async(list)(
            Sigma_Boosts.objects.annotate(
                boost_type=Case(
                    When(income_level__gt=0, then=Value('income')),
                    When(energy_capacity_level__gt=0, then=Value('energy_capacity')),
                    When(recovery_level__gt=0, then=Value('recovery')),
                    When(passive_income_level__gt=0, then=Value('passive_income')),
                    default=Value('none'),
                    output_field=CharField()
                )
            ).values('boost_type').annotate(
                total_users=Count('user_id', distinct=True),
                avg_level=Avg(
                    Case(
                        When(boost_type='income', then='income_level'),
                        When(boost_type='energy_capacity', then='energy_capacity_level'),
                        When(boost_type='recovery', then='recovery_level'),
                        When(boost_type='passive_income', then='passive_income_level'),
                        default=0,
                        output_field=IntegerField()
                    )
                ),
                max_level=Max(
                    Case(
                        When(boost_type='income', then='income_level'),
                        When(boost_type='energy_capacity', then='energy_capacity_level'),
                        When(boost_type='recovery', then='recovery_level'),
                        When(boost_type='passive_income', then='passive_income_level'),
                        default=0,
                        output_field=IntegerField()
                    )
                )
            ).exclude(boost_type='none')
        )
        
        # Дополнительная аналитика по пассивному доходу
        passive_income_stats = await sync_to_async(
            lambda: Sigma_Boosts.objects.filter(
                passive_income_level__gt=0
            ).aggregate(
                avg_claim_interval=Avg(
                    ExpressionWrapper(
                        Now() - F('_last_passive_claim'),
                        output_field=DurationField()
                    )
                )
            )
        )()
        
        return {
            'boost_types': boost_stats,
            'passive_income': {
                'total_users': await sync_to_async(
                    Sigma_Boosts.objects.filter(passive_income_level__gt=0).count
                )(),
                **passive_income_stats
            }
        }
    
    async def get_lumberjack_game(self) -> Any:
        """
        Итоги дровосека
        """
        logger.info(await sync_to_async(self._top_starcoins_players)())
        logger.info(await sync_to_async(self._average_earnings_game)())
        logger.info(await self._boost_activity())


class SocialTiesStatistics:
    """
    Социальные связи
    """

    def __init__(self):
        pass

    async def _number_families_created(self) -> Any:
        """
        Количество созданных семей
        """
        return await sync_to_async(list)(
            Family_Ties.objects.values('family_id').annotate(
                members=Count('user_id')
            ).filter(members__gt=1)
        )

    async def _average_children_per_parent(self) -> Any:
        """
        Среднее количество детей на одного родителя
        """
        return await sync_to_async(list)(
            Users.objects.filter(
                _role='parent'
            ).annotate(
                child_count=Count('family_children')
            ).aggregate(avg=Avg('child_count'))
        )

    async def get_social_ties(self) -> Any:
        """
        Стата по родственным связям.
        """
        created = await self._number_families_created()
        children_per_parent = await self._average_children_per_parent()

        logger.info(created)
        logger.info(children_per_parent)


class FinancialAnalyticsStatistics:
    """
    Финансовая аналитика
    """

    def __init__(self):
        pass

    async def _total_starcoins_in_system(self) -> Any:
        """
        Общее количество старкоинов в системе
        """
        return await sync_to_async(
            Users.objects.aggregate(total=Sum('_starcoins'))
        )

    async def _total_starcoins_in_all_time(self) -> Any:
        """
        Общее количество старкоинов заработанных за все время
        """
        return await sync_to_async(
            Users.objects.aggregate(total=Sum('all_starcoins'))
        )

    async def _top_buys(self) -> Any:
        """
        Топ покупок
        """
        return await sync_to_async(list)(
            Purchases.objects.values('item').annotate(
                total_sold=Count('id'),
                total_revenue=Sum('price')
            )
        )

    # async def _effectiveness_promo_codes(self) -> Any:
    #     """
    #     Эффективность промокодов
    #     """
    #     return await sync_to_async(list)(
    #         Promocodes.objects.annotate(
    #             usage_count=Count('used_by'),
    #             total_reward=Sum('reward')
    #         )
    #     )

    async def get_financial_analytics(self) -> Any:
        """
        Стата по финансам.
        """
        total_starcoins_in_system = await self._total_starcoins_in_system()
        total_starcoins_in_all_time = await self._total_starcoins_in_all_time()
        top_buys = await self._top_buys()
        # effectiveness_promo_codes = await self._effectiveness_promo_codes()

        logger.info(total_starcoins_in_system)
        logger.info(total_starcoins_in_all_time)
        logger.info(top_buys)
        # logger.info(effectiveness_promo_codes)


class UserActivityStatistics:
    """
    Активность пользователей
    """

    def __init__(self):
        pass

    async def _registr_schedule_by_day_week(self) -> Any:
        """
        График регистраций (по дням/неделям)
        """
        return await sync_to_async(list)(
            Users.objects.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        )

    async def _percentage_active_users(self) -> float:
        """
        Процент активных пользователей
        """
        active_users = await Users.objects.filter(active=True).acount()
        total_users = await Users.objects.acount()
        return (active_users / total_users) * 100

    async def get_user_activity(self) -> Any:
        """
        Стата по активности пользователей.
        """
        registr_schedule_by_day_week = await self._registr_schedule_by_day_week()
        percentage_active_users = await self._percentage_active_users()

        logger.info(registr_schedule_by_day_week)
        logger.info(percentage_active_users)


class TaskEfficiencyStatistics:
    """
    Эффективность заданий
    """

    def __init__(self):
        pass

    async def _сonversion_channel_subscriptions(self) -> float:
        """
        Конверсия подписок на канал
        """
        total_assigned = SubscribeQuest.objects.count()
        completed = SubscribeQuest.objects.filter(completed=True).count()
        return (completed / total_assigned) * 100

    async def get_task_efficiency(self) -> Any:
        """
        Стата по эффективности задач.
        """
        registr_schedule_by_day_week = await self._сonversion_channel_subscriptions()

        logger.info(registr_schedule_by_day_week)


class TechnicalMetricsStatistics:
    """
    Технические метрики
    """

    def __init__(self):
        pass

    async def _average_session_time(self) -> Any:
        """
        Среднее время сессии (разница между created_at и updated_at)
        """
        return await sync_to_async(list)(
            Users.objects.annotate(
                session_time=ExpressionWrapper(
                    F('updated_at') - F('created_at'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('session_time'))
        )

    async def get_technical_metrics(self) -> Any:
        """
        Стата по технологическим метрикам.
        """
        registr_schedule_by_day_week = await self._average_session_time()
        logger.info(registr_schedule_by_day_week)


class Graphs:
    pass


class Statistics(
    DemographicStatistics,
    Lumberjack_GameStatistics,
    SocialTiesStatistics,
    FinancialAnalyticsStatistics,
    UserActivityStatistics,
    TaskEfficiencyStatistics,
    TechnicalMetricsStatistics
    ):
    
    def __init__(self):
        super().__init__()

    async def get_all(self) -> Any:
        # await super().get_demographics()
        await super().get_lumberjack_game()
        await super().get_social_ties()
        await super().get_financial_analytics()
        await super().get_user_activity()
        await super().get_task_efficiency()
        await super().get_technical_metrics()



