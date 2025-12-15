import os
import sys
import django
from mimesis import Field, Locale, Schema
import pytest
from unittest.mock import Mock, patch, MagicMock

# from bot.models import Users, Sigma_Boosts, Lumberjack_Game, GeoHunter, Bonuses
# from bot.views.game import (
#     UserGameMethods,
#     SigmaBoostsMethods,
#     SigmaBoostsViewMethods,
#     GameMethods,
#     GameView,
#     LumberjackGameViewMethods,
#     GeoHunterViewMethods
# )


"""
Фикстуры
Скоупы
Марки
Параметризация
Плагины
Хуки
манки патч
моки
create_autospec
!seal
!spy
!stub

pytest_plugins = [
    'plugins.django_settings'
]

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')
django.setup()

"""


@pytest.fixture
def fake_user_data():
    mf = Field(Locale.RU)
    schema = Schema(schema=lambda: {
        'user_id': mf('numeric.integer_number', start=1, end=100000),
        'vk_id': mf('numeric.integer_number', start=1, end=100000),
        'tg_first_name': mf('person.first_name'),
        'tg_last_name': mf('person.last_name'),
        'tg_username': mf('person.username'),
        'referral_user_id': mf('numeric.integer_number', start=1, end=100000),
        'authorised': mf('boolean'),
        'authorised_at': mf('datetime'),
        'role': mf('choice', items=['user', 'admin', 'moderator']),
        'gender': mf('person.gender'),
        'age': mf('datetime'),
        'name': mf('person.first_name'),
        'supername': mf('person.last_name'),
        'patronymic': mf('person.surname'),
        'nickname': mf('person.username'),
        'phone': mf('person.telephone'),
        'email': mf('person.email'),
        'active': mf('boolean'),
        'ban': mf('boolean'),
        'purch_ban': mf('boolean'),
        'starcoins': mf('numeric.float_number', start=0, end=1000),
        'all_starcoins': mf('numeric.float_number', start=0, end=5000),
        'purchases': mf('numeric.integer_number', start=0, end=100)
    })
    base_data = schema.create()
    return {**base_data[0]}



 