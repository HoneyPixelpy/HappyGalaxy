from datetime import datetime, timedelta
from typing import List, Optional, Union
from loguru import logger
import pytz

from rest_framework import status
from rest_framework.response import Response
from django.db.models import Prefetch
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from bot.schemas.game import BoostData
from conf.settings import DEBUG

from ..models import Bonuses, GameData, GeoHunter, InteractiveGames, Lumberjack_Game, Sigma_Boosts, Users
from ..serializers import GameDataSerializer, GeoHunterSerializer, InteractiveGamesSerializer, LumberjackGameSerializer, SigmaBoostsSerializer, UserSerializer
from ..schemas import boosts_data
from .error import RaisesResponse
from .abstract import *


INTERACTIVE_INVITE_TIME = 10


class SigmaBoostsMethods:
    @classmethod
    def get(
        cls, 
        pk: Optional[int] = None,
        user: Optional[Users] = None
        ) -> Sigma_Boosts:
        """
        Получаем или создаем информацию о бустах
        """
        try:
            if pk:
                return Sigma_Boosts.objects.get(pk=pk)
            elif user:
                return Sigma_Boosts.objects.get(user=user)
            else:
                raise Exception("Нет нужного аргумента")
        except Sigma_Boosts.DoesNotExist:
            return Sigma_Boosts.objects.create(user=user)
    @classmethod
    def _check_passive_income_level(
        cls, 
        user: Users,
        boosts_user: Sigma_Boosts
        ) -> Optional[RaisesResponse]:
        """
        Удостоверяемся, что пассивный доход
        прокачен хоть на один уровень
        """
        if boosts_user.passive_income_level == 0:
            raise RaisesResponse(
                data={'income': 0, 'user': UserSerializer(user).data},
                status=status.HTTP_200_OK
            )
    @classmethod
    def _calculate_elapsed_hours(
        cls, 
        user: Users,
        boosts_user: Sigma_Boosts
        ) -> Union[RaisesResponse, int]:
        """
        Расчитываем сколько часов прошло с последнего 
        зачисления пассивного дохода
        """
        now = timezone.now().astimezone(
            pytz.timezone('Europe/Moscow')
            )
        seconds_passed = (
            now - boosts_user.last_passive_claim
            ).total_seconds()
        full_hours = int(seconds_passed // 3600)
        
        if full_hours < 1:
            raise RaisesResponse(
                data={'income': 0, 'user': UserSerializer(user).data},
                status=status.HTTP_200_OK
            )
        return full_hours
    @classmethod
    def _calculate_passive_income(
        cls, 
        boosts_user: Sigma_Boosts,
        full_hours: int
        ) -> float:
        """
        Расчитываем доход от пассивки
        """
        return full_hours * boosts_data.passive_income_level.value_by_level(
            boosts_user.passive_income_level
        )
    @classmethod
    def _add_passive_income(
        cls, 
        user: Users,
        boosts_user: Sigma_Boosts,
        full_hours: int,
        income: float
        ) -> None:
        """
        Обновление данных о последнем зачислении пассивного дохода
        и зачисляем доход пользователю
        """
        boosts_user.last_passive_claim = boosts_user.last_passive_claim + timedelta(hours=full_hours)
        boosts_user.save()
        
        user.starcoins += income
        user.save()
    @classmethod
    def _check_possibility_upgrade_by_starcoins(
        cls, 
        user: Users,
        boost_data: BoostData,
        boost_level: int
        ) -> None:
        """
        Проверяем позволяют ли средстава
        пользователя улучшить буст
        """
        if user.starcoins < boost_data.price(boost_level):
            raise RaisesResponse(
                data=False,
                status=status.HTTP_200_OK
            )
    @classmethod
    def _check_possibility_upgrade_by_max_level(
        cls, 
        boost_data: BoostData,
        boost_level: int
        ) -> None:
        """
        Проверяем не прокачен ли буст
        на максимальный уровень
        """
        if boost_level >= boost_data.max_level():
            raise RaisesResponse(
                data=False,
                status=status.HTTP_200_OK
            )
    @classmethod
    def _upgrade_boost(
        cls, 
        user_boosts: Sigma_Boosts,
        name: str,
        boost_level: int
        ) -> None:
        """
        Проверяем не прокачен ли буст
        на максимальный уровень
        
        Если мы впервые качаем пассивку, то
        выставляем время последнего зачисления
        """
        if name == 'passive_income_level' and user_boosts.passive_income_level == 0:
            user_boosts.last_passive_claim = datetime.now()

        setattr(user_boosts, name, boost_level + 1)
        user_boosts.save()
    @classmethod
    def _write_off_money(
        cls, 
        user: Users,
        boost_data: BoostData,
        boost_level: int
        ) -> None:
        """
        Списание средств
        """
        user.starcoins -= boost_data.price(boost_level)
        user.save()    
    @classmethod
    def _refresh_energy(
        cls, 
        game: Union[GeoHunter, Lumberjack_Game],
        name: Optional[str] = None,
        new_max_energy: Optional[int] = None
        ) -> None:
        """
        Восстанавливаем энергию
        """
        if name and new_max_energy and isinstance(game, Lumberjack_Game):
            if name == 'energy_capacity_level':
                game.max_energy = new_max_energy
            
        game.current_energy = game.max_energy
        game.last_energy_update = datetime.now()
        game.save()


class SigmaBoostsViewMethods(AbstractSigmaBoosts, SigmaBoostsMethods):
    @classmethod
    def get_by_user(
        cls, 
        boost: Sigma_Boosts
        ) -> RaisesResponse:
        raise RaisesResponse(
            SigmaBoostsSerializer(boost).data,
            status=status.HTTP_200_OK
            )
    @classmethod
    def passive_income_calculation(
        cls, 
        user: Users,
        boosts_user: Sigma_Boosts
        ) -> RaisesResponse:
        cls._check_passive_income_level(user, boosts_user)

        full_hours = cls._calculate_elapsed_hours(user, boosts_user)
        income = cls._calculate_passive_income(boosts_user, full_hours)
        
        cls.add_passive_income(user, boosts_user, full_hours, income)

        raise RaisesResponse(
            data={
                'income': income,
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def upgrade_boost(
        cls, 
        user: Users,
        user_boosts: Sigma_Boosts,
        jack_game: Lumberjack_Game,
        geo_hunter: GeoHunter,
        name: str
        ) -> RaisesResponse:
        boost_level: int = getattr(user_boosts, name)
        boost_data: BoostData = getattr(boosts_data, name)
        
        if not DEBUG:
            cls._check_possibility_upgrade_by_starcoins(user, boost_data, boost_level)
        cls._check_possibility_upgrade_by_max_level(boost_data, boost_level)
                    
        cls._upgrade_boost(user_boosts, name, boost_level)
        cls._write_off_money(user, boost_data, boost_level)
        
        if jack_game:
            cls._refresh_energy(
                jack_game,
                name,
                boost_data.value_by_level(boost_level+1)
                )
        
        if geo_hunter:
            cls._refresh_energy(geo_hunter)
        
        raise RaisesResponse(
            data={
                'emoji': boost_data.emoji(boost_level + 1),
                'level': boost_level + 1,
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def calculate_recovery_time(
        cls, 
        user_boosts: Sigma_Boosts
        ) -> RaisesResponse:
        raise RaisesResponse(
            boosts_data.recovery_level.value_by_level(user_boosts.recovery_level),
            status=status.HTTP_200_OK
        )


class GameMethods:
    @classmethod
    def refresh_energy(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        user_boosts: Sigma_Boosts
        ) -> Response:
        """Обновляет энергию"""
        force_update_energy = False
        first_click = game_user.current_energy == game_user.max_energy
        
        time_passed = datetime.now(pytz.timezone('Europe/Moscow')) - game_user.last_energy_update

        required_delay: timedelta = timedelta(
            minutes=boosts_data.recovery_level.value_by_level(user_boosts.recovery_level)
            )
        total_seconds = (required_delay - time_passed).total_seconds()
        if (total_seconds + 30) < 0 and not first_click:
            total_seconds = 0  # или обработать случай, когда время уже прошло
            force_update_energy = True

        hours, remainder = divmod(int(total_seconds), 3600)  # Преобразуем в int перед divmod
        minutes, seconds = divmod(int(remainder), 60)       # Аналогично здесь
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
        raise RaisesResponse(
            data={
                'force_update_energy': force_update_energy,
                'time_str': time_str,
                'first_click': first_click,
                'game_user': LumberjackGameSerializer(game_user).data if isinstance(
                    game_user, Lumberjack_Game) else GeoHunterSerializer(game_user).data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def check_energy(
        cls,
        boosts_user: Sigma_Boosts,
        game_user: Union[Lumberjack_Game, GeoHunter],
        game_user_two: Union[Lumberjack_Game, GeoHunter],
        energy_in_click: int
        ) -> int:
        """
        Проверяет энергию
        Получаем награду за клик
        """
        if game_user.current_energy < energy_in_click:
            raise RaisesResponse(
                data={'error': 'Not enough energy'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if game_user.current_energy == game_user.max_energy:
            game_user.last_energy_update = datetime.now()
            game_user_two.last_energy_update = datetime.now()
            game_user_two.save()

        return cls._apply_click_bonuses(
            boosts_data.income_level.value_by_level(boosts_user.income_level)
            )
    @classmethod
    def _apply_click_bonuses(
        cls, 
        base_income: float
        ) -> float:
        """Применяет все активные бонусы к доходу за клик"""
        current_time = datetime.now(pytz.timezone('Europe/Moscow'))
        active_bonuses = Bonuses.objects.filter(
            type_bonus="click_scale",
            active=True,
            _expires_at__gt=timezone.now()
        ).prefetch_related(
            Prefetch('content_type', queryset=ContentType.objects.all())
        ).all()

        for bonus in active_bonuses:
            # Проверяем срок действия
            if bonus.expires_at < current_time:
                bonus.active = False
                bonus.save()
                continue
            logger.debug(base_income)
            logger.debug(bonus.bonus_data)
            logger.debug(bonus.bonus_data.value)
            # Применяем бонус
            bonus_data = bonus.bonus_data
            base_income *= bonus_data.value
            logger.debug(base_income)
            break  # Применяем только первый активный бонус

        return round(base_income, 3)
    @classmethod
    def restore_energy(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        game_user_two: Union[GeoHunter, Lumberjack_Game]
        ):
        """
        Полностью восстанавливает энергию игрока
        """
        game_user.current_energy = game_user.max_energy
        game_user.last_energy_update = datetime.now()
        game_user.save()
        
        game_user_two.current_energy = game_user_two.max_energy
        game_user_two.last_energy_update = datetime.now()
        game_user_two.save()

        raise RaisesResponse(
            data={
                'success': True,
                'current_energy': game_user.current_energy,
                'max_energy': game_user.max_energy,
                'last_updated': game_user.last_energy_update.isoformat()
            },
            status=status.HTTP_200_OK
        )

class LumberjackGameMethods(GameMethods):
    @classmethod
    def get(
        cls, 
        pk: Optional[int] = None,
        user: Optional[Users] = None
        ) -> Lumberjack_Game:
        """Получить кликер"""
        try:
            if pk:
                return Lumberjack_Game.objects.get(pk=pk)
            else:
                return Lumberjack_Game.objects.get(user=user)
        except Lumberjack_Game.DoesNotExist:
            return Lumberjack_Game.objects.create(user=user)
    @classmethod
    def all(cls) -> List[Lumberjack_Game]:
        """Получить кликеры"""
        return Lumberjack_Game.objects.all()
    @classmethod
    def update_grid(
        cls,
        game_user: Lumberjack_Game,
        grid: List[List[str]]
        ) -> Response:
        """
        Обновляет игровое поле пользователя
        """
        # Проверяем что grid имеет правильный формат (4x5)
        if not isinstance(grid, list) or len(grid) != 4 or any(len(row) != 5 for row in grid):
            raise RaisesResponse(
                data={'error': 'Grid must be 4x5 matrix'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        game_user.current_grid = grid
        game_user.save()
        
        raise RaisesResponse(
            data=LumberjackGameSerializer(game_user).data,
            status=status.HTTP_200_OK
        )
    @classmethod
    def process_click(
        cls, 
        user: Users,
        game_user: Lumberjack_Game,
        game_user_two: GeoHunter,
        boosts_user: Sigma_Boosts,
        energy_in_click: int,
        row: int,
        col: int
        ) -> Response:
        """
        Обрабатывает клик в игре с учетом всех бустов и обновляет состояние
        """
        income_per_click = super().check_energy(
            boosts_user,
            game_user,
            game_user_two,
            energy_in_click
        )
        
        # Основная логика обработки клика
        game_user.total_clicks += 1
        
        # Обновление игрового состояния
        game_user.current_grid[row][col] = str(income_per_click)
        game_user.total_currency += income_per_click
        game_user.current_energy -= energy_in_click
        
        # Получаем игровые данные пользователя
        if game_user_two.current_energy > 0:
            game_user_two.current_energy -= energy_in_click
            game_user_two.save()
        
        user.starcoins += income_per_click
        
        game_user.save()
        user.save()
        
        raise RaisesResponse(
            data=income_per_click,
            status=status.HTTP_200_OK
            )

class GeoHunterMethods(GameMethods):
    @classmethod
    def get(
        cls, 
        pk: Optional[int] = None,
        user: Optional[Users] = None
        ) -> GeoHunter:
        """Получить геохантер"""
        try:
            if pk:
                return GeoHunter.objects.get(pk=pk)
            else:
                return GeoHunter.objects.get(user=user)
        except GeoHunter.DoesNotExist:
            return GeoHunter.objects.create(
                user=user,
                current_energy=100,
                max_energy=100
            )
    @classmethod
    def all(cls) -> List[GeoHunter]:
        """Получить геохантеры"""
        return GeoHunter.objects.all()
    @classmethod
    def process_click(
        cls, 
        user: Users,
        game_user: Lumberjack_Game,
        game_user_two: GeoHunter,
        boosts_user: Sigma_Boosts,
        energy_in_click: int,
        user_choice: int
        ) -> Response:
        """
        Обрабатывает клик в игре с учетом всех бустов и обновляет состояние
        """
        income_per_click = super().check_energy(
            boosts_user,
            game_user,
            game_user_two,
            energy_in_click
        )

        game_user.current_energy -= energy_in_click
        
        # Получаем игровые данные пользователя
        if game_user_two.current_energy > 0:
            game_user_two.current_energy -= energy_in_click
            game_user_two.save()
        
        if user_choice:            
            # Обновление игрового состояния
            game_user.total_true += 1
            game_user.total_currency += income_per_click
            user.starcoins += income_per_click

            game_user.save()
            user.save()

        else:
            game_user.total_false += 1
            game_user.save()

        return GeoHunterSerializer(game_user).data

class BoostsMethods:
    @classmethod
    def catalog(
        cls, 
        user_boosts: Sigma_Boosts
        ) -> Response:
        """
        Получаем данные для вознаграждений
        """
        result_data = []
        for name, value in user_boosts.__dict__.items():
            if "_level" in name:
                boost_data: BoostData = getattr(boosts_data, name)
                result_data.append(
                    {
                        'name': name,
                        'value': value,
                        'max_level': boost_data.max_level()
                    }
                )

        raise RaisesResponse(
            data=result_data,
            status=status.HTTP_200_OK
        )
    @classmethod
    def info(
        cls,
        user_boosts: Sigma_Boosts,
        name: str
        ):
        """
        Получаем данные для вознаграждений
        """
        boost_level: int = getattr(user_boosts, name)
        boost_data: BoostData = getattr(boosts_data, name)
        
        raise RaisesResponse(
            data={
                'boost_level': boost_level,
                'max_level': boost_data.max_level(),
                'emoji': boost_data.emoji(boost_level),
                'price': boost_data.price(boost_level),
            },
            status=status.HTTP_200_OK
        )

class InteractiveGameMethods:
    @classmethod
    def get(
        cls, 
        pk: Optional[int] = None
        ) -> InteractiveGames:
        """Получить игру"""
        try:
            if pk:
                return InteractiveGames.objects.get(pk=pk)
            else:
                raise Exception('Game not found')
        except InteractiveGames.DoesNotExist:
            raise RaisesResponse(
                data={'error': 'InteractiveGames not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    @classmethod
    def active(
        cls, 
        game: InteractiveGames
        ) -> InteractiveGamesSerializer:
        if game.game_status in ['expired', 'canceled', 'ended']:
            raise RaisesResponse(
                data={'error': 'Game is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return InteractiveGamesSerializer(game)
    @classmethod
    def create(
        cls, 
        user: Users,
        data: dict
        ) -> Response:
        data.update({'user': user})

        game = InteractiveGames.objects.create(**data)
        
        raise RaisesResponse(
            data=InteractiveGamesSerializer(game).data, 
            status=status.HTTP_201_CREATED
        )
    @classmethod
    def delete(
        cls, 
        game: InteractiveGames
        ) -> Response:
        serializer_game = InteractiveGamesSerializer(game)
        game.delete()
        raise RaisesResponse(
            data=serializer_game.data, 
            status=status.HTTP_200_OK
        )
    @classmethod
    def success_game(
        cls, 
        game: InteractiveGames
        ) -> Response:
        game.game_status = 'ready'
        game.start_invite_at = datetime.now(pytz.utc) # pytz.timezone('Europe/Moscow')
        game.save()
        
        GameData.objects.create(
            user=game.user,
            game=game,
            creator=True
        )

        serializer_game = InteractiveGamesSerializer(game)
        raise RaisesResponse(
            data=serializer_game.data, 
            status=status.HTTP_200_OK
        )
    @classmethod
    def invite_game(
        cls, 
        user: Users,
        game: InteractiveGames
        ) -> Response:
        game_datas = GameData.objects.filter(game=game)
        logger.warning(game.max_players and game.max_players <= game_datas.count())
        if game.max_players and game.max_players < game_datas.count():
            raise RaisesResponse(
                data={'error': 'Количество игроков превышает максимальное количество'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.warning(game.game_status)
        if game.game_status != 'ready':
            raise RaisesResponse(
                data={'error': 'Игра не готова'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        level = user.get_current_rang().level
        logger.warning((
            game.min_rang and game.min_rang > level
            ) or (game.max_rang and level > game.max_rang))
        if (
            game.min_rang and game.min_rang > level
            ) or (game.max_rang and level > game.max_rang):
            raise RaisesResponse(
                data={'error': 'У вас недостаточно прав для начала игры'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.warning((
            game.start_invite_at + timedelta(minutes=INTERACTIVE_INVITE_TIME)
            ) < datetime.now(pytz.timezone('Europe/Moscow')))
        if (
            game.start_invite_at + timedelta(minutes=INTERACTIVE_INVITE_TIME)
            ) < datetime.now(pytz.timezone('Europe/Moscow')):
            raise RaisesResponse(
                data={'error': 'Время приглашения истекло'},
                status=status.HTTP_400_BAD_REQUEST
            )

        GameData.objects.create(
            user=user,
            game=game
        )
        
        serializer_game = InteractiveGamesSerializer(game)
        raise RaisesResponse(
            data=serializer_game.data, 
            status=status.HTTP_200_OK
        )
    @classmethod
    def delete_pending(
        cls, 
        game: InteractiveGames
        ) -> Response:
        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]
        serializer_users = UserSerializer(users_in_game, many=True)
        serializer_game = InteractiveGamesSerializer(game)
        
        game.delete()
        
        raise RaisesResponse(
            data={
                'users': serializer_users.data,
                'game': serializer_game.data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def start_game(
        cls, 
        game: InteractiveGames
        ) -> Response:
        if game.game_status == 'active':
            raise RaisesResponse(
                data={'error': 'Game already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]
        
        if len(users_in_game) < 2 or len(users_in_game) < game.min_players:
            raise RaisesResponse(
                data={'error': 'Not enough players in game'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        game.game_status = 'active'
        game.start_game_at = datetime.now() # pytz.timezone('Europe/Moscow')
        game.save()

        serializer_users = UserSerializer(users_in_game, many=True)
        serializer_game = InteractiveGamesSerializer(game)
        
        raise RaisesResponse(
            data={
                'users': serializer_users.data,
                'game': serializer_game.data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def get_info(
        cls, 
        game: InteractiveGames,
        serializer_game: InteractiveGamesSerializer
        ) -> Response:
        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]
        
        serializer_users = UserSerializer(users_in_game, many=True)
        
        raise RaisesResponse(
            data={
                'users': serializer_users.data,
                'game': serializer_game.data
            },
            status=status.HTTP_200_OK
        )
    @classmethod
    def end_game(
        cls, 
        game: InteractiveGames,
        winers: List[int]
        ) -> Response:
        game_datas = GameData.objects.filter(game=game)
        
        if game.reward_type == 'from_all_wins':
            reward = game.reward_starcoins / len(winers)
        else:
            reward = game.reward_starcoins
        
        # NOTE распределение награды между победителями
        for game_data in game_datas:
            if game_data.user.user_id in winers:
                game_data.result = 'win'
                game_data.reward_starcoins = reward
                game.user.starcoins += reward
                game.user.save()
            else:
                game_data.result = 'lose'
        
            game_data.completed = True
            game_data.save()
        
        game.game_status = 'ended'
        game.ended_game_at = datetime.now(pytz.utc)
        game.save()
        
        serializer_game_data = GameDataSerializer(game_datas, many=True)
        serializer_game = InteractiveGamesSerializer(game)
        
        raise RaisesResponse(
            data={
                'game_datas': serializer_game_data.data,
                'game': serializer_game.data
            },
            status=status.HTTP_200_OK
        )

