import abc
from datetime import datetime

import pytz
from rest_framework import status
from rest_framework.response import Response

from ..models import (
    ManagementLinks,
    Promocodes,
    UseManagementLinks,
    UsePromocodes,
    Users,
)
from ..serializers import StarcoinsPromoSerializer
from .error import RaisesResponse


class CodesAbstract:
    @abc.abstractmethod
    def get(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def create(self, *args, **kwargs):
        pass


class PromocodesMethods(CodesAbstract):
    @classmethod
    def get(cls, code: str) -> Promocodes:
        try:
            return Promocodes.objects.get(code=code)
        except Promocodes.DoesNotExist:
            raise RaisesResponse(data={"error": "undefined"}, status=status.HTTP_200_OK)

    @classmethod
    def create(cls, user: Users, promocode: Promocodes) -> Response:
        if not promocode.active:
            raise RaisesResponse(data={"error": "active"}, status=status.HTTP_200_OK)

        if promocode.role and promocode.role != user._role:
            raise RaisesResponse(data={"error": "role"}, status=status.HTTP_200_OK)

        if UsePromocodes.objects.filter(user=user, promocode=promocode).first():
            raise RaisesResponse(
                data={"error": "use_promocodes"}, status=status.HTTP_200_OK
            )

        if promocode.used_quantity >= promocode.all_quantity:
            raise RaisesResponse(
                data={"error": "all_quantity"}, status=status.HTTP_200_OK
            )

        if promocode.expires_at and promocode.expires_at < datetime.now(
            pytz.timezone("Europe/Moscow")
        ):
            raise RaisesResponse(
                data={"error": "expires_at"}, status=status.HTTP_200_OK
            )

        if promocode.type_promo == "starcoins":
            promocode_obj = promocode.promo_data
            user.starcoins += promocode_obj.reward_starcoins
            user.save()
            serializer = StarcoinsPromoSerializer(promocode_obj)
            _type = "starcoins"
        else:
            raise RaisesResponse(
                data={"error": "Type Promo not found"}, status=status.HTTP_404_NOT_FOUND
            )

        promocode.used_quantity += 1
        promocode.save()

        UsePromocodes.objects.create(user=user, promocode=promocode)

        raise RaisesResponse(
            data={"data": serializer.data, "type": _type}, status=status.HTTP_200_OK
        )


class ManagementLinksMethods(CodesAbstract):
    @classmethod
    def get(cls, code: str) -> Promocodes:
        try:
            return ManagementLinks.objects.get(code=code)
        except ManagementLinks.DoesNotExist:
            raise RaisesResponse(
                data={"error": "ManagementLinks not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @classmethod
    def create(cls, user: Users, management_link: ManagementLinks) -> Response:
        if UseManagementLinks.objects.filter(
            user=user, management_link=management_link
        ).first():
            raise RaisesResponse(
                data={"error": "use_promocodes"}, status=status.HTTP_200_OK
            )

        UseManagementLinks.objects.create(user=user, management_link=management_link)

        raise RaisesResponse(data=True, status=status.HTTP_200_OK)


class CodesMethods(CodesAbstract):

    def __init__(self, key: str):
        if key == "promo":
            self.base = PromocodesMethods
        elif key == "links":
            self.base = ManagementLinksMethods
        else:
            raise ValueError("Unknown key")

    def get(self, *args, **kwargs) -> Response:
        return self.base.get(*args, **kwargs)

    def create(self, *args, **kwargs) -> Response:
        return self.base.create(*args, **kwargs)
