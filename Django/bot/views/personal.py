from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from loguru import logger
from rest_framework import status
from rest_framework.response import Response

from ..models import (
    Family_Ties,
    Lumberjack_Game,
    Quests,
    Rangs,
    ReferralConnections,
    Sigma_Boosts,
    SubscribeQuest,
    UseQuests,
    Users,
    Work_Keys,
)
from ..schemas import boosts_data, reward_data
from ..serializers import FamilyTiesSerializer, RangsSerializer, UserSerializer
from .error import RaisesResponse


class UserMethods:
    @classmethod
    def get(
        cls,
        pk: Optional[int] = None,
        user_id: Optional[int] = None,
        phone: Optional[str] = None,
        nickname: Optional[str] = None,
    ) -> Union[Users, Response]:
        """Получить пользователя"""
        try:
            if pk is not None:
                return Users.objects.get(pk=pk)
            elif user_id is not None:
                return Users.objects.get(user_id=user_id)
            elif phone is not None:
                return Users.objects.get(phone=phone)
            elif nickname is not None:
                return Users.objects.get(_nickname=nickname)
        except Users.DoesNotExist:
            raise RaisesResponse(
                data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def filter(
        cls,
        pk: Optional[int] = None,
        user_id: Optional[int] = None,
        phone: Optional[str] = None,
        nickname: Optional[str] = None,
    ) -> Union[Users, Response]:
        """Получить пользователя"""
        if pk is not None:
            return Users.objects.filter(pk=pk).first()
        elif user_id is not None:
            return Users.objects.filter(user_id=user_id).first()
        elif phone is not None:
            return Users.objects.filter(phone=phone).first()
        elif nickname is not None:
            return Users.objects.filter(_nickname=nickname).first()
        else:
            raise RaisesResponse(
                data={"error": "No parameters provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @classmethod
    def all(cls) -> List[Users]:
        """Получить пользователей"""
        return Users.objects.all()

    @classmethod
    def create(cls, validated_data: Dict) -> Response:
        """Создать пользователя"""
        user = Users.objects.create(**validated_data)
        Sigma_Boosts.objects.create(user=user)
        Lumberjack_Game.objects.create(user=user)
        raise RaisesResponse(
            data=UserSerializer(user).data, status=status.HTTP_201_CREATED
        )

    @classmethod
    def banned(cls) -> Response:
        """Получить забаненных пользователей"""
        banned_ids = list(
            Users.objects.filter(ban=True).values_list("user_id", flat=True)
        )  # .all()
        raise RaisesResponse(data=banned_ids, status=status.HTTP_200_OK)

    @classmethod
    def referral_count(cls, pk: int) -> Response:
        """Получить кол-во рефералов"""
        count = Users.objects.filter(referral_user_id=pk, authorised=True).count()
        raise RaisesResponse(data=count, status=status.HTTP_200_OK)

    @classmethod
    def complete_registration(
        cls, user: Users, state_data: Dict, rollback: Optional[bool]
    ) -> Response:
        """Завершить регистрацию пользователя"""
        if state_data["role"] in ["worker", "manager"] and not rollback:
            game_user = Lumberjack_Game.objects.filter(user=user).first()
            if game_user and not game_user.max_energy:
                game_user.max_energy = boosts_data.energy_capacity_level.value_by_level(
                    0
                )
                game_user.current_energy = (
                    boosts_data.energy_capacity_level.value_by_level(0)
                )
                game_user.save()

        # Обновление данных пользователя
        user.role = state_data["role"]
        user.gender = state_data["gender"]
        user.age = datetime.fromisoformat(state_data["age"])  # datetime
        user.name = state_data["name"]
        user.supername = state_data["supername"]
        user.nickname = state_data["nickname"]
        user.phone = state_data["phone"]
        user.authorised = (
            True
            if state_data.get("authorised") is None
            else state_data.get("authorised")
        )
        user.authorised_at = (
            timezone.now()
            if not state_data.get("authorised_at")
            else state_data.get("authorised_at")
        )

        user.save()

        raise RaisesResponse(data=UserSerializer(user).data, status=status.HTTP_200_OK)

    @classmethod
    def update_telegram_username(cls, user: Users, username: str) -> Response:
        """Обновить Telegram username пользователя"""
        user.tg_username = username
        user.save()
        raise RaisesResponse(
            data={
                "success": True,
                "user_id": user.id,
                "new_username": user.tg_username,
            },
            status=status.HTTP_200_OK,
        )

    @classmethod
    def update_balance(cls, user: Users, new_balance: Any) -> Response:
        """Обновить баланс пользователя"""
        try:
            logger.debug(type(new_balance))
            user.starcoins = float(new_balance)
            user.save()

            raise RaisesResponse(data=user.starcoins, status=status.HTTP_200_OK)
        except ValueError:
            raise RaisesResponse(
                data={"error": "new_balance must be a valid number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @classmethod
    def update_ban(cls, user: Users, ban: bool) -> Response:
        """Баним или разбаним пользователя"""
        try:
            user.ban = ban
            user.save()

            raise RaisesResponse(data=True, status=status.HTTP_200_OK)
        except ValueError:
            raise RaisesResponse(
                data={"error": "new_balance must be a valid number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @classmethod
    def check_vk_id(cls, vk_id: int) -> None:
        """Проверка VK ID"""
        try:
            Users.objects.get(vk_id=vk_id)
            raise RaisesResponse(data=False, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            return

    @classmethod
    def update_vk_id(cls, user: Users, vk_id: int) -> Response:
        """Обновить VK ID пользователя"""
        user.vk_id = vk_id
        user.save()

        raise RaisesResponse(data=True, status=status.HTTP_200_OK)

    @classmethod
    def get_all_vk_users(cls) -> Response:
        users_with_vk = Users.objects.exclude(vk_id__isnull=True)
        serializer = UserSerializer(
            users_with_vk, many=True
        )  # Обратите внимание на many=True
        raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)

    @classmethod
    def back_vk_id(cls, user: Users, chat_id_name: Any) -> Response:
        # Получаем ContentType для SubscribeQuest
        content_type = ContentType.objects.get_for_model(SubscribeQuest)

        # Находим ID всех SubscribeQuest с нужным chat_id_name
        subscribe_quest_ids = SubscribeQuest.objects.filter(
            chat_id_name=chat_id_name
        ).values_list("id", flat=True)

        if not subscribe_quest_ids:
            raise RaisesResponse(
                data={"error": "No subscribe quest found with this chat_id_name"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Находим квест в Quests
        quest = Quests.objects.filter(
            content_type=content_type, object_id__in=subscribe_quest_ids
        ).first()

        use_quest = UseQuests.objects.filter(user=user, quest=quest).first()

        user.vk_id = None
        user.all_starcoins -= quest.quest_data.reward_starcoins
        user.starcoins -= quest.quest_data.reward_starcoins
        user.save()

        use_quest.delete()

        logger.info(f"Сняли за отпуску ВК {quest.quest_data.reward_starcoins} у {user}")

        raise RaisesResponse(data=True, status=status.HTTP_200_OK)

    @classmethod
    def unregistered_users(cls) -> Response:
        # Только дата (без времени) - вчера и ранее
        today = timezone.now().date()

        unregistered_ids = list(
            Users.objects.filter(
                authorised=False,
                created_at__date__lt=today,  # Созданы до сегодняшнего дня
            ).values_list("user_id", flat=True)
        )

        if unregistered_ids:
            raise RaisesResponse(data=unregistered_ids, status=status.HTTP_200_OK)
        else:
            raise RaisesResponse(data=False, status=status.HTTP_404_NOT_FOUND)

    @classmethod
    def active_users(cls, min_rang: int, max_rang: int) -> Response:
        queryset = Users.objects.all().filter(active=True)
        for user in queryset:
            level = user.get_current_rang().level
            logger.debug(
                f"Пользователь {user} активен {level} -> {min_rang <= level <= max_rang}"
            )

        serializer = UserSerializer(
            [
                user
                for user in queryset
                if min_rang <= user.get_current_rang().level <= max_rang
            ],
            many=True,
        )
        raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)

    @classmethod
    def delete_purch(cls, user: Users, cost: float) -> None:
        user.purchases -= 1
        user._starcoins += cost
        user.save()


class ReferralConnectionsMethods:
    @classmethod
    def process_referral(cls, user: Users) -> Response:
        """
        Process referral rewards for both referrer and referee
        """
        new_ref_connection = False

        referer_user = UserMethods.filter(user_id=user.referral_user_id)
        if not referer_user:
            logger.error(f"{user.referral_user_id}")
            user.referral_user_id = None
            user.save()
            raise RaisesResponse(
                data={"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        referral_connection = ReferralConnections.objects.filter(
            Q(referer=referer_user, referal=user)
            | Q(referer=user, referal=referer_user)
        )

        if not referral_connection:
            ReferralConnections.objects.create(
                referer=referer_user,
                referal=user,
                referer_starcoins=reward_data.starcoins_for_referer,
                referal_starcoins=reward_data.starcoins_for_referal,
            )

            # Update balances
            referer_user.starcoins += reward_data.starcoins_for_referer
            user.starcoins += reward_data.starcoins_for_referal

            # Save changes
            referer_user.save()
            user.save()
            new_ref_connection = True

        raise RaisesResponse(
            data={
                "user_id": referer_user.user_id,
                "new_ref_connection": new_ref_connection,
            },
            status=status.HTTP_200_OK,
        )


class FamilyTiesMethods:
    @classmethod
    def _tie_exists(cls, user1: Users, user2: Users) -> bool:
        """Проверяет существование связи между пользователями"""
        return Family_Ties.objects.filter(
            Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1)
        ).exists()

    @classmethod
    def _get_direct_relatives(cls, user: Users) -> set[Users]:
        """Возвращает список непосредственных родственников (1 уровень)"""
        relatives = set()
        # Где пользователь инициатор
        for tie in Family_Ties.objects.filter(from_user=user):
            relatives.add(tie.to_user)
        # Где пользователь цель
        for tie in Family_Ties.objects.filter(to_user=user):
            relatives.add(tie.from_user)
        return relatives

    @classmethod
    def _create_family_tie(cls, from_user: Users, to_user: Users) -> Family_Ties:
        if from_user._role == "parent" and to_user._role == "child":
            parent_game = Lumberjack_Game.objects.filter(user=from_user).first()
            child_game = Lumberjack_Game.objects.filter(user=to_user).first()
        elif to_user._role == "parent" and from_user._role == "child":
            parent_game = Lumberjack_Game.objects.filter(user=to_user).first()
            child_game = Lumberjack_Game.objects.filter(user=from_user).first()
        else:
            parent_game = None
            child_game = None

        for game in [parent_game, child_game]:
            if game and not game.max_energy:
                game.max_energy = boosts_data.energy_capacity_level.value_by_level(0)
                game.current_energy = boosts_data.energy_capacity_level.value_by_level(
                    0
                )
                game.save()

        return Family_Ties.objects.create(from_user=from_user, to_user=to_user)

    @classmethod
    def create(cls, from_user: Users, to_user: Users) -> Response:
        # Проверка на существующую связь
        if cls._tie_exists(from_user, to_user):
            raise RaisesResponse(
                data={"detail": "Tie already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Связываем всех родственников from_user с to_user
        from_user_ties = cls._get_direct_relatives(from_user)
        if from_user_ties:
            for relative in from_user_ties:
                if not cls._tie_exists(relative, to_user):
                    cls._create_family_tie(from_user=relative, to_user=to_user)
        else:
            from_user.starcoins += reward_data.starcoins_parent_bonus
            from_user.save()

        # Связываем всех родственников to_user с from_user
        to_user_ties = cls._get_direct_relatives(to_user)
        if to_user_ties:
            for relative in to_user_ties:
                if not cls._tie_exists(from_user, relative):
                    cls._create_family_tie(from_user=from_user, to_user=relative)
        else:
            to_user.starcoins += reward_data.starcoins_parent_bonus
            to_user.save()

        tie = cls._create_family_tie(from_user=from_user, to_user=to_user)

        serializer = FamilyTiesSerializer(tie)
        raise RaisesResponse(data=serializer.data, status=status.HTTP_201_CREATED)

    @classmethod
    def get_family(cls, user: Users) -> Response:
        ties = Family_Ties.objects.filter(Q(from_user=user) | Q(to_user=user))
        serializer = FamilyTiesSerializer(ties, many=True)
        raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)

    @classmethod
    def get_target_ties(cls, user: Users, parent: Users) -> Response:
        tie = Family_Ties.objects.filter(
            Q(from_user=parent, to_user=user) | Q(to_user=parent, from_user=user)
        ).first()
        if tie:
            serializer = FamilyTiesSerializer(tie)
            raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)
        raise RaisesResponse(
            data={"detail": "No ties found"}, status=status.HTTP_404_NOT_FOUND
        )


class WorkKeysMethods:
    @classmethod
    def get(cls, pk: int, key: str) -> Work_Keys:
        try:
            if pk is not None:
                return Work_Keys.objects.get(pk=pk)
            if key is not None:
                return Work_Keys.objects.get(key=key)
        except Work_Keys.DoesNotExist:
            raise RaisesResponse(
                data={"error": "Work key not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @classmethod
    def all(cls) -> Work_Keys:
        return Work_Keys.objects.all()

    @classmethod
    def create(cls) -> Work_Keys:
        return Work_Keys.objects.create()

    @classmethod
    def register_with_key(cls, work_key: Work_Keys, user: Users) -> Response:
        if work_key.from_user:
            raise RaisesResponse(
                data={"error": "Work key already used"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Associate work key
        work_key.from_user = user
        work_key.save()

        raise RaisesResponse(data=True, status=status.HTTP_200_OK)


class RangsMethods:
    @classmethod
    def role(cls, role: str) -> Response:
        rangs = (
            Rangs.objects.filter(Q(_role=role) | Q(_role__isnull=True))
            .order_by("all_starcoins")
            .all()
        )
        serializer = RangsSerializer(rangs, many=True)
        raise RaisesResponse(data=serializer.data, status=status.HTTP_200_OK)
