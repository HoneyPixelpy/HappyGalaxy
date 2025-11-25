# tests/test_models.py
# from django.test import TransactionTestCase
# from django.test import TestCase
import pytest
# from django.db import IntegrityError


class TestUserModel:
    """Тесты для модели User"""
    
    @pytest.mark.django_db # (transaction=True)
    def test_user_serializer(self, fake_user_data):
        """Проверяем базовое создание пользователя"""
        from bot.serializers import UserSerializer
        from bot.models import Users
        
        print(fake_user_data)

        user = UserSerializer(data=fake_user_data)
        
        assert user.is_valid

