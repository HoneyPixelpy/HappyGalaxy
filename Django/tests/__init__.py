# # tests/__init__.py
# # Package initialization for tests

# # tests/conftest.py
# import pytest
# from unittest.mock import Mock, MagicMock
# from django.contrib.auth import get_user_model

# User = get_user_model()

# @pytest.fixture
# def mock_user():
#     """Fixture для создания mock пользователя"""
#     user = Mock()
#     user.id = 1
#     user.username = 'testuser'
#     user.starcoins = 1000
#     user.save = Mock()
#     return user

# @pytest.fixture
# def mock_lumberjack_game(mock_user):
#     """Fixture для создания mock игры lumberjack"""
#     game = Mock()
#     game.user = mock_user
#     game.current_energy = 100
#     game.max_energy = 100
#     game.total_clicks = 0
#     game.total_currency = 0
#     game.current_grid = [[''] * 5 for _ in range(4)]
#     game.last_energy_update = Mock()
#     game.save = Mock()
#     return game

# @pytest.fixture
# def mock_geo_hunter_game(mock_user):
#     """Fixture для создания mock игры geo hunter"""
#     game = Mock()
#     game.user = mock_user
#     game.current_energy = 100
#     game.max_energy = 100
#     game.total_true = 0
#     game.total_false = 0
#     game.total_currency = 0
#     game.last_energy_update = Mock()
#     game.save = Mock()
#     return game

# @pytest.fixture
# def mock_user_boosts(mock_user):
#     """Fixture для создания mock бустов пользователя"""
#     boosts = Mock()
#     boosts.user = mock_user
#     boosts.income_level = 3
#     boosts.passive_income_level = 2
#     boosts.energy_capacity_level = 1
#     boosts.recovery_level = 1
#     boosts.last_passive_claim = Mock()
#     boosts.save = Mock()
#     return boosts

# @pytest.fixture
# def mock_boosts_data():
#     """Fixture для создания mock данных бустов"""
#     boosts_data = Mock()
    
#     # Mock income level
#     income_level = Mock()
#     income_level.value_by_level.return_value = 50
#     income_level.max_level.return_value = 10
#     income_level.emoji.return_value = "💰"
#     income_level.price.return_value = 100
#     boosts_data.income_level = income_level
    
#     # Mock passive income level
#     passive_income_level = Mock()
#     passive_income_level.value_by_level.return_value = 25
#     passive_income_level.max_level.return_value = 5
#     boosts_data.passive_income_level = passive_income_level
    
#     # Mock energy capacity level
#     energy_capacity_level = Mock()
#     energy_capacity_level.value_by_level.return_value = 150
#     energy_capacity_level.max_level.return_value = 8
#     boosts_data.energy_capacity_level = energy_capacity_level
    
#     # Mock recovery level
#     recovery_level = Mock()
#     recovery_level.value_by_level.return_value = 60  # 60 minutes
#     boosts_data.recovery_level = recovery_level
    
#     return boosts_data
