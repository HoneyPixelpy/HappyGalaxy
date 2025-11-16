import os
import aiohttp
import json
from typing import Optional, Dict, Any
from loguru import logger
import requests

from MainBot.utils.errors import InternalServerErrorClass


class DjangoAPI:
    
    def __init__(self):
        self.base_url = "http://{}/api/v1".format(
            os.getenv("DJANGO_API_LINK")
        )
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None
        ) -> Any:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    json=data,
                    params=params,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                ) as response:
                    if response.status == 200 or response.status == 201:
                        # Пытаемся получить содержимое ответа в наиболее универсальном виде
                        try:
                            content = await response.read()
                            if not content:  # Пустой ответ
                                return None
                            
                            # Пробуем декодировать JSON
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                # Если не JSON, возвращаем как текст или буфер
                                return content.decode('utf-8')
                        except UnicodeDecodeError:
                            return content
                        except Exception as e:
                            logger.error(f"Failed to process response: {e.__class__.__name__}")
                            return None
                    elif response.status == 500:
                        await InternalServerErrorClass().send(f"Неопределенная ошибка, {method} {self.base_url}{endpoint} {str(data)} {str(params)}\n\n{str(response)}")
                    return None
        
        except TimeoutError:
            await InternalServerErrorClass().send(f"Не ответили за 20 сек, {method} {self.base_url}{endpoint} {str(data)} {str(params)}")
        except aiohttp.ClientConnectorError:
            await InternalServerErrorClass().send(f"Сервер не отвечает, {method} {self.base_url}{endpoint} {str(data)} {str(params)}")

    def _sync_make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None
        ) -> Any:
        try:
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                json=data,
                params=params,
                headers={"Content-Type": "application/json"},
                timeout=20
            )
            if response.status_code == 200 or response.status_code == 201:
                # Пытаемся получить содержимое ответа в наиболее универсальном виде
                try:
                    if not response.content:  # Пустой ответ
                        return None
                    return response.json()
                except Exception as e:
                    logger.error(f"Failed to process response: {e.__class__.__name__}")
                    return response.content
            elif response.status_code == 500:
                logger.error(f"Неопределенная ошибка, {method} {self.base_url}{endpoint} {str(data)} {str(params)}\n\n{str(response)}")
            return None
        
        except TimeoutError:
            logger.error(f"Не ответили за 20 сек, {method} {self.base_url}{endpoint} {str(data)} {str(params)}")
        except aiohttp.ClientConnectorError:
            logger.error(f"Сервер не отвечает, {method} {self.base_url}{endpoint} {str(data)} {str(params)}")


class DataRequests(DjangoAPI):

    async def get_reward_data(self) -> Optional[Dict]:
        return await self._make_request("GET", "/reward_data/")

    async def get_catalog_boosts(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/boosts_data/catalog",
            params={
                'user_id': user_id
            }
        )

    async def get_info_boost(self, user_id: int, name: str) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/boosts_data/info",
            params={
                'user_id': user_id,
                'name': name
            }
        )


class UsersRequests(DjangoAPI):

    async def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/users/{user_id}/")

    async def create_user(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/users/", user_data)

    async def get_all_users(self, **kwargs) -> Optional[Dict]:
        return await self._make_request("GET", "/users/", data=kwargs)

    async def get_banned_users(self) -> Optional[Dict]:
        return await self._make_request("GET", "/users/banned/")

    async def get_referral_count(self, user_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/users/{user_id}/referrals/count/")

    async def check_phone(self, phone: str) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/users/check_phone/",
            params={
                "phone": phone
            }
        )

    # async def check_fio(self, last_name: str, first_name: str, middle_name: str) -> Optional[Dict]:
    #     return await self._make_request(
    #         "GET", 
    #         "/users/check_fio/",
    #         params={
    #             "last_name": last_name,
    #             "first_name": first_name,
    #             "middle_name": middle_name
    #         }
    #     )

    async def check_nickname(self, nickname: str) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/users/check_nickname/",
            params={
                "nickname": nickname
            }
        )

    async def complete_registration(self, user_id, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PUT", 
            f"/users/{user_id}/complete_registration/", 
            user_data
            )

    async def update_username(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/users/update_telegram_username/", 
            user_data
            )

    async def update_balance(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/users/update_balance/", 
            user_data
            )

    async def update_ban(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/users/update_ban/", 
            user_data
            )

    async def process_referral(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/users/process_referral/", user_data)

    async def update_vk_id(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/users/update_vk_id/", 
            user_data
            )

    async def get_all_vk_users(self) -> Optional[Dict]:
        return await self._make_request("GET", f"/users/get_all_vk_users/")

    async def back_vk_id(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "DELETE", 
            "/users/back_vk_id/", 
            user_data
            )

    async def active_users(self, data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/users/active_users/",
            data
            )


class Family_TiesRequests(DjangoAPI):

    async def get_family(self, user_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/family-ties/{user_id}/get_family/")

    async def get_target_ties(self, parent_id: int, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/family-ties/get_target_ties/",
            params={
                'parent_id': parent_id,
                'user_id': user_id
            }
        )

    async def create_family(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/family-ties/", user_data)


class PurchasesRequests(DjangoAPI):

    async def create_purch(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/purchases/", user_data)

    async def get_user_purchases(self, user_id: int, completed: bool) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/purchases/user_purchases/",
            params={
                'completed': str(completed),
                'user_id': user_id
            }
        )

    async def get_all_purchases(self) -> Optional[Dict]:
        return await self._make_request("GET", "/purchases/")

    async def get_by_id(self, id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/purchases/{id}/")

    async def confirm_purchase(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/purchases/confirm_purchase/", 
            user_data
            )


class Pikmi_ShopRequests(DjangoAPI):

    async def get_all_products(self) -> Optional[Dict]:
        return await self._make_request("GET", "/pikmi-shop/")

    async def get_by_id(self, id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/pikmi-shop/{id}/")


class Sigma_BoostsRequests(DjangoAPI):

    async def get_by_user(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/sigma-boosts/get_by_user/",
            params={
                'user_id': user_id
            }
        )

    async def add_passive_income(self, user_id) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/sigma-boosts/{user_id}/add_passive_income/"
            )

    async def upgrade_boost(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/sigma-boosts/upgrade_boost/", 
            user_data
            )

    async def calculate_recovery_time(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/sigma-boosts/calculate_recovery_time/",
            params={
                'user_id': user_id
            }
        )


class Lumberjack_GameRequests(DjangoAPI):

    async def get_by_user(self, user_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/lumberjack-games/{user_id}/")

    async def get_active_games(self) -> Optional[Dict]:
        return await self._make_request("GET", "/lumberjack-games/active_games/")

    async def update_grid(self, game_user_id, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/lumberjack-games/{game_user_id}/update_grid/", 
            user_data
            )

    async def process_click(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/lumberjack-games/process_click/", 
            user_data
            )

    async def update_energy(self, game_user_id) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/lumberjack-games/{game_user_id}/restore_energy/"
            )

    async def refresh_energy(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/lumberjack-games/refresh_energy/",
            params={
                'user_id': user_id
            }
        )


class GeoHunter_GameRequests(DjangoAPI):

    async def get_by_user(self, user_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/geo-hunter/{user_id}/")

    async def get_active_games(self) -> Optional[Dict]:
        return await self._make_request("GET", "/geo-hunter/active_games/")

    async def process_click(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/geo-hunter/process_click/", 
            user_data
            )

    async def update_energy(self, game_user_id) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/geo-hunter/{game_user_id}/restore_energy/"
            )

    async def refresh_energy(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/geo-hunter/refresh_energy/",
            params={
                'user_id': user_id
            }
        )


class Work_KeysRequests(DjangoAPI):

    async def create_key(self) -> Optional[Dict]:
        return await self._make_request("POST", "/work-keys/")

    async def check_by_key(self, key: str) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/work-keys/check_by_key/",
            params={
                'key': key
            }
        )

    async def register_with_key(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/work-keys/register_with_key/", 
            user_data
            )


class BonusesRequests(DjangoAPI):

    async def create_bonus(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/bonuses/", user_data)

    async def get_by_id(self, id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/bonuses/{id}/")

    async def claim_bonus(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/bonuses/claim_bonus/", user_data)


class UseBonusesRequests(DjangoAPI):

    async def create_bonus(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/use-bonuses/", user_data)

    async def get_connection(self, user_id: int, bonus_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/use-bonuses/",
            params={
                'user_id': user_id,
                'bonus_id': bonus_id
            }
        )


class QuestsRequests(DjangoAPI):

    # async def create_quest(self, user_data: Dict) -> Optional[Dict]:
    #     return await self._make_request("POST", "/quests/create_quest/", user_data)

    async def get_info(self, user_id: int, quest_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/quests/get_info/",
            params={
                'user_id': user_id,
                'quest_id': quest_id
                }
            )

    async def get_quests(self) -> Optional[Dict]:
        return await self._make_request("GET", "/quests/")

    async def get_active_quests(self, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/quests/active/",
            params={
                'user_id': user_id
            }
        )


class UseQuestsRequests(DjangoAPI):

    async def create_quest(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/use-quests/", user_data)

    async def get_connection(self, user_id: int, quest_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/use-quests/get_quests/",
            params={
                'user_id': user_id,
                'quest_id': quest_id
            }
        )

    async def get_all_sub_tg_chat(self, quest_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/use-quests/sub_tg_chat/",
            params={
                'quest_id': quest_id
                }
            )

    async def get_all_sub_vk_chat(self, quest_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/use-quests/sub_vk_chat/",
            params={
                'quest_id': quest_id
                }
            )

    async def back_tg_quest(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "DELETE", 
            "/use-quests/back_tg_quest/", 
            user_data
            )

    async def create_idea_daily(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/use-quests/create_idea_daily/", user_data)

    async def success_idea_daily(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            "/use-quests/success_idea_daily/", 
            user_data
            )

    async def delete_quest(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "DELETE", 
            "/use-quests/delete_idea/", 
            user_data
            )


class CopyBaseRequests(DjangoAPI):

    async def copy_base(self) -> Optional[Dict]:
        return await self._make_request("POST", "/copy-base/")

    def sync_copy_base(self) -> Optional[Dict]:
        return self._sync_make_request("POST", "/copy-base/")


class RangsRequests(DjangoAPI):

    async def get_by_role(self, role: str) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/rangs/role/",
            params={
                'role': role
            }
        )


class PromocodesRequests(DjangoAPI):

    async def activate(self, user_id: int, code: str) -> Optional[Dict]:
        return await self._make_request(
            "POST", 
            "/promocodes/",
            data={
                'user_id': user_id,
                'code': code
            }
        )


class ManagementLinksRequests(DjangoAPI):

    async def activate(self, user_id: int, utm: str) -> Optional[Dict]:
        return await self._make_request(
            "POST", 
            "/management-link/",
            data={
                'user_id': user_id,
                'utm': utm
            }
        )


class InteractiveGameRequests(DjangoAPI):

    async def get(self, game_id: int) -> Optional[Dict]:
        return await self._make_request("GET", f"/interactive-game/{game_id}/")

    async def create(self, user_data: Dict) -> Optional[Dict]:
        return await self._make_request("POST", "/interactive-game/", user_data)

    async def delete_rejected(self, game_id: int) -> Optional[Dict]:
        return await self._make_request("DELETE", f"/interactive-game/{game_id}/")

    async def success_game(self, game_id: int) -> Optional[Dict]:
        return await self._make_request(
            "POST", 
            "/interactive-game/success_game/",
            data={
                'game_id': game_id
            }
        )

    async def invite_game(self, game_id: int, user_id: int) -> Optional[Dict]:
        return await self._make_request(
            "POST", 
            "/interactive-game/invite_game/",
            data={
                'game_id': game_id,
                'user_id': user_id
            }
        )

    async def delete_pending(self, game_id: int) -> Optional[Dict]:
        return await self._make_request(
            "DELETE", 
            f"/interactive-game/{game_id}/delete_pending/"
        )

    async def start_game(self, game_id: int) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/interactive-game/{game_id}/start_game/"
        )

    async def get_info(self, game_id: int) -> Optional[Dict]:
        return await self._make_request(
            "GET", 
            "/interactive-game/get_info/",
            params={
                'game_id': game_id
            }
        )

    async def end_game(self, game_id, data: Dict) -> Optional[Dict]:
        return await self._make_request(
            "PATCH", 
            f"/interactive-game/{game_id}/end_game/",
            data
        )
