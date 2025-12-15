# tests/test_game_methods.py
import os
import sys
from datetime import datetime, timedelta
from typing import Protocol, TypedDict, Unpack, TypeAlias, Callable
from typing_extensions import final
from unittest.mock import Mock, create_autospec, patch, MagicMock, seal

from django.utils import timezone
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.db import models
from loguru import logger
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
import pytest
import pytz


# Assuming these imports exist in your project
from bot.views.game import (
    UserGameMethods,
    SigmaBoostsMethods,
    SigmaBoostsViewMethods,
    GameMethods,
    GameView,
    LumberjackGameViewMethods,
    GeoHunterViewMethods
)
from bot.models import Users, Sigma_Boosts, Lumberjack_Game, GeoHunter, Bonuses



