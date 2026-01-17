from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import pytz
from bot.schemas.game import BoostData
from conf.settings import DEBUG
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.utils import timezone
from loguru import logger
from rest_framework import status
from rest_framework.response import Response

from ..models import (
    Bonuses,
    GameData,
    GeoHunter,
    InteractiveGames,
    Lumberjack_Game,
    Sigma_Boosts,
    Users,
)
from ..schemas import boosts_data
from ..serializers import (
    GameDataSerializer,
    GeoHunterSerializer,
    InteractiveGamesSerializer,
    LumberjackGameSerializer,
    SigmaBoostsSerializer,
    UserSerializer,
)
from .abstract import *
from .error import RaisesResponse

INTERACTIVE_INVITE_TIME = 10


class UserGameMethods:
    @classmethod
    def _restore_energy(
        cls,
        game: Union[GeoHunter, Lumberjack_Game],
        name: Optional[str] = None,
        new_max_energy: Optional[int] = None,
    ) -> None:
        """
        Восстанавливаем энергию
        """
        if name and new_max_energy and isinstance(game, Lumberjack_Game):
            if name == "energy_capacity_level":
                game.max_energy = new_max_energy

        game.current_energy = game.max_energy
        game.last_energy_update = datetime.now()
        game.save()


class SigmaBoostsMethods:
    @classmethod
    def get(
        cls, pk: Optional[int] = None, user: Optional[Users] = None
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
        cls, user: Users, boosts_user: Sigma_Boosts
    ) -> Optional[RaisesResponse]:
        """
        Удостоверяемся, что пассивный доход
        прокачен хоть на один уровень
        """
        if boosts_user.passive_income_level == 0:
            raise RaisesResponse(
                data={"income": 0, "user": UserSerializer(user).data},
                status=status.HTTP_200_OK,
            )

    @classmethod
    def _calculate_elapsed_hours(
        cls, user: Users, boosts_user: Sigma_Boosts
    ) -> Union[RaisesResponse, int]:
        """
        Расчитываем сколько часов прошло с последнего
        зачисления пассивного дохода
        """
        now = timezone.now().astimezone(pytz.timezone("Europe/Moscow"))
        seconds_passed = (now - boosts_user.last_passive_claim).total_seconds()
        full_hours = int(seconds_passed // 3600)

        if full_hours < 1:
            raise RaisesResponse(
                data={"income": 0, "user": UserSerializer(user).data},
                status=status.HTTP_200_OK,
            )
        return full_hours

    @classmethod
    def _calculate_passive_income(
        cls, boosts_user: Sigma_Boosts, full_hours: int
    ) -> float:
        """
        Расчитываем доход от пассивки
        """
        return full_hours * boosts_data.passive_income_level.value_by_level(
            boosts_user.passive_income_level
        )

    @classmethod
    def _add_passive_income(
        cls, user: Users, boosts_user: Sigma_Boosts, full_hours: int, income: float
    ) -> None:
        """
        Обновление данных о последнем зачислении пассивного дохода
        и зачисляем доход пользователю
        """
        boosts_user.last_passive_claim = boosts_user.last_passive_claim + timedelta(
            hours=full_hours
        )
        boosts_user.save()

        user.starcoins += income
        user.save()

    @classmethod
    def _check_possibility_upgrade_by_starcoins(
        cls, user: Users, boost_data: BoostData, boost_level: int
    ) -> None:
        """
        Проверяем позволяют ли средстава
        пользователя улучшить буст
        """
        if user.starcoins < boost_data.price(boost_level):
            raise RaisesResponse(data=False, status=status.HTTP_200_OK)

    @classmethod
    def _check_possibility_upgrade_by_max_level(
        cls, boost_data: BoostData, boost_level: int
    ) -> None:
        """
        Проверяем не прокачен ли буст
        на максимальный уровень
        """
        if boost_level >= boost_data.max_level():
            raise RaisesResponse(data=False, status=status.HTTP_200_OK)

    @classmethod
    def _upgrade_boost(
        cls, user_boosts: Sigma_Boosts, name: str, boost_level: int
    ) -> None:
        """
        Проверяем не прокачен ли буст
        на максимальный уровень

        Если мы впервые качаем пассивку, то
        выставляем время последнего зачисления
        """
        if name == "passive_income_level" and user_boosts.passive_income_level == 0:
            user_boosts.last_passive_claim = datetime.now()

        setattr(user_boosts, name, boost_level + 1)
        user_boosts.save()

    @classmethod
    def _write_off_money(
        cls, user: Users, boost_data: BoostData, boost_level: int
    ) -> None:
        """
        Списание средств
        """
        user.starcoins -= boost_data.price(boost_level)
        user.save()


class SigmaBoostsViewMethods(SigmaBoostsMethods, UserGameMethods, AbstractSigmaBoosts):
    @classmethod
    def catalog(cls, user_boosts: Sigma_Boosts) -> RaisesResponse:
        result_data = []
        for name, value in user_boosts.__dict__.items():
            if "_level" in name:
                boost_data: BoostData = getattr(boosts_data, name)
                result_data.append(
                    {"name": name, "value": value, "max_level": boost_data.max_level()}
                )

        raise RaisesResponse(data=result_data, status=status.HTTP_200_OK)

    @classmethod
    def info(cls, user_boosts: Sigma_Boosts, name: str) -> RaisesResponse:
        boost_level: int = getattr(user_boosts, name)
        boost_data: BoostData = getattr(boosts_data, name)

        raise RaisesResponse(
            data={
                "boost_level": boost_level,
                "max_level": boost_data.max_level(),
                "emoji": boost_data.emoji(boost_level),
                "price": boost_data.price(boost_level),
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def get_by_user(cls, boost: Sigma_Boosts) -> RaisesResponse:
        raise RaisesResponse(
            SigmaBoostsSerializer(boost).data, status=status.HTTP_200_OK
        )

    @classmethod
    def passive_income_calculation(
        cls, user: Users, boosts_user: Sigma_Boosts
    ) -> RaisesResponse:
        cls._check_passive_income_level(user, boosts_user)

        full_hours = cls._calculate_elapsed_hours(user, boosts_user)
        income = cls._calculate_passive_income(boosts_user, full_hours)

        cls._add_passive_income(user, boosts_user, full_hours, income)

        raise RaisesResponse(
            data={"income": income, "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def upgrade_boost(
        cls,
        user: Users,
        user_boosts: Sigma_Boosts,
        jack_game: Lumberjack_Game,
        geo_hunter: GeoHunter,
        name: str,
    ) -> RaisesResponse:
        boost_level: int = getattr(user_boosts, name)
        boost_data: BoostData = getattr(boosts_data, name)

        if not DEBUG:
            cls._check_possibility_upgrade_by_starcoins(user, boost_data, boost_level)
        cls._check_possibility_upgrade_by_max_level(boost_data, boost_level)

        cls._upgrade_boost(user_boosts, name, boost_level)
        cls._write_off_money(user, boost_data, boost_level)

        if jack_game:
            cls._restore_energy(
                jack_game, name, boost_data.value_by_level(boost_level + 1)
            )

        if geo_hunter:
            cls._restore_energy(geo_hunter)

        raise RaisesResponse(
            data={
                "emoji": boost_data.emoji(boost_level + 1),
                "level": boost_level + 1,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def calculate_recovery_time(cls, user_boosts: Sigma_Boosts) -> RaisesResponse:
        raise RaisesResponse(
            boosts_data.recovery_level.value_by_level(user_boosts.recovery_level),
            status=status.HTTP_200_OK,
        )


class GameMethods(UserGameMethods):
    @classmethod
    def _get_active_click_bonuses(cls) -> List[Bonuses]:
        """
        Получить QuerySet активных бонусов для кликов
        """
        return (
            Bonuses.objects.filter(
                type_bonus="click_scale", active=True, _expires_at__gt=timezone.now()
            )
            .prefetch_related(
                Prefetch("content_type", queryset=ContentType.objects.all())
            )
            .all()
        )

    @classmethod
    def _is_bonus_valid(cls, bonus: Bonuses, current_time: datetime) -> bool:
        """
        Проверить валидность бонуса
        """
        return bonus.expires_at < current_time

    @classmethod
    def _deactivate_expired_bonus(cls, bonus: Bonuses) -> None:
        """
        Деактивировать просроченный бонус
        """
        bonus.active = False
        bonus.save(update_fields=["active"])

    @classmethod
    def _apply_bonus_to_income(cls, base_income: float, bonus: Bonuses) -> float:
        """
        Применить бонус к доходу
        """
        bonus_data = bonus.bonus_data
        modified_income = base_income * bonus_data.value
        return round(modified_income, 3)

    @classmethod
    def _get_many_seconds_passed(
        cls, game_user: Union[Lumberjack_Game, GeoHunter], user_boosts: Sigma_Boosts
    ) -> int:
        time_passed = (
            datetime.now(pytz.timezone("Europe/Moscow")) - game_user.last_energy_update
        )
        required_delay: timedelta = timedelta(
            minutes=boosts_data.recovery_level.value_by_level(
                user_boosts.recovery_level
            )
        )
        return (required_delay - time_passed).total_seconds()

    @classmethod
    def _сheck_overdue_time(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        first_click: bool,
        total_seconds: int,
    ) -> Tuple[bool, int]:
        """
        Обрабатываем случай, когда время уже прошло
        """
        if (total_seconds + 30) < 0 and not first_click:
            total_seconds = 0
            super()._restore_energy(game_user)
            return True, total_seconds
        else:
            return False, total_seconds

    @classmethod
    def _build_time_str(cls, total_seconds: int) -> str:
        """
        Получаем строку времени
        """
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(int(remainder), 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @classmethod
    def _enough_energy_now(
        cls, game_user: Union[Lumberjack_Game, GeoHunter], energy_in_click: int
    ) -> int:
        """
        Проверяет энергию есть ли энергия в игре
        """
        if game_user.current_energy < energy_in_click:
            raise RaisesResponse(
                data={"error": "Not enough energy"}, status=status.HTTP_400_BAD_REQUEST
            )

    @classmethod
    def _reference_point_last_energy_update(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        game_user_two: Union[Lumberjack_Game, GeoHunter],
    ) -> int:
        """
        Обновляем точку отсчета при полной энергии
        """
        if game_user.current_energy == game_user.max_energy:
            game_user.last_energy_update = datetime.now()
            game_user_two.last_energy_update = datetime.now()
            game_user_two.save()


class GameView(GameMethods):
    @classmethod
    def game_state(
        cls, game_user: Union[Lumberjack_Game, GeoHunter], user_boosts: Sigma_Boosts
    ) -> Response:
        first_click = game_user.current_energy == game_user.max_energy

        total_seconds = super()._get_many_seconds_passed(game_user, user_boosts)
        force_update_energy, total_seconds = super()._сheck_overdue_time(
            game_user, first_click, total_seconds
        )
        time_str = super()._build_time_str(total_seconds)

        raise RaisesResponse(
            data={
                "force_update_energy": force_update_energy,
                "time_str": time_str,
                "first_click": first_click,
                "game_user": (
                    LumberjackGameSerializer(game_user).data
                    if isinstance(game_user, Lumberjack_Game)
                    else GeoHunterSerializer(game_user).data
                ),
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def apply_click_bonuses(cls, base_income: float) -> float:
        """
        Применяет все активные бонусы к доходу за клик
        """
        current_time = datetime.now(pytz.timezone("Europe/Moscow"))

        for bonus in super()._get_active_click_bonuses():
            # Проверяем срок действия
            if super()._is_bonus_valid(bonus, current_time):
                super()._deactivate_expired_bonus(bonus)
                continue

            return super()._apply_bonus_to_income(base_income, bonus)
        return base_income

    @classmethod
    def check_energy(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        game_user_two: Union[Lumberjack_Game, GeoHunter],
        energy_in_click: int,
    ) -> int:
        """
        Проверяет энергию
        """
        super()._enough_energy_now(game_user, energy_in_click)
        super()._reference_point_last_energy_update(game_user, game_user_two)

    @classmethod
    def restore_energy(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        game_user_two: Union[GeoHunter, Lumberjack_Game],
    ):
        """
        Полностью восстанавливает энергию игрока
        """
        super()._restore_energy(game_user)
        super()._restore_energy(game_user_two)

        raise RaisesResponse(
            data={
                "success": True,
                "current_energy": game_user.current_energy,
                "max_energy": game_user.max_energy,
                "last_updated": game_user.last_energy_update.isoformat(),
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def _update_grid(
        cls,
        game_user: Union[Lumberjack_Game, GeoHunter],
        grid: Optional[List[List[str]]],
    ):
        game_user.current_grid = grid
        game_user.save()

    @classmethod
    def _check_grid_format(cls, grid: Optional[List[List[str]]]):
        if (
            not isinstance(grid, list)
            or len(grid) != 4
            or any(len(row) != 5 for row in grid)
        ):
            raise RaisesResponse(
                data={"error": "Grid must be 4x5 matrix"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @classmethod
    def _process_lumberjack_click(
        cls,
        user: Users,
        game_user: Lumberjack_Game,
        game_user_two: GeoHunter,
        income_per_click: int,
        energy_in_click: int,
        row: int,
        col: int,
    ) -> None:
        """
        Обрабатывает клик в кликере
        """
        game_user.total_clicks += 1
        game_user.current_grid[row][col] = str(income_per_click)
        game_user.total_currency += income_per_click
        game_user.current_energy -= energy_in_click
        game_user.save()

        if game_user_two.current_energy > 0:
            game_user_two.current_energy -= energy_in_click
            game_user_two.save()

        user.starcoins += income_per_click
        user.save()

    @classmethod
    def _process_geohunter_click(
        cls,
        user: Users,
        game_user: Lumberjack_Game,
        game_user_two: GeoHunter,
        income_per_click: int,
        energy_in_click: int,
        user_choice: bool,
    ) -> None:
        """
        Обрабатывает клик в геохантере
        """
        game_user.current_energy -= energy_in_click

        if user_choice:
            game_user.total_true += 1
            game_user.total_currency += income_per_click

            user.starcoins += income_per_click
            user.save()
        else:
            game_user.total_false += 1

        game_user.save()

        if game_user_two.current_energy > 0:
            game_user_two.current_energy -= energy_in_click
            game_user_two.save()


class LumberjackGameViewMethods(GameView, AbstractLumberjackGame, AbstractGame):
    @classmethod
    def get(
        cls, pk: Optional[int] = None, user: Optional[Users] = None
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
    def retrieve(cls, game: Lumberjack_Game) -> RaisesResponse:
        raise RaisesResponse(
            LumberjackGameSerializer(game).data, status=status.HTTP_200_OK
        )

    @classmethod
    def active_games(cls, games: List[Lumberjack_Game]) -> RaisesResponse:
        raise RaisesResponse(
            LumberjackGameSerializer(games, many=True).data, status=status.HTTP_200_OK
        )

    @classmethod
    def game_state(
        cls, game_user: Lumberjack_Game, user_boosts: Sigma_Boosts
    ) -> RaisesResponse:
        super().game_state(game_user, user_boosts)

    @classmethod
    def update_grid(cls, game_user: Lumberjack_Game, grid: List[List[str]]) -> Response:
        """
        Обновляет игровое поле пользователя
        """
        super()._check_grid_format(grid)
        super()._update_grid(game_user, grid)

        raise RaisesResponse(
            data=LumberjackGameSerializer(game_user).data, status=status.HTTP_200_OK
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
        col: int,
    ) -> RaisesResponse:
        """
        Обрабатывает клик в игре с учетом всех бустов
        """
        super().check_energy(game_user, game_user_two, energy_in_click)

        income_per_click = super().apply_click_bonuses(
            boosts_data.income_level.value_by_level(boosts_user.income_level)
        )

        super()._process_lumberjack_click(
            user, game_user, game_user_two, income_per_click, energy_in_click, row, col
        )

        raise RaisesResponse(data=income_per_click, status=status.HTTP_200_OK)

    @classmethod
    def restore_energy(
        cls, game_user: Lumberjack_Game, game_user_two: GeoHunter
    ) -> RaisesResponse:
        """
        Восстанавливает энергию игрока
        """
        super().restore_energy(game_user, game_user_two)

    @classmethod
    def get_list_correct_clicks(cls) -> List[Lumberjack_Game]:
        return Lumberjack_Game.objects.filter(
            total_clicks__gte=0
        ).values(
            "user__user_id", "total_clicks"
        ).order_by('-total_clicks', '-updated_at')


class GeoHunterViewMethods(GameView, AbstractGame):
    @classmethod
    def get(cls, pk: Optional[int] = None, user: Optional[Users] = None) -> GeoHunter:
        """Получить геохантер"""
        try:
            if pk:
                return GeoHunter.objects.get(pk=pk)
            else:
                return GeoHunter.objects.get(user=user)
        except GeoHunter.DoesNotExist:
            return GeoHunter.objects.create(
                user=user, current_energy=100, max_energy=100
            )

    @classmethod
    def all(cls) -> List[GeoHunter]:
        """Получить геохантеры"""
        return GeoHunter.objects.all()

    @classmethod
    def retrieve(cls, game: GeoHunter) -> RaisesResponse:
        raise RaisesResponse(GeoHunterSerializer(game).data, status=status.HTTP_200_OK)

    @classmethod
    def active_games(cls, games: List[GeoHunter]) -> RaisesResponse:
        raise RaisesResponse(
            GeoHunterSerializer(games, many=True).data, status=status.HTTP_200_OK
        )

    @classmethod
    def game_state(
        cls, game_user: Sigma_Boosts, user_boosts: Lumberjack_Game
    ) -> RaisesResponse:
        super().game_state(game_user, user_boosts)

    @classmethod
    def process_click(
        cls,
        user: Users,
        game_user: Lumberjack_Game,
        game_user_two: GeoHunter,
        boosts_user: Sigma_Boosts,
        energy_in_click: int,
        user_choice: int,
    ) -> RaisesResponse:
        """
        Обрабатывает клик в игре с учетом всех бустов
        """
        super().check_energy(game_user, game_user_two, energy_in_click)

        income_per_click = super().apply_click_bonuses(
            boosts_data.income_level.value_by_level(boosts_user.income_level)
        )

        super()._process_geohunter_click(
            user,
            game_user,
            game_user_two,
            income_per_click,
            energy_in_click,
            user_choice,
        )

        raise RaisesResponse(
            GeoHunterSerializer(game_user).data, status=status.HTTP_200_OK
        )

    @classmethod
    def restore_energy(
        cls, game_user: GeoHunter, game_user_two: Lumberjack_Game
    ) -> RaisesResponse:
        """
        Восстанавливает энергию игрока
        """
        super().restore_energy(game_user, game_user_two)

    @classmethod
    def get_list_correct_answers(cls) -> List[Dict]:
        return GeoHunter.objects.filter(
            total_true__gte=0
        ).values(
            "total_true", "user__user_id"
        ).order_by('-total_true', '-updated_at')


# NOTE новая фича
class InteractiveGameMethods:
    @classmethod
    def get(cls, pk: Optional[int] = None) -> InteractiveGames:
        """Получить игру"""
        try:
            if pk:
                return InteractiveGames.objects.get(pk=pk)
            else:
                raise Exception("Game not found")
        except InteractiveGames.DoesNotExist:
            raise RaisesResponse(
                data={"error": "InteractiveGames not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @classmethod
    def active(cls, game: InteractiveGames) -> InteractiveGamesSerializer:
        if game.game_status in ["expired", "canceled", "ended"]:
            raise RaisesResponse(
                data={"error": "Game is not active"}, status=status.HTTP_400_BAD_REQUEST
            )
        return InteractiveGamesSerializer(game)

    @classmethod
    def create(cls, user: Users, data: dict) -> Response:
        data.update({"user": user})

        game = InteractiveGames.objects.create(**data)

        raise RaisesResponse(
            data=InteractiveGamesSerializer(game).data, status=status.HTTP_201_CREATED
        )

    @classmethod
    def delete(cls, game: InteractiveGames) -> Response:
        serializer_game = InteractiveGamesSerializer(game)
        game.delete()
        raise RaisesResponse(data=serializer_game.data, status=status.HTTP_200_OK)

    @classmethod
    def success_game(cls, game: InteractiveGames) -> Response:
        game.game_status = "ready"
        game.start_invite_at = datetime.now(pytz.utc)  # pytz.timezone('Europe/Moscow')
        game.save()

        GameData.objects.create(user=game.user, game=game, creator=True)

        serializer_game = InteractiveGamesSerializer(game)
        raise RaisesResponse(data=serializer_game.data, status=status.HTTP_200_OK)

    @classmethod
    def invite_game(cls, user: Users, game: InteractiveGames) -> Response:
        game_datas = GameData.objects.filter(game=game)
        logger.warning(game.max_players and game.max_players <= game_datas.count())
        if game.max_players and game.max_players < game_datas.count():
            raise RaisesResponse(
                data={"error": "Количество игроков превышает максимальное количество"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.warning(game.game_status)
        if game.game_status != "ready":
            raise RaisesResponse(
                data={"error": "Игра не готова"}, status=status.HTTP_400_BAD_REQUEST
            )

        level = user.get_current_rang().level
        logger.warning(
            (game.min_rang and game.min_rang > level)
            or (game.max_rang and level > game.max_rang)
        )
        if (game.min_rang and game.min_rang > level) or (
            game.max_rang and level > game.max_rang
        ):
            raise RaisesResponse(
                data={"error": "У вас недостаточно прав для начала игры"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.warning(
            (game.start_invite_at + timedelta(minutes=INTERACTIVE_INVITE_TIME))
            < datetime.now(pytz.timezone("Europe/Moscow"))
        )
        if (
            game.start_invite_at + timedelta(minutes=INTERACTIVE_INVITE_TIME)
        ) < datetime.now(pytz.timezone("Europe/Moscow")):
            raise RaisesResponse(
                data={"error": "Время приглашения истекло"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GameData.objects.create(user=user, game=game)

        serializer_game = InteractiveGamesSerializer(game)
        raise RaisesResponse(data=serializer_game.data, status=status.HTTP_200_OK)

    @classmethod
    def delete_pending(cls, game: InteractiveGames) -> Response:
        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]
        serializer_users = UserSerializer(users_in_game, many=True)
        serializer_game = InteractiveGamesSerializer(game)

        game.delete()

        raise RaisesResponse(
            data={"users": serializer_users.data, "game": serializer_game.data},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def start_game(cls, game: InteractiveGames) -> Response:
        if game.game_status == "active":
            raise RaisesResponse(
                data={"error": "Game already active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]

        if len(users_in_game) < 2 or len(users_in_game) < game.min_players:
            raise RaisesResponse(
                data={"error": "Not enough players in game"},
                status=status.HTTP_404_NOT_FOUND,
            )

        game.game_status = "active"
        game.start_game_at = datetime.now()  # pytz.timezone('Europe/Moscow')
        game.save()

        serializer_users = UserSerializer(users_in_game, many=True)
        serializer_game = InteractiveGamesSerializer(game)

        raise RaisesResponse(
            data={"users": serializer_users.data, "game": serializer_game.data},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def get_info(
        cls, game: InteractiveGames, serializer_game: InteractiveGamesSerializer
    ) -> Response:
        game_datas = GameData.objects.filter(game=game)
        users_in_game = [data.user for data in game_datas]

        serializer_users = UserSerializer(users_in_game, many=True)

        raise RaisesResponse(
            data={"users": serializer_users.data, "game": serializer_game.data},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def end_game(cls, game: InteractiveGames, winers: List[int]) -> Response:
        game_datas = GameData.objects.filter(game=game)

        if game.reward_type == "from_all_wins":
            reward = game.reward_starcoins / len(winers)
        else:
            reward = game.reward_starcoins

        # NOTE распределение награды между победителями
        for game_data in game_datas:
            if game_data.user.user_id in winers:
                game_data.result = "win"
                game_data.reward_starcoins = reward
                game.user.starcoins += reward
                game.user.save()
            else:
                game_data.result = "lose"

            game_data.completed = True
            game_data.save()

        game.game_status = "ended"
        game.ended_game_at = datetime.now(pytz.utc)
        game.save()

        serializer_game_data = GameDataSerializer(game_datas, many=True)
        serializer_game = InteractiveGamesSerializer(game)

        raise RaisesResponse(
            data={
                "game_datas": serializer_game_data.data,
                "game": serializer_game.data,
            },
            status=status.HTTP_200_OK,
        )
