"""
URL configuration for conf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from bot.views import *
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"family-ties", FamilyTiesViewSet, basename="family-ties")
router.register(r"purchases", PurchasesViewSet, basename="purchases")
router.register(r"pikmi-shop", PikmiShopViewSet, basename="pikmi-shop")
router.register(r"sigma-boosts", SigmaBoostsViewSet, basename="sigma-boosts")
router.register(r"lumberjack-games", LumberjackGameViewSet, basename="lumberjack-games")
router.register(r"geo-hunter", GeoHunterGameViewSet, basename="geo-hunter")
router.register(r"work-keys", WorkKeysViewSet, basename="work-keys")
router.register(r"bonuses", BonusesViewSet, basename="bonuses")
# router.register(r"use-bonuses", UseBonusesViewSet, basename="use-bonuses")
router.register(r"quests", QuestsViewSet, basename="quests")
router.register(r"use-quests", UseQuestsViewSet, basename="use-quests")
router.register(r"reward_data", RewardViewSet, basename="reward_data")
router.register(r"copy-base", CopyBaseViewSet, basename="copy-base")
router.register(r"rangs", RangsViewSet, basename="rangs")
router.register(
    r"quest-moderation-attempt",
    QuestModerationAttemptViewSet,
    basename="quest-moderation-attempt",
)
router.register(r"promocodes", PromocodesViewSet, basename="promocodes")
router.register(r"management-link", ManagementLinksViewSet, basename="management-link")
router.register(
    r"interactive-game", InteractiveGameViewSet, basename="interactive-game"
)
router.register(
    r"aggregation-daily-stats",
    AggregatorDailyStatsViewSet,
    basename="aggregation-daily-stats",
)
router.register(
    r"rating",
    RatingViewSet,
    basename="rating",
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
]
