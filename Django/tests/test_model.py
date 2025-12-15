# tests/test_models.py
# from django.test import TransactionTestCase
# from django.test import TestCase
from datetime import datetime, timezone as dt_tz
import pytest
# from django.db import IntegrityError
from zoneinfo import ZoneInfo
from bot.models import roles, Users
from bot.serializers import UserSerializer


class TestUserModel:
    """Тесты для модели User"""
    
    @pytest.mark.django_db
    def test_user_serializer(self, fake_user_data):
        """Проверяем сериализатор"""

        user = UserSerializer(data=fake_user_data)
        
        assert user.is_valid(), user.errors

    @pytest.mark.django_db
    def test_user_serializer_required_field(self, fake_user_data):
        """Проверяем сериализатор на обязательные поля"""

        fake_user_data.pop("user_id", None)

        serializer = UserSerializer(data=fake_user_data)

        assert not serializer.is_valid()
        assert "user_id" in serializer.errors

    @pytest.mark.django_db
    def test_user_create_minimal(self, fake_user_data):
        """Создание пользователя с минимально обязательными полями."""
        user = Users.objects.create(
            user_id=fake_user_data["user_id"]
        )

        assert user.pk is not None
        assert user.user_id == fake_user_data["user_id"]
        assert user.authorised is False
        assert user.ban is False
        assert user._starcoins == 0.0

    @pytest.mark.django_db
    def test_authorised_at_timezone_conversion(self):
        
        user = Users.objects.create(user_id=1)

        moscow = ZoneInfo("Europe/Moscow")
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        aware_moscow = naive_dt.replace(tzinfo=moscow)

        user.authorised_at = aware_moscow
        user.save()

        # В БД должно лежать в UTC
        assert user._authorised_at.tzinfo == dt_tz.utc

        # Геттер возвращает в МСК
        value = user.authorised_at
        assert value.tzinfo == moscow
        assert value.hour == 12  # локальное время такое же, как ставили

    @pytest.mark.django_db
    @pytest.mark.parametrize("code, expected_name", [
        ("child", "⚡️ Главный герой"),
        ("parent", "❤️ Родитель"),
        ("worker", "🎖 Современник Галактики"),
        ("manager", "🛠 Работник"),
        (None, "Незнакомец"),
    ])
    def test_role_name(self, code, expected_name):
        user = Users.objects.create(user_id=1, _role=code)
        assert user.role_name == expected_name

    @pytest.mark.django_db
    def test_role_property_formatting_child(self):
        user = Users.objects.create(user_id=1, _role="child")
        expected = roles.get("child")
        assert user.role == f"<u>{expected}</u>"

    @pytest.mark.django_db
    def test_role_setter(self):
        user = Users.objects.create(user_id=1)
        user.role = "parent"
        assert user._role == "parent"

    @pytest.mark.django_db
    def test_nickname_default(self):
        user = Users.objects.create(user_id=1)
        assert user.nickname == "Без никнейма"

    @pytest.mark.django_db
    def test_nickname_setter(self):
        user = Users.objects.create(user_id=1)
        user.nickname = "testnick"
        assert user.nickname == "testnick"
        assert user._nickname == "testnick"

    @pytest.mark.django_db
    def test_starcoins_rounding_int(self):
        user = Users.objects.create(user_id=1, _starcoins=10.0)
        assert user.starcoins == 10  # int, когда без дробной части

    @pytest.mark.django_db
    def test_starcoins_rounding_fraction(self):
        user = Users.objects.create(user_id=1, _starcoins=10.123456)
        assert user.starcoins == 10.1235  # округляется до 4 знаков

    @pytest.mark.django_db
    def test_all_starcoins_added(self):
        user = Users.objects.create(user_id=1)
        
        assert user.starcoins == 0
        
        user.starcoins += 4
        user.save()
        
        assert user.all_starcoins == 4






