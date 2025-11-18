__all__ = [
    "UserViewSet",
    "FamilyTiesViewSet",
    "PurchasesViewSet",
    "PikmiShopViewSet",
    "SigmaBoostsViewSet",
    "LumberjackGameViewSet",
    "GeoHunterGameViewSet",
    "WorkKeysViewSet",
    "BonusesViewSet",
    "UseBonusesViewSet",
    "QuestsViewSet",
    "UseQuestsViewSet",
    "RewardViewSet",
    "BoostsViewSet",
    "CopyBaseViewSet",
    "RangsViewSet",
    "PromocodesViewSet",
    "ManagementLinksViewSet",
    "InteractiveGameViewSet",
    "QuestModerationAttemptViewSet",
]

from datetime import datetime
from loguru import logger
import pytz

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet

from bot.service.rang import RangService

from ..serializers import BonusesSerializer, GeoHunterSerializer, LumberjackGameSerializer, \
    PikmiShopSerializer, PurchasesSerializer, QuestsSerializer, SigmaBoostsSerializer, \
                UseBonusesSerializer, UserSerializer, WorkKeysSerializer
from ..schemas import reward_data, boosts_data

from .game import BoostsMethods, GeoHunterMethods, LumberjackGameMethods, SigmaBoostsViewMethods, InteractiveGameMethods
from .personal import FamilyTiesMethods, RangsMethods, ReferralConnectionsMethods, UserMethods, WorkKeysMethods
from .utils import QueryData, check_sql_injection, queue_request
from .shop import Pikmi_ShopMethods, PurchasesMethods
from .bonus import BonusesMethods, UseBonusesMethods
from .quest import Quest_MA_Methods, QuestMethods, UseQuestMethods
from .backup import CopyBaseMethods
from .codes import CodesMethods
from .abstract import *


""" NOTE
НА СТАДИИ РЕФАКТОРИНГА
"""

""" NOTE
"no key" в качестве значения ключу нельзя 
передавать в Django
"""

""" NOTE 
методы не возвращают Response, а вызывает ошибку в которой передаем 
данные для составления в дальнейшем Response (всегда это делается в @queue_request)
"""

class SigmaBoostsViewSet(ViewSet, AbstractSigmaBoosts):

    # GET /api/v1/sigma-boosts/get_by_user/?user_id=123
    @action(detail=False, methods=['get'])
    @queue_request
    def get_by_user(self, request):
        user_id = QueryData.check_params(request, 'user_id')

        user = UserMethods.get(user_id=user_id)
        boost = SigmaBoostsViewMethods.get(user=user)
        
        SigmaBoostsViewMethods.get_by_user(boost)

    # PATCH /api/v1/sigma-boosts/{user_id}/add_passive_income/
    @action(detail=True, methods=['patch']) # , url_path='add-passive-income'
    @queue_request
    def add_passive_income(self, request, pk=None):
        # user_id = QueryData.check_params(request, 'user_id')

        user = UserMethods.get(pk=pk)
        boosts_user = SigmaBoostsViewMethods.get(user=user)
        
        SigmaBoostsViewMethods.passive_income_calculation(user, boosts_user)
    
    # PATCH /api/v1/sigma-boosts/upgrade_boost/?user_id=123&name=asdfas
    @action(detail=False, methods=['patch']) # , url_path='upgrade-boost'
    @queue_request
    def upgrade_boost(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        name = QueryData.check_params(request, 'name')
        
        user = UserMethods.get(pk=user_id)
        user_boosts = SigmaBoostsViewMethods.get(user=user)
        jack_game = LumberjackGameMethods.get(user=user)
        geo_hunter = GeoHunterMethods.get(user=user)
                
        SigmaBoostsViewMethods.upgrade_boost(
            user,
            user_boosts,
            jack_game,
            geo_hunter,
            name
        )

    # GET /api/v1/sigma-boosts/calculate_recovery_time/?user_id=123123
    @action(detail=False, methods=['get'])
    @queue_request
    def calculate_recovery_time(self, request):
        user_id = QueryData.check_params(request, 'user_id')

        user = UserMethods.get(pk=user_id)
        user_boosts = SigmaBoostsViewMethods.get(user=user)
        
        SigmaBoostsViewMethods.calculate_recovery_time(user_boosts)


class LumberjackGameViewSet(ViewSet):

    # GET /api/v1/lumberjack-games/{id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """Получить игру пользователя"""
        user = UserMethods.get(user_id=pk)
        game = LumberjackGameMethods.get(user=user)
        
        serializer = LumberjackGameSerializer(game)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/lumberjack-games/active_games/
    @action(detail=False, methods=['get'])
    @queue_request
    def active_games(self, request):
        """Получить все активные игры (аналог get_active_games)"""
        games = LumberjackGameMethods.all().select_related('user')
        serializer = LumberjackGameSerializer(games, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/lumberjack-games/refresh_energy/?user_id=123123
    @action(detail=False, methods=['get'])
    @queue_request
    def refresh_energy(self, request):
        """Получить все активные игры (аналог get_active_games)"""
        user_id = QueryData.check_params(request, 'user_id')

        user = UserMethods.get(pk=user_id)
        game_user = LumberjackGameMethods.get(user=user)
        user_boosts = SigmaBoostsViewMethods.get(user=user)
        
        return LumberjackGameMethods.refresh_energy(game_user, user_boosts)

    # PATCH /api/v1/lumberjack-games/{game_user_id}/update_grid/
    @action(detail=True, methods=['patch']) # , url_path='update-grid'
    @queue_request
    def update_grid(self, request, pk=None):
        """
        Обновляет игровое поле пользователя
        """
        # game_user_id = QueryData.check_params(request, 'game_user_id')
        grid = QueryData.check_params(request, 'grid')
        
        game_user = LumberjackGameMethods.get(pk=pk)
        
        return LumberjackGameMethods.update_grid(game_user, grid)

    # PATCH /api/v1/lumberjack-games/process_click/
    @action(detail=False, methods=['patch']) # , url_path='process-click'
    @queue_request
    def process_click(self, request):
        """
        Обрабатывает клик в игре с учетом всех бустов и обновляет состояние
        """
        user_id = QueryData.check_params(request, 'user_id')
        energy_in_click = QueryData.check_params(request, 'energy_in_click')
        row = QueryData.check_params(request, 'row')
        col = QueryData.check_params(request, 'col')
        
        # Получаем все необходимые данные за один запрос
        user = UserMethods.get(user_id=user_id)
        game_user = LumberjackGameMethods.get(user=user)
        boosts_user = SigmaBoostsViewMethods.get(user=user)
        game_user_two = GeoHunterMethods.get(user=user)

        return LumberjackGameMethods.process_click(
            user,
            game_user,
            game_user_two,
            boosts_user,
            energy_in_click,
            row,
            col
        )

    # PATCH /api/v1/lumberjack-games/{game_user_id}/restore_energy/
    @action(detail=True, methods=['patch']) # , url_path='restore-energy'
    @queue_request
    def restore_energy(self, request, pk=None):
        """
        Полностью восстанавливает энергию игрока
        """
        # game_user_id = QueryData.check_params(request, 'game_user_id')

        game_user = LumberjackGameMethods.get(pk=pk)
        game_user_two = GeoHunterMethods.get(user=game_user.user)
        
        return LumberjackGameMethods.restore_energy(game_user, game_user_two)


class GeoHunterGameViewSet(ViewSet):

    # GET /api/v1/geo-hunter/{id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """Получить геохантер"""
        user = UserMethods.get(user_id=pk)
        game = GeoHunterMethods.get(user=user)
        
        serializer = GeoHunterSerializer(game)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/geo-hunter/active_games/
    @action(detail=False, methods=['get'])
    @queue_request
    def active_games(self, request):
        games = GeoHunterMethods.all().select_related('user')
        serializer = GeoHunterSerializer(games, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/geo-hunter/refresh_energy/?user_id=123123
    @action(detail=False, methods=['get'])
    @queue_request
    def refresh_energy(self, request):
        user_id = QueryData.check_params(request, 'user_id')

        user = UserMethods.get(pk=user_id)
        game_user = GeoHunterMethods.get(user=user)
        user_boosts = SigmaBoostsViewMethods.get(user=user)

        return GeoHunterMethods.refresh_energy(game_user, user_boosts)

    # PATCH /api/v1/geo-hunter/process_click/
    @action(detail=False, methods=['patch']) # , url_path='process-click'
    @queue_request
    def process_click(self, request):
        """
        Обрабатывает клик в игре с учетом всех бустов и обновляет состояние
        """
        user_id = QueryData.check_params(request, 'user_id')
        energy_in_click = QueryData.check_params(request, 'energy_in_click')
        user_choice = QueryData.check_params(request, "user_choice")
        logger.debug(user_id)
        logger.debug(energy_in_click)
        logger.debug(user_choice)

        # Получаем все необходимые данные за один запрос
        user = UserMethods.get(pk=user_id)
        game_user = GeoHunterMethods.get(user=user)
        boosts_user = SigmaBoostsViewMethods.get(user=user)
        game_user_two = LumberjackGameMethods.get(user=user)

        response = GeoHunterMethods.process_click(
            user,
            game_user,
            game_user_two,
            boosts_user,
            energy_in_click,
            user_choice
        )
        logger.debug(response)
        return Response(
            response,
            status=status.HTTP_200_OK
            )

    # PATCH /api/v1/geo-hunter/{game_user_id}/restore_energy/
    @action(detail=False, methods=['patch']) # , url_path='restore-energy'
    @queue_request
    def restore_energy(self, request, pk=None):
        """
        Полностью восстанавливает энергию игрока
        """
        # game_user_id = QueryData.check_params(request, 'game_user_id')

        game_user = GeoHunterMethods.get(pk=pk)
        game_user_two = LumberjackGameMethods.get(user=game_user.user)
            
        return GeoHunterMethods.restore_energy(game_user, game_user_two)


class RewardViewSet(ViewSet):

    # GET /api/v1/reward_data/
    @queue_request
    def list(self, request):
        """
        Получаем данные для вознаграждений
        """
        return Response(
            reward_data.model_dump(),
            status=status.HTTP_200_OK
            )


class BoostsViewSet(ViewSet):

    # GET /api/v1/boosts_data/catalog/?user_id=123123
    @action(detail=False, methods=['get'])
    @queue_request
    def catalog(self, request):
        """
        Получаем данные для вознаграждений
        """
        user_id = QueryData.check_params(request, 'user_id')
        
        user = UserMethods.get(pk=user_id)
        user_boosts = SigmaBoostsViewMethods.get(user=user)
        
        return BoostsMethods.catalog(user_boosts)

    # GET /api/v1/boosts_data/info/?user_id=123123&name=income_level
    @action(detail=False, methods=['get'])
    @queue_request
    def info(self, request):
        """
        Получаем данные для вознаграждений
        """
        user_id = QueryData.check_params(request, 'user_id')
        name = QueryData.check_params(request, 'name')
        
        user = UserMethods.get(pk=user_id)
        user_boosts = SigmaBoostsViewMethods.get(user=user)
        
        return BoostsMethods.info(user_boosts, name)


class UserViewSet(ViewSet):

    # GET /api/v1/users/{user_id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """
        Получить конкретного пользователя по user_id
        """
        user = UserMethods.get(user_id=pk)
        serializer = UserSerializer(user)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
            )

    # GET /api/v1/users/
    @queue_request
    def list(self, request):
        """
        Получаем все записи
        """
        queryset = UserMethods.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
            )

    # POST /api/v1/users/
    @queue_request
    def create(self, request):
        """ create
        Создаем нового пользователя и две другие записи
        """
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
                )
        
        return UserMethods.create(serializer.validated_data)

    # GET /api/v1/users/banned/
    @action(detail=False, methods=['get'])
    @queue_request
    def banned(self, request):
        """
        Получаем всех забаненных пользователей
        """
        return UserMethods.banned()

    # GET /api/v1/users/{user_id}/referrals/count/
    @action(detail=True, methods=['get'], url_path='referrals/count')
    @queue_request
    def referral_count(self, request, pk=None):
        """
        Получаем кол-во рефералов
        """
        return UserMethods.referral_count(pk)

    # GET /api/v1/users/check_phone/?phone=+71234567890
    @action(detail=False, methods=['get'])
    @queue_request
    def check_phone(self, request):
        """
        Проверяем номер телефона на совпадения
        """
        phone = QueryData.check_params(request, 'phone')

        user = UserMethods.filter(phone=phone)
        
        serializer = UserSerializer(user) if user else None
        return Response(
            serializer.data if user else None,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/users/check_nickname/?nickname=superuser
    @action(detail=False, methods=['get'])
    @queue_request
    def check_nickname(self, request):
        """
        Проверяем никнейм на совпадения
        """
        nickname = QueryData.check_params(request, 'nickname')
        
        user = UserMethods.filter(nickname=nickname)
        serializer = UserSerializer(user) if user else None
        return Response(
            serializer.data if user else None,
            status=status.HTTP_200_OK
            )

    # PUT /api/v1/users/{user_id}/complete_registration/
    @action(detail=True, methods=['put']) # , url_path='complete-registration'
    @queue_request
    def complete_registration(self, request, pk=None):
        """
        Завершает регистрацию пользователя и инициализирует игровые данные
        """
        # user_id = QueryData.check_params(request, 'user_id')
        state_data = QueryData.check_params(request, 'state_data')
        rollback = QueryData.check_params(request, "rollback")
        
        user = UserMethods.get(pk=pk)
                
        return UserMethods.complete_registration(
            user, 
            state_data, 
            rollback
            )

    # PATCH /api/v1/users/update_telegram_username/?user_id=1&username=superuser
    @action(detail=False, methods=['patch']) # , url_path='update-telegram-username'
    @queue_request
    def update_telegram_username(self, request):
        """
        Обновляет Telegram username пользователя
        """
        user_id = QueryData.check_params(request, 'user_id')
        username = QueryData.check_params(request, 'username')
        
        user = UserMethods.get(pk=user_id)
        
        return UserMethods.update_telegram_username(user, username)

    # PATCH /api/v1/users/update_balance/?user_id=1&new_balance=1000
    @action(detail=False, methods=['patch']) # , url_path='update-balance'
    @queue_request
    def update_balance(self, request):
        """
        Admin endpoint to update user's starcoins balance
        """
        user_id = QueryData.check_params(request, 'user_id')
        new_balance = QueryData.check_params(request, 'new_balance')

        user = UserMethods.get(user_id=user_id)
        
        return UserMethods.update_balance(user, new_balance)

    # PATCH /api/v1/users/update_ban/?user_id=1&ban=True
    @action(detail=False, methods=['patch']) # , url_path='update_ban'
    @queue_request
    def update_ban(self, request):
        """
        Баним или разбаним пользователя
        """
        user_id = QueryData.check_params(request, 'user_id')
        ban = QueryData.check_params(request, 'ban')
        
        user = UserMethods.get(user_id=user_id)
        
        return UserMethods.update_ban(user, ban)

    # POST /api/v1/users/process_referral/
    @action(detail=False, methods=['post']) # , url_path='process-referral'
    @queue_request
    def process_referral(self, request):
        """
        Process referral rewards for both referrer and referee
        """
        user_id = QueryData.check_params(request, 'user_id')
        
        user = UserMethods.get(user_id=user_id)
        
        return ReferralConnectionsMethods.process_referral(user)

    # PATCH /api/v1/users/update_vk_id/?user_id=1&vk_id=1
    @action(detail=False, methods=['patch']) # , url_path='update-vk-id'
    @queue_request
    def update_vk_id(self, request):
        """
        Update user's VK ID
        """
        user_id = QueryData.check_params(request, 'user_id')
        vk_id = QueryData.check_params(request, 'vk_id')
        
        UserMethods.check_vk_id(vk_id)

        user = UserMethods.get(pk=user_id)
        
        return UserMethods.update_vk_id(user, vk_id)

    # GET /api/v1/users/vk_ids/
    @action(detail=False, methods=['get'])
    @queue_request
    def get_all_vk_users(self, request):
        """
        Получаем все id из ВК
        """
        return UserMethods.get_all_vk_users()

    # DELETE /api/v1/users/back_vk_id/?user_id=1&chat_id_name=1
    @action(detail=False, methods=['delete']) # , url_path='update-vk-id'
    @queue_request
    def back_vk_id(self, request):
        """
        Back user's VK ID
        """
        user_id = QueryData.check_params(request, 'user_id')
        chat_id_name = QueryData.check_params(request, 'chat_id_name')

        user = UserMethods.get(pk=user_id)
        
        return UserMethods.back_vk_id(user, chat_id_name)

    # GET /api/v1/users/unregistered_users/
    @action(detail=False, methods=['get'])
    @queue_request
    def unregistered_users(self, request):
        return UserMethods.unregistered_users()

    # GET /api/v1/users/active_users/
    @action(detail=False, methods=['get'])
    @queue_request
    def active_users(self, request):
        """ active_users
        Получаем всех активных пользователей
        """
        min_rang = int(request.query_params.get('min_rang', 0))
        max_rang = int(request.query_params.get('max_rang', 999999))
        
        return UserMethods.active_users(min_rang, max_rang)


class FamilyTiesViewSet(ViewSet):
    
    # POST /api/v1/family-ties/
    @queue_request
    def create(self, request):
        """Создать новую связь
        - Проверяем есть ли уже такая связь;
        - Получаем связи пользователя:
          - Если нету, то даем 5 коинов;
        - Скрещиваем связи;
        - Создаем нужную связь.
        """
        from_user_id = QueryData.check_params(request, 'from_user')
        to_user_id = QueryData.check_params(request, 'to_user')
        
        from_user = UserMethods.get(user_id=from_user_id)
        to_user = UserMethods.get(user_id=to_user_id)
        
        return FamilyTiesMethods.create(from_user, to_user)
    
    # GET /api/v1/family-ties/{user_id}/get_family/
    @action(detail=True, methods=['get'])
    @queue_request
    def get_family(self, request, pk=None):
        """Получить все связи пользователя"""
        user = UserMethods.get(user_id=pk)
        
        return FamilyTiesMethods.get_family(user)

    # GET /api/v1/family-ties/get_target_ties/?parent_id=213&user_id=456
    @action(detail=False, methods=['get'])
    @queue_request
    def get_target_ties(self, request):
        """Получить конкретную связь между пользователями"""
        parent_id = QueryData.check_params(request, 'parent_id')
        user_id = QueryData.check_params(request, 'user_id')

        parent = UserMethods.get(user_id=parent_id)
        user = UserMethods.get(user_id=user_id)

        return FamilyTiesMethods.get_target_ties(parent, user)


class PurchasesViewSet(ViewSet):
    
    # GET /api/v1/purchases/{id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """Получить покупку по ID"""
        purchase = PurchasesMethods.get(pk=pk)
        serializer = PurchasesSerializer(purchase)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
            )

    # GET /api/v1/purchases/
    @queue_request
    def list(self, request):
        """Получить все незавершенные покупки"""
        queryset = PurchasesMethods.all().filter(completed=False)
        serializer = PurchasesSerializer(queryset, many=True)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
            )

    # POST /api/v1/purchases/
    @queue_request
    def create(self, request):
        """Создать новую покупку"""
        user_id = QueryData.check_params(request, 'user_id')
        title = QueryData.check_params(request, 'title')
        description = QueryData.check_params(request, 'description')
        cost = QueryData.check_params(request, 'cost')
        product_id = QueryData.check_params(request, 'product_id')
        
        user = UserMethods.get(user_id=user_id)
        product = Pikmi_ShopMethods.get(pk=product_id)
        
        return PurchasesMethods.create(user, product, title, description, cost)

    # GET /api/v1/purchases/user_purchases/?completed=False&user_id=456
    @action(detail=False, methods=['get'])
    @queue_request
    def user_purchases(self, request):
        """Получить покупки конкретного пользователя"""
        completed = QueryData.check_params(request, 'completed')
        user_id = QueryData.check_params(request, 'user_id')
        
        user = UserMethods.get(user_id=user_id)
        
        return PurchasesMethods.user_purchases(user, completed)

    # PATCH /api/v1/purchases/confirm_purchase/?task_id=456
    @action(detail=False, methods=['patch']) # , url_path='confirm-purchase'
    @queue_request
    def confirm_purchase(self, request):
        """
        Confirm purchase
        """
        task_id = QueryData.check_params(request, 'task_id')

        purchase = PurchasesMethods.get(pk=task_id)
        
        return PurchasesMethods.confirm_purchase(purchase)


class PikmiShopViewSet(ViewSet):
    
    # GET /api/v1/pikmi-shop/
    @queue_request
    def list(self, request):
        """Получить все продукты (аналог get_all_products)"""
        queryset = Pikmi_ShopMethods.all().order_by('_price')
        serializer = PikmiShopSerializer(queryset, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/pikmi-shop/{id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """Получить продукт по ID (аналог get_by_id)"""
        product = Pikmi_ShopMethods.get(pk=pk)
        serializer = PikmiShopSerializer(product)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )


class WorkKeysViewSet(ViewSet):
    
    # POST /api/v1/work-keys/
    @queue_request
    def create(self, request):
        """Создать новый ключ (аналог create)"""
        key = WorkKeysMethods.create()
        serializer = WorkKeysSerializer(key)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED
            )

    # GET /api/v1/work-keys/check_by_key/?key=asd123
    @action(detail=False, methods=['get'])
    @queue_request
    def check_by_key(self, request):
        key_value = QueryData.check_params(request, 'key')
        
        key = WorkKeysMethods.get(key=key_value)

        return Response(
            not bool(key.from_user),
            status=status.HTTP_200_OK
            )

    # PATCH /api/v1/work-keys/register_with_key/?user_id=456&key=asd123
    @action(detail=False, methods=['patch']) # , url_path='register-with-key'
    @queue_request
    def register_with_key(self, request):
        """
        Complete user registration and associate work key
        """
        user_id = QueryData.check_params(request, 'user_id')
        key = QueryData.check_params(request, 'key')
        user = UserMethods.get(pk=user_id)
        
        work_key = WorkKeysMethods.get(key=key)
        
        return WorkKeysMethods.register_with_key(user, work_key)


class BonusesViewSet(ViewSet):

    # GET /api/v1/bonuses/{id}/
    @queue_request
    def retrieve(self, request, pk=None):
        bonus = BonusesMethods.get(pk=pk)
        serializer = BonusesSerializer(bonus)
        
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # POST /api/v1/bonuses/
    @queue_request
    def create(self, request):
        type_bonus = QueryData.check_params(request, 'type_bonus')
        expires_at = QueryData.check_params(request, 'expires_at')
        
        try:
            expires_at = datetime.fromisoformat(expires_at)
            # expires_at = pytz.utc.localize(expires_at)
        except ValueError:
            return Response(
                {
                    'error': 'Invalid datetime format'
                }, 
                status=status.HTTP_400_BAD_REQUEST
                )
        
        if type_bonus == 'add_starcoins':
            value = QueryData.check_params(request, 'value')
            max_quantity = QueryData.check_params(request, 'max_quantity')

            bonus_obj = BonusesMethods.create_add_starcoins(
                value=value,
                max_quantity=max_quantity
            )
        elif type_bonus == 'click_scale':
            value = QueryData.check_params(request, 'value')
            duration = QueryData.check_params(request, 'duration_hours')

            bonus_obj = BonusesMethods.create_click_scale(
                value=value,
                duration_hours=duration
            )
        elif type_bonus == 'energy_renewal':
            duration = QueryData.check_params(request, 'duration_hours')

            bonus_obj = BonusesMethods.create_energy_renewal(
                duration_hours=duration
            )
        else:
            return Response(
                {'error': 'Invalid bonus type'}, 
                status=status.HTTP_400_BAD_REQUEST
                )
        
        return BonusesMethods.create(
            type_bonus=type_bonus,
            expires_at=expires_at,
            bonus_obj=bonus_obj
        )

    # POST /api/v1/bonuses/claim_bonus/
    @action(detail=False, methods=['post']) # , url_path='claim-bonus'
    @queue_request
    def claim_bonus(self, request):
        """Обрабатывает получение бонуса пользователем"""
        user_id = QueryData.check_params(request, 'user_id')
        bonus_id = QueryData.check_params(request, 'bonus_id')
        
        # Получаем объекты
        user = UserMethods.get(pk=user_id)
        bonus = BonusesMethods.get(pk=bonus_id)
        
        # Проверка активности бонуса
        if not bonus.active:
            return Response(
                {'text': 'not_active'},
                status=status.HTTP_200_OK
            )
        
        now = datetime.now(pytz.timezone('Europe/Moscow'))
        
        # Обработка разных типов бонусов
        if bonus.type_bonus == "add_starcoins":
            return UseBonusesMethods.create_add_starcoins(
                bonus=bonus,
                user=user,
                now=now
            )
        elif bonus.type_bonus == "energy_renewal":
            game = LumberjackGameMethods.get(user=user).first()
            return UseBonusesMethods.create_energy_renewal(
                bonus=bonus,
                game=game,
                now=now
            )
        else:
            return Response(
                {'text': 'undefined_error'},
                status=status.HTTP_200_OK
            )


class UseBonusesViewSet(ViewSet):

    # GET /api/v1/use-bonuses/?user_id=123&bonus_id=123
    @action(detail=False, methods=['get'])
    @queue_request
    def get_bonus(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        bonus_id = QueryData.check_params(request, 'bonus_id')

        user = UserMethods.get(pk=user_id)
        bonus = BonusesMethods.get(pk=bonus_id)

        user_bonuses = UseBonusesMethods.get(user=user, bonus=bonus)

        # NOTE тут раньше несколько записей возвращалось
        return Response(
            UseBonusesSerializer(user_bonuses).data,
            status=status.HTTP_200_OK
            )

    # POST /api/v1/use-bonuses/
    @queue_request
    def create(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        bonus_id = QueryData.check_params(request, 'bonus_id')
        
        user = UserMethods.get(pk=user_id)
        bonus = BonusesMethods.get(pk=bonus_id)
        
        return UseBonusesMethods.create(
            user,
            bonus
        )


class QuestsViewSet(ViewSet):

    # GET /api/v1/quests/
    @queue_request
    def list(self, request):
        quests = QuestMethods.all().filter(active=True)
        serializer = QuestsSerializer(quests, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
            )

    # GET /api/v1/quests/get_info/?user_id=asd&quest_id=asd
    @action(detail=False, methods=['get'])
    @queue_request
    def get_info(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')

        user = UserMethods.get(user_id=user_id)
        quest = QuestMethods.get(pk=quest_id)

        return QuestMethods.get_info(
            user=user,
            quest=quest
        )

    # GET /api/v1/quests/active/?user_id=123123
    @action(detail=False, methods=['get'])
    @queue_request
    def active(self, request):
        user_id = QueryData.check_params(request, 'user_id')
    
        user = UserMethods.get(pk=user_id)
        rang = RangService().get_user_rang(user)
        
        return QuestMethods.active(user, rang)


class UseQuestsViewSet(ViewSet):

    # GET /api/v1/use-quests/get_quests/?user_id=123&quest_id=123
    @action(detail=False, methods=['get'])
    @queue_request
    def get_quests(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')

        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)

        return UseQuestMethods.get_quests(user, quest)

    # POST /api/v1/use-quests/
    @queue_request
    def create(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')
        
        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)
        
        return UseQuestMethods.create(user, quest)

    # POST /api/v1/use-quests/create_idea_daily/
    @action(detail=False, methods=['post'])
    @queue_request
    def create_idea_daily(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')

        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)

        return UseQuestMethods.create_idea_daily(user, quest)

    # PATCH /api/v1/use-quests/success_idea_daily/?user_id=123&quest_id=123
    @action(detail=False, methods=['patch'])
    @queue_request
    def success_idea_daily(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')
        logger.debug(f"success_idea_daily {user_id=} {quest_id=}")

        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)
        
        use_quest_obj = UseQuestMethods.get(user=user, quest=quest)
        logger.debug(f"success_idea_daily {use_quest_obj=}")

        return Quest_MA_Methods.success_idea_daily(user, quest, use_quest_obj)

    # DELETE /api/v1/use-quests/delete_idea/?user_id=123&quest_id=123
    @action(detail=False, methods=['delete'])
    @queue_request
    def delete_idea(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')
        logger.debug(f"delete_idea {user_id=} {quest_id=}")

        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)
        
        use_quest_obj = UseQuestMethods.get(user=user, quest=quest)
        logger.debug(f"delete_idea {use_quest_obj=}")
        
        return Quest_MA_Methods.delete_idea(quest, use_quest_obj)
    
    # GET /api/v1/use-quests/sub_tg_chat/?quest_id=123
    @action(detail=False, methods=['get'])
    @queue_request
    def sub_tg_chat(self, request):
        quest_id = QueryData.check_params(request, 'quest_id')

        quest = QuestMethods.get(pk=quest_id)

        return UseQuestMethods.sub_tg_chat(quest)
    
    # GET /api/v1/use-quests/sub_vk_chat/?quest_id=123
    @action(detail=False, methods=['get'])
    @queue_request
    def sub_vk_chat(self, request):
        quest_id = QueryData.check_params(request, 'quest_id')

        quest = QuestMethods.get(pk=quest_id)

        return UseQuestMethods.sub_vk_chat(quest)

    # DELETE /api/v1/use-quests/back_tg_quest/?user_id=123&quest_id=123
    @action(detail=False, methods=['delete'])
    @queue_request
    def back_tg_quest(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        quest_id = QueryData.check_params(request, 'quest_id')

        user = UserMethods.get(pk=user_id)
        quest = QuestMethods.get(pk=quest_id)
        
        use_quest = UseQuestMethods.get(user=user, quest=quest)
            
        return UseQuestMethods.back_tg_quest(user, quest, use_quest)


class CopyBaseViewSet(ViewSet):

    # POST /api/v1/copy-base/
    @queue_request
    def create(self, request):
        """
        Возвращаем базу данных
        """
        return CopyBaseMethods().copy_base()


class RangsViewSet(ViewSet):

    # GET /api/v1/rangs/role/
    @action(detail=False, methods=['get'])
    @queue_request
    def role(self, request):
        role = QueryData.check_params(request, 'role')
        
        return RangsMethods.role(role)


class QuestModerationAttemptViewSet(ViewSet):

    # POST /api/v1/quest-moderation-attempt/delete_old_quest/
    @action(detail=False, methods=['post'])
    @queue_request
    def delete_old_quest(self, request):
        return Quest_MA_Methods.delete_old_quest()


class PromocodesViewSet(ViewSet):

    # POST /api/v1/promocodes/
    @queue_request
    def create(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        code = QueryData.check_params(request, 'code')
        logger.debug(code)
        
        check_sql_injection(code)
        
        user = UserMethods.get(pk=user_id)
        promocode = CodesMethods('promo').get(code=code)
        logger.debug(promocode)
        
        return CodesMethods('promo').create(user, promocode)


class ManagementLinksViewSet(ViewSet):

    # POST /api/v1/management-link/
    @queue_request
    def create(self, request):
        user_id = QueryData.check_params(request, 'user_id')
        utm = QueryData.check_params(request, 'utm')
        logger.debug(utm)
        
        check_sql_injection(utm)
        
        user = UserMethods.get(pk=user_id)
        management_link = CodesMethods('links').get(code=utm)
        logger.debug(management_link)
        
        return CodesMethods('links').create(user, management_link)


class InteractiveGameViewSet(ViewSet):
    
    # GET /api/v1/interactive-game/{game_id}/
    @queue_request
    def retrieve(self, request, pk=None):
        """
        Получаем игру
        """
        game = InteractiveGameMethods.get(pk=pk)
        
        serializer_game = InteractiveGameMethods.active(game)
        return Response(
            serializer_game.data, 
            status=status.HTTP_200_OK
        )
    
    # POST /api/v1/interactive-game/
    @queue_request
    def create(self, request):
        """
        Создаем игру
        """
        user_id = QueryData.check_params(request, 'user_id')
        data = QueryData.check_params(request, 'data')
        
        user = UserMethods.get(pk=user_id)
        
        return InteractiveGameMethods.create(user, data)

    # DELETE /api/v1/interactive-game/
    @queue_request
    def delete(self, request, pk=None):
        """
        Удаляем игру
        """
        game = InteractiveGameMethods.get(pk=pk)
        
        return InteractiveGameMethods.delete(game)

    # POST /api/v1/interactive-game/success_game/
    @action(detail=False, methods=['post'])
    @queue_request
    def success_game(self, request):
        game_id = QueryData.check_params(request, 'game_id')
        game = InteractiveGameMethods.get(pk=game_id)
        
        return InteractiveGameMethods.success_game(game)

    # POST /api/v1/interactive-game/invite_game/
    @action(detail=False, methods=['post'])
    @queue_request
    def invite_game(self, request):
        game_id = QueryData.check_params(request, 'game_id')
        user_id = QueryData.check_params(request, 'user_id')
        
        game = InteractiveGameMethods.get(pk=game_id)
        user = UserMethods.get(pk=user_id)
        
        return InteractiveGameMethods.invite_game(user, game)

    # DELETE /api/v1/interactive-game/{game_id}/delete_pending/
    @action(detail=True, methods=['delete'])
    @queue_request
    def delete_pending(self, request, pk=None):
        # game_id = QueryData.check_params(request, 'game_id')
        game = InteractiveGameMethods.get(pk=pk)

        return InteractiveGameMethods.delete_pending(game)

    # PATCH /api/v1/interactive-game/{game_id}/start_game/
    @action(detail=True, methods=['patch'])
    @queue_request
    def start_game(self, request, pk=None):
        # game_id = QueryData.check_params(request, 'game_id')
        game = InteractiveGameMethods.get(pk=pk)

        return InteractiveGameMethods.start_game(game)

    # GET /api/v1/interactive-game/get_info/
    @action(detail=False, methods=['get'])
    @queue_request
    def get_info(self, request):
        game_id = QueryData.check_params(request, 'game_id')
        game = InteractiveGameMethods.get(pk=game_id)
        
        serializer_game = InteractiveGameMethods.active(game)
        
        return InteractiveGameMethods.get_info(game, serializer_game)

    # PATCH /api/v1/interactive-game/{game_id}/end_game/
    @action(detail=True, methods=['patch'])
    @queue_request
    def end_game(self, request, pk=None):
        # game_id = QueryData.check_params(request, 'game_id')
        winers = QueryData.check_params(request, 'winers')
        
        winers = [int(winer) for winer in winers]
        
        game = InteractiveGameMethods.get(pk=pk)
        
        return InteractiveGameMethods.end_game(game, winers)

