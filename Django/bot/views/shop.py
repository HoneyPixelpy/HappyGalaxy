from datetime import datetime
from typing import List, Optional, Union

from rest_framework import status
from rest_framework.response import Response

from ..models import Pikmi_Shop, Purchases, Users
from ..serializers import PurchasesSerializer
from .error import RaisesResponse


class PurchasesMethods:
    @classmethod
    def get(
        cls,
        *,
        pk: Optional[int] = None,
        answer_message_id: Optional[int] = None
    ) -> Union[Purchases, Response]:
        """Получить покупку"""
        try:
            if pk is not None:
                return Purchases.objects.get(pk=pk)
            elif answer_message_id is not None:
                return Purchases.objects.get(
                    message_id=answer_message_id
                )
        except Purchases.DoesNotExist:
            raise RaisesResponse(
                data={"error": "Purchases not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def all(
        cls,
    ) -> List[Purchases]:
        return Purchases.objects.all()

    @classmethod
    def create(
        cls,
        user: Users,
        product: Pikmi_Shop,
        title: str,
        description: str,
        cost: int,
        delivery_data: Optional[str] = None
    ) -> Purchases:
        if user.purch_ban:
            raise RaisesResponse(
                data={"error": "You are banned from purchases"},
                status=status.HTTP_404_NOT_FOUND,
            )

        purchase = Purchases.objects.create(
            user=user,
            title=title,
            description=description,
            cost=cost,
            delivery_data=delivery_data
        )

        user.starcoins -= purchase.cost
        user.purchases += 1
        user.save()

        product.quantity -= 1
        product.save()

        raise RaisesResponse(
            data=PurchasesSerializer(purchase).data,
            status=status.HTTP_201_CREATED
        )
    
    @classmethod
    def edit_message_id(
        cls,
        purchase: Purchases,
        message_id: int
    ) -> None:
        purchase.message_id = message_id
        purchase.save()
        
        raise RaisesResponse(
            status=status.HTTP_200_OK
        )

    @classmethod
    def delete(
        cls,
        purchase: Purchases
    ) -> None:
        purchase.delete()

        raise RaisesResponse(
            status=status.HTTP_200_OK
        )

    @classmethod
    def success(
        cls,
        purchase: Purchases
    ) -> None:
        if not purchase.completed:
            purchase.completed = True
            purchase.completed_at = datetime.now()
            purchase.save()
        
        raise RaisesResponse(
            status=status.HTTP_200_OK
        )

    @classmethod
    def user_purchases(cls, user: Users, completed: str) -> List[Purchases]:
        if completed == "False":
            purchases = Purchases.objects.filter(user=user, completed=False)
        else:
            purchases = Purchases.objects.filter(user=user)
        serializer = PurchasesSerializer(purchases, many=True)
        raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)

    @classmethod
    def confirm_purchase(cls, purchase: Purchases) -> Purchases:
        purchase.completed = True
        purchase.completed_at = datetime.now()
        purchase.save()

        raise RaisesResponse(
            data=PurchasesSerializer(purchase).data, status=status.HTTP_200_OK
        )


class Pikmi_ShopMethods:
    @classmethod
    def get(
        cls,
        pk: Optional[int] = None,
    ) -> Union[Pikmi_Shop, Response]:
        """Получить товар"""
        try:
            if pk is not None:
                return Pikmi_Shop.objects.get(pk=pk)
        except Pikmi_Shop.DoesNotExist:
            raise RaisesResponse(
                data={"error": "Pikmi_Shop not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def all(
        cls,
    ) -> List[Pikmi_Shop]:
        return Pikmi_Shop.objects.all()
