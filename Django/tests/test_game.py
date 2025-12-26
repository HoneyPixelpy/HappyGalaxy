# tests/test_game_methods.py
import os
import sys
from datetime import datetime, timedelta
from typing import Callable, Protocol, TypeAlias, TypedDict, Unpack
from unittest.mock import MagicMock, Mock, create_autospec, patch, seal

import pytest
import pytz
from bot.models import Bonuses, GeoHunter, Lumberjack_Game, Sigma_Boosts, Users

# Assuming these imports exist in your project
from bot.views.game import (
    GameMethods,
    GameView,
    GeoHunterViewMethods,
    LumberjackGameViewMethods,
    SigmaBoostsMethods,
    SigmaBoostsViewMethods,
    UserGameMethods,
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from django.utils import timezone
from loguru import logger
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
from typing_extensions import final
