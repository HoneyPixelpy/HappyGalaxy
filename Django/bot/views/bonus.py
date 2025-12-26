from datetime import datetime
from typing import List, Optional, Union

from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.response import Response

from ..models import (
    AddStarcoinsBonus,
    Bonuses,
    ClickScaleBonus,
    EnergyRenewalBonus,
    GeoHunter,
    Lumberjack_Game,
    UseBonuses,
    Users,
)
from ..serializers import (
    BonusesSerializer,
    LumberjackGameSerializer,
    UseBonusesSerializer,
)
from .error import RaisesResponse
from .game import UserGameMethods


class BonusesMethods:
    @classmethod
    def get(
        cls,
        pk: Optional[int] = None,
    ) -> Union[Bonuses, Response]:
        """Получить бонус"""
        try:
            if pk is not None:
                return Bonuses.objects.get(pk=pk)
        except Bonuses.DoesNotExist:
            raise RaisesResponse(
                data={"error": "Bonuses not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def all(cls) -> List[Bonuses]:
        """Получить все бонусы"""
        return Bonuses.objects.all()

    @classmethod
    def create_add_starcoins(cls, value: int, max_quantity: int) -> Bonuses:
        return AddStarcoinsBonus.objects.create(_value=value, max_quantity=max_quantity)

    @classmethod
    def create_click_scale(cls, value: int, duration_hours: int) -> Bonuses:
        return ClickScaleBonus.objects.create(
            _value=value, _duration_hours=duration_hours
        )

    @classmethod
    def create_energy_renewal(cls, duration_hours: int) -> Bonuses:
        return EnergyRenewalBonus.objects.create(_duration_hours=duration_hours)

    @classmethod
    def create(
        cls,
        bonus_obj: Union[ClickScaleBonus, AddStarcoinsBonus, EnergyRenewalBonus],
        type_bonus: str,
        expires_at: datetime,
    ) -> Bonuses:
        content_type = ContentType.objects.get_for_model(bonus_obj.__class__)
        bonus = Bonuses.objects.create(
            content_type=content_type,
            object_id=bonus_obj.id,
            type_bonus=type_bonus,
            expires_at=expires_at,
        )
        raise RaisesResponse(
            data=BonusesSerializer(bonus).data, status=status.HTTP_201_CREATED
        )


class UseBonusesMethods(UserGameMethods):
    @classmethod
    def get(cls, user: Users, bonus: Bonuses) -> Union[UseBonuses, Response]:
        try:
            return UseBonuses.objects.get(user=user, bonus=bonus)
        except Users.DoesNotExist:
            raise RaisesResponse(
                data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def create(cls, user: Users, bonus: Bonuses) -> Response:
        if UseBonuses.objects.filter(user=user, bonus=bonus).exists():
            raise RaisesResponse(
                data={"error": "This bonus is already assigned to the user"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        use_bonus = UseBonuses.objects.create(user=user, bonus=bonus)
        serializer = UseBonusesSerializer(use_bonus)
        raise RaisesResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    @classmethod
    def create_add_starcoins(
        cls, bonus: Bonuses, user: Users, now: datetime
    ) -> Union[UseBonuses, Response]:
        bonus_data = bonus.bonus_data

        if bonus_data.use_quantity >= bonus_data.max_quantity or bonus.expires_at < now:
            bonus.active = False
            bonus.save()
            raise RaisesResponse(data={"text": "not_active"}, status=status.HTTP_200_OK)

        # Проверяем не получал ли уже пользователь этот бонус
        if UseBonuses.objects.filter(user=user, bonus=bonus).exists():
            raise RaisesResponse(
                data={"text": "already_used"}, status=status.HTTP_200_OK
            )

        # Начисляем бонус
        bonus_data.use_quantity += 1
        user.starcoins += bonus_data.value

        bonus_data.save()
        user.save()
        UseBonuses.objects.create(user=user, bonus=bonus)

        raise RaisesResponse(
            data={"text": f"success_add_starcoins={bonus_data.value}"},
            status=status.HTTP_200_OK,
        )

    @classmethod
    def _check_expires_at(
        cls, bonus: Bonuses, now: datetime
    ) -> Union[UseBonuses, Response]:
        if bonus.expires_at < now:
            bonus.active = False
            bonus.save()
            raise RaisesResponse(data={"text": "not_active"}, status=status.HTTP_200_OK)

    @classmethod
    def activate_energy_renewal(
        cls,
        bonus: Bonuses,
        lumberjack: Lumberjack_Game,
        geohunter: GeoHunter,
        now: datetime,
    ) -> Union[UseBonuses, Response]:
        cls._check_expires_at(bonus, now)

        super()._restore_energy(lumberjack)
        super()._restore_energy(geohunter)

        raise RaisesResponse(
            data={"text": "success_energy_renewal"}, status=status.HTTP_200_OK
        )
