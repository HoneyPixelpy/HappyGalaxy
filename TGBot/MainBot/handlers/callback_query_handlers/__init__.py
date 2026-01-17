__all__ = ("callback_routers",)

from .background import background_router
from .bonus import bonus_router
from .boosts import boosts_router
from .game import game_router
from .main import main_router
from .product import product_router
from .profile import profile_router
from .quest import quest_router
from .rangs import rangs_router
from .rating import rating_router
from .register import register_router

callback_routers = [
    main_router,
    register_router,
    game_router,
    boosts_router,
    product_router,
    quest_router,
    profile_router,
    rangs_router,
    rating_router,
    bonus_router,
    background_router,
]
