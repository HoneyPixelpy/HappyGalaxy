from datetime import datetime, timedelta
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union

from aiogram import types

from .api_client import (
    BonusesRequests,
    CopyBaseRequests,
    DataRequests,
    Family_TiesRequests,
    GeoHunter_GameRequests,
    InteractiveGameRequests,
    Lumberjack_GameRequests,
    ManagementLinksRequests,
    Pikmi_ShopRequests,
    PromocodesRequests,
    PurchasesRequests,
    QuestsRequests,
    RangsRequests,
    RatingRequests,
    Sigma_BoostsRequests,
    UseQuestsRequests,
    UsersRequests,
    Work_KeysRequests,
)
from .models import (
    Bonuses,
    Family_Ties,
    GeoHunter,
    IdeaQuests,
    InteractiveGameAllInfo,
    InteractiveGameBase,
    InteractiveGameInfo,
    Lumberjack_Game,
    Pikmi_Shop,
    Purchases,
    Quests,
    Rangs,
    RewardData,
    Sigma_Boosts,
    StarcoinsPromo,
    SubscribeQuest,
    # UseBonuses,
    Users,
    Work_Keys,
)


class IdempotencyKeyMethods:
    @classmethod
    async def IKgenerate(
        cls,
        user_id: int,
        message: types.Message
    ) -> str:
        created = message.date.timestamp()
        
        if message.edit_date is not None:
            data_str = f"{message.edit_date}:{created}:{user_id}"
        else:
            # Если edit_date нет, используем 0 как placeholder
            data_str = f"0:{created}:{user_id}"
        
        # Создаем MD5 хэш (16 байт) и берем первые 12 символов
        hash_obj = hashlib.md5(data_str.encode())
        _hash = hash_obj.hexdigest()
        
        return _hash


class DataMethods:

    def __init__(self):
        self.api = DataRequests()

    async def reward(self) -> Optional[RewardData]:
        data = await self.api.get_reward_data()
        reward = RewardData(**data) if data else None
        return reward


class UserMethods:

    def __init__(self):
        self.api = UsersRequests()

    async def get_by_user_id(self, user_id: int) -> Optional[Users]:
        data = await self.api.get_by_user_id(user_id)
        return Users(**data) if data else None

    async def create(
        self, user_data: types.User, referral_user_id: Optional[int], idempotency_key: str
    ) -> Optional[Users]:
        data = await self.api.create_user(
            user_data={
                "user_id": user_data.id,
                "tg_first_name": user_data.first_name,
                "tg_last_name": user_data.last_name,
                "tg_username": user_data.username,
                "referral_user_id": referral_user_id,
            },
            idempotency_key=idempotency_key
        )
        return Users(**data) if data else None

    async def get_all_users(self, **kwargs) -> List[Users]:
        datas = await self.api.get_all_users(**kwargs)
        return [Users(**data) for data in datas]

    async def get_banned_users(self) -> List[int]:
        datas = await self.api.get_banned_users()
        return [Users(**data) for data in datas]

    async def get_referral_count(self, user_id: int) -> int:
        return await self.api.get_referral_count(user_id)

    async def check_phone(self, phone: str) -> Optional[Users]:
        data = await self.api.check_phone(phone)
        return Users(**data) if data else None

    async def check_nickname(self, nickname: str) -> Optional[Users]:
        data = await self.api.check_nickname(nickname)
        return Users(**data) if data else None

    async def complete_registration(
        self, user: Users, state_data: Dict, rollback: Optional[bool] = None
    ) -> Users:
        if "user" in state_data:
            del state_data["user"]
        if "age" in state_data and isinstance(state_data["age"], datetime):
            state_data["age"] = state_data["age"].isoformat()
        data = await self.api.complete_registration(
            user_id=user.id, user_data={"state_data": state_data, "rollback": rollback}
        )
        return Users(**data) if data else None

    async def update_username(self, user: Users, username: str) -> None:
        await self.api.update_username(
            user_data={"user_id": user.id, "username": username}
        )

    async def update_balance(self, user_id: int, new_balance: int) -> int:
        return await self.api.update_balance(
            user_data={"user_id": user_id, "new_balance": new_balance}
        )

    async def update_ban(self, user_id: int, ban: bool) -> bool:
        return await self.api.update_ban(user_data={"user_id": user_id, "ban": ban})

    async def process_referral(self, user_id: int) -> Optional[dict]:
        return await self.api.process_referral(user_data={"user_id": user_id})

    async def get_all_vk_users(self) -> List[Users]:
        datas = await self.api.get_all_vk_users()
        return [Users(**data) for data in datas]

    async def update_vk_id(self, user: Users, vk_id: int) -> Optional[Dict]:
        return await self.api.update_vk_id(
            user_data={"user_id": user.id, "vk_id": vk_id}
        )

    async def back_vk_id(self, user: Users, chat_id_name: str) -> Optional[Dict]:
        return await self.api.back_vk_id(
            user_data={"user_id": user.id, "chat_id_name": chat_id_name}
        )

    async def active_users(self, min_rang: int, max_rang: int) -> Optional[Dict]:
        datas = await self.api.active_users(
            {"min_rang": min_rang, "max_rang": max_rang}
        )
        return [Users(**data) for data in datas]


class Family_TiesMethods:

    def __init__(self):
        self.api = Family_TiesRequests()

    async def get_family(self, user: Users) -> List[Family_Ties]:
        datas = await self.api.get_family(user.user_id)
        return [Family_Ties(**data) for data in datas]

    async def get_target_ties(
        self, parent_user: Users, user: Users
    ) -> Optional[Family_Ties]:
        data = await self.api.get_target_ties(parent_user.user_id, user.user_id)
        return Family_Ties(**data) if data else None

    async def create(
        self,
        from_user: Users,
        to_user: Users,
        idempotency_key: str
    ) -> Family_Ties:
        data = await self.api.create_family(
            user_data={"from_user": from_user.user_id, "to_user": to_user.user_id},
            idempotency_key=idempotency_key
        )
        return Family_Ties(**data) if data else None


class PurchasesMethods:

    def __init__(self):
        self.api = PurchasesRequests()

    async def create(
        self,
        user: Users,
        title: str,
        description: str,
        cost: int,
        product_id: int,
        delivery_data: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Optional[Purchases]:
        data = await self.api.create_purch(
            user_data={
                "user_id": user.user_id,
                "title": title,
                "description": description,
                "cost": cost,
                "product_id": product_id,
                "delivery_data": delivery_data
            },
            idempotency_key=idempotency_key
        )
        return Purchases(**data) if data else None

    async def get_user_purchases(
        self, user: Users, completed: bool = False
    ) -> List[Purchases]:
        datas = await self.api.get_user_purchases(user.user_id, completed)
        return [Purchases(**data) for data in datas]

    async def get_all_purchases(self) -> List[Purchases]:
        datas = await self.api.get_all_purchases()
        return [Purchases(**data) for data in datas]

    async def get_by_id(self, _id: int) -> Optional[Purchases]:
        data = await self.get_by_id(_id)
        return Purchases(**data) if data else None

    async def confirm_purchase(self, task_id: int) -> Purchases:
        data = await self.api.confirm_purchase(user_data={"task_id": task_id})
        return Purchases(**data) if data else None

    async def add_message_id(self, purchases_id: int, message_id: int) -> None:
        await self.api.add_message_id(
            user_data={"purchases_id": purchases_id, "message_id": message_id}
            )

    async def cancel_buy(self, purchases_id: int) -> Optional[Purchases]:
        data = await self.api.cancel_buy(
            user_data={"purchases_id": purchases_id}
            )
        return Purchases(**data) if data else None

    async def success_buy(self, purchases_id: int) -> Optional[Purchases]:
        data = await self.api.success_buy(
            user_data={"purchases_id": purchases_id}
            )
        return Purchases(**data) if data else None

    async def answer_buy(self, answer_message_id: int) -> Optional[Purchases]:
        data = await self.api.answer_buy(
            params={"answer_message_id": answer_message_id}
            )
        return Purchases(**data) if data else None

    async def product_message_id(self, answer_message_id: int, msg_ids: list[int]) -> None:
        await self.api.product_message_id(
            user_data={
                "answer_message_id": answer_message_id,
                "msg_ids": msg_ids
                }
            )

    async def rollback_buy(self, purchases_id: int) -> Optional[Tuple[Purchases,Pikmi_Shop]]:
        data = await self.api.rollback_buy(
            user_data={"purchases_id": purchases_id}
            )
        if not data:
            return None, None
        else:
            return (
                Purchases(**data['purchase']),
                Pikmi_Shop(**data['product'])
                )


class Pikmi_ShopMethods:

    def __init__(self):
        self.api = Pikmi_ShopRequests()

    async def get_all_products(self) -> List[Pikmi_Shop]:
        datas = await self.api.get_all_products()
        return [Pikmi_Shop(**data) for data in datas]

    async def get_by_id(self, product_id: int) -> Optional[Pikmi_Shop]:
        data = await self.api.get_by_id(product_id)
        return Pikmi_Shop(**data) if data else None


class Sigma_BoostsMethods:

    def __init__(self):
        self.api = Sigma_BoostsRequests()

    async def catalog_boosts(self, user: Users) -> Optional[List]:
        return await self.api.get_catalog_boosts(user.id)

    async def info_boost(self, user: Users, name: str) -> Optional[Dict]:
        return await self.api.get_info_boost(user.id, name)

    async def get_by_user(self, user: Users) -> Optional[Sigma_Boosts]:
        data = await self.api.get_by_user(user.user_id)
        return Sigma_Boosts(**data) if data else None

    async def add_passive_income(self, user: Users) -> Optional[Users]:
        data = await self.api.add_passive_income(user_id=user.id)
        return Users(**data["user"]) if data else None

    async def upgrade_boost(self, user: Users, name: str) -> Optional[Dict]:
        return await self.api.upgrade_boost(
            user_data={"user_id": user.id, "name": name}
        )

    async def calculate_recovery_time(self, user: Users) -> timedelta:
        result = await self.api.calculate_recovery_time(user_id=user.id)
        return timedelta(minutes=float(result))


class Lumberjack_GameMethods:

    def __init__(self):
        self.api = Lumberjack_GameRequests()

    async def get_by_user(self, user: Users) -> Optional[Lumberjack_Game]:
        data = await self.api.get_by_user(user.user_id)
        return Lumberjack_Game(**data) if data else None

    async def get_max_energy(self, user: Users) -> int:
        game: Lumberjack_Game = await self.get_by_user(user)
        return game.max_energy if game else 0

    async def get_active_games(self) -> List[Lumberjack_Game]:
        datas = await self.api.get_active_games()
        return [Lumberjack_Game(**data) for data in datas]

    async def update_grid(
        self, game_user_id: int, grid: List
    ) -> Optional[Lumberjack_Game]:
        data = await self.api.update_grid(
            game_user_id=game_user_id, user_data={"grid": grid}
        )
        return Lumberjack_Game(**data) if data else None

    async def process_click(
        self, user_id: int, energy_in_click: int, row: int, col: int
    ) -> Dict:
        return await self.api.process_click(
            user_data={
                "user_id": user_id,
                "energy_in_click": energy_in_click,
                "row": row,
                "col": col,
            }
        )

    async def restore_energy(self, game_user_id: int) -> Dict:
        return await self.api.restore_energy(game_user_id=game_user_id)

    async def game_state(self, user: Users) -> Optional[Dict]:
        data = await self.api.game_state(user_id=user.id)
        if data:
            data["game_user"] = Lumberjack_Game(**data["game_user"])
            return data


class GeoHunter_GameMethods:

    def __init__(self):
        self.api = GeoHunter_GameRequests()

    async def get_by_user(self, user: Users) -> Optional[GeoHunter]:
        data = await self.api.get_by_user(user.user_id)
        return GeoHunter(**data) if data else None

    async def get_active_games(self) -> List[GeoHunter]:
        datas = await self.api.get_active_games()
        return [GeoHunter(**data) for data in datas]

    async def process_click(
        self, user: Users, user_choice: bool, energy_in_click: int = 1
    ) -> GeoHunter:
        data = await self.api.process_click(
            user_data={
                "user_id": user.id,
                "user_choice": user_choice,
                "energy_in_click": energy_in_click,
            }
        )
        return GeoHunter(**data) if data else None

    async def restore_energy(self, game_user: GeoHunter) -> Dict:
        return await self.api.restore_energy(game_user_id=game_user.id)

    async def game_state(self, user: Users) -> Optional[Dict]:
        data = await self.api.game_state(user_id=user.id)
        if data:
            data["game_user"] = GeoHunter(**data["game_user"])
            return data


class Work_KeysMethods:

    def __init__(self):
        self.api = Work_KeysRequests()

    async def create(self) -> Work_Keys:
        data = await self.api.create_key()
        return Work_Keys(**data) if data else None

    async def check_by_key(self, key: str) -> bool:
        return await self.api.check_by_key(key)

    async def register_with_key(self, user: Users, key: str) -> bool:
        return await self.api.register_with_key(
            user_data={"user_id": user.id, "key": key}
        )


class BonusesMethods:

    def __init__(self):
        self.api = BonusesRequests()

    async def create_bonus(
        self,
        type_bonus: str,
        *,
        expires_at: str = None,
        value: Optional[Any] = None,
        max_quantity: Optional[Any] = None,
        duration_hours: Optional[Any] = None,
        idempotency_key: str
    ) -> Bonuses:
        data = await self.api.create_bonus(
            user_data={
                "type_bonus": type_bonus,
                "expires_at": expires_at,
                "value": value,
                "max_quantity": max_quantity,
                "duration_hours": duration_hours,
            },
            idempotency_key=idempotency_key
        )
        return Bonuses(**data) if data else None

    async def get_by_id(self, bonus_id: int) -> Optional[Bonuses]:
        data = await self.api.get_by_id(bonus_id)
        return Bonuses(**data) if data else None

    async def claim_bonus(self, user: Users, bonus_id: int, idempotency_key: str) -> Dict:
        return await self.api.claim_bonus(
            user_data={"user_id": user.id, "bonus_id": bonus_id},
            idempotency_key=idempotency_key
        )


# class UseBonusesMethods:

#     def __init__(self):
#         self.api = UseBonusesRequests()

#     async def create_bonus(self, user: Users, bonus: Bonuses, idempotency_key: str) -> UseBonuses:
#         data = await self.api.create_bonus(
#             user_data={"user_id": user.id, "bonus_id": bonus.id},
#             idempotency_key=idempotency_key
#         )
#         return UseBonuses(**data) if data else None

#     async def get_connection(self, user: Users, bonus: Bonuses) -> Optional[UseBonuses]:
#         data = await self.api.get_connection(user_id=user.id, bonus_id=bonus.id)
#         return UseBonuses(**data) if data else None


class QuestsMethods:

    def __init__(self):
        self.api = QuestsRequests()

    async def get_by_id(self, user_id: int, quest_id: int) -> Optional[Quests]:
        data = await self.api.get_info(user_id, quest_id)
        return Quests(**data) if data else None

    async def get_quests(self) -> List[Quests]:
        datas = await self.api.get_quests()
        return [Quests(**data) for data in datas]

    async def get_active_quests(self, user: Users) -> List[Quests]:
        datas = await self.api.get_active_quests(user.id)
        return [Quests(**data) for data in datas]


class UseQuestsMethods:

    def __init__(self):
        self.api = UseQuestsRequests()

    async def create_quest(
        self, user: Users, quest: Quests, idempotency_key: str
    ) -> Union[SubscribeQuest, IdeaQuests]:
        data = await self.api.create_quest(
            user_data={"user_id": user.id, "quest_id": quest.id},
            idempotency_key=idempotency_key
        )
        if quest.type_quest == "subscribe":
            return SubscribeQuest(**data) if data else None
        elif quest.type_quest == "idea":
            return IdeaQuests(**data) if data else None

    async def get_connection(self, user: Users, quest: Quests) -> Optional[bool]:
        return await self.api.get_connection(user_id=user.id, quest_id=quest.id)

    async def get_all_users_sub_tg_chat(self, quest_id: int) -> List[Users]:
        datas = await self.api.get_all_sub_tg_chat(quest_id=quest_id)
        return [Users(**data) for data in datas]

    async def get_all_users_sub_vk_chat(self, quest_id: int) -> List[Users]:
        datas = await self.api.get_all_sub_vk_chat(quest_id=quest_id)
        return [Users(**data) for data in datas]

    async def back_tg_quest(self, user: Users, quest: Quests) -> None:
        await self.api.back_tg_quest(
            user_data={"user_id": user.id, "quest_id": quest.id}
        )

    async def create_idea_daily(
        self, user_id: int, quest_id: int, idempotency_key: str
    ) -> Optional[Union[bool, float]]:
        return await self.api.create_idea_daily(
            user_data={"user_id": user_id, "quest_id": quest_id},
            idempotency_key=idempotency_key
        )

    async def success_idea_daily(self, user: Users, quest_id: int) -> Union[float, int]:
        return await self.api.success_idea_daily(
            user_data={"user_id": user.id, "quest_id": quest_id}
        )

    async def delete(self, user_id: int, quest_id: int) -> Dict:
        return await self.api.delete_quest(
            user_data={"user_id": user_id, "quest_id": quest_id}
        )


class CopyBaseMethods:

    def __init__(self):
        self.api = CopyBaseRequests()

    async def copy_base(
        self,
    ) -> str:
        return await self.api.copy_base()

    def sync_copy_bd(
        self,
    ) -> str:
        return self.api.sync_copy_base()


class RangsMethods:

    def __init__(self):
        self.api = RangsRequests()

    async def get_by_role(self, role: str) -> List[Rangs]:
        datas = await self.api.get_by_role(role)
        return [Rangs(**data) for data in datas]


class PromocodesMethods:

    def __init__(self):
        self.api = PromocodesRequests()

    async def activate(self, user_id: int, code: str, idempotency_key: str) -> Union[StarcoinsPromo, str]:
        data = await self.api.activate(user_id, code, idempotency_key)

        if data:
            if data.get("data"):
                if data.get("type") == "starcoins":
                    return StarcoinsPromo(**data["data"])
                else:
                    return "server_error"
            elif data.get("error"):
                return data["error"]
            else:
                return "server_error"
        else:
            return "server_error"


class ManagementLinksMethods:

    def __init__(self):
        self.api = ManagementLinksRequests()

    async def activate(self, user_id: int, utm: str, idempotency_key: str) -> Optional[bool]:
        return await self.api.activate(user_id, utm, idempotency_key)


class InteractiveGameMethods:

    def __init__(self):
        self.api = InteractiveGameRequests()

    async def get(self, game_id: int) -> Optional[InteractiveGameBase]:
        game = await self.api.get(game_id)
        return InteractiveGameBase(**game) if game else None

    async def create(self, user: Users, data: dict) -> Optional[InteractiveGameBase]:
        game = await self.api.create(user_data={"user_id": user.id, "data": data})
        return InteractiveGameBase(**game) if game else None

    async def delete_rejected(self, game_id: int) -> Optional[InteractiveGameBase]:
        game = await self.api.delete_rejected(game_id)
        return InteractiveGameBase(**game) if game else None

    async def success_game(self, game_id: int) -> Optional[InteractiveGameBase]:
        game = await self.api.success_game(game_id)
        return InteractiveGameBase(**game) if game else None

    async def invite_game(
        self, game_id: int, user: Users
    ) -> Optional[InteractiveGameBase]:
        game = await self.api.invite_game(game_id, user.id)
        return InteractiveGameBase(**game) if game else None

    async def delete_pending(self, game_id: int) -> Optional[InteractiveGameInfo]:
        game = await self.api.delete_pending(game_id)
        return InteractiveGameInfo(**game) if game else None

    async def start_game(self, game_id: int) -> Optional[InteractiveGameInfo]:
        game = await self.api.start_game(game_id)
        return InteractiveGameInfo(**game) if game else None

    async def get_info(self, game_id: int) -> Optional[InteractiveGameInfo]:
        game = await self.api.get_info(game_id)
        return InteractiveGameInfo(**game) if game else None

    async def end_game(
        self, game_id: int, winers: List[str]
    ) -> Optional[InteractiveGameAllInfo]:
        game = await self.api.end_game(game_id, data={"winers": winers})
        return InteractiveGameAllInfo(**game) if game else None


class RatingMethods:

    def __init__(self):
        self.api = RatingRequests()

    async def daily_login(self, user_id: int) -> Optional[Dict]:
        return await self.api.daily_login(user_id)

    async def collect_starcoins(self, user_id: int) -> Optional[Dict]:
        return await self.api.collect_starcoins(user_id)

    async def guess_country(self, user_id: int) -> Optional[Dict]:
        return await self.api.guess_country(user_id)

    async def make_clicks(self, user_id: int) -> Optional[Dict]:
        return await self.api.make_clicks(user_id)

    async def completed_quests(self, user_id: int) -> Optional[Dict]:
        return await self.api.completed_quests(user_id)

    async def invited_friends(self, user_id: int) -> Optional[Dict]:
        return await self.api.invited_friends(user_id)

