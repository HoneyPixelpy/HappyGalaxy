import json
import os
from typing import Any, Dict, Optional

from loguru import logger
import requests


class FastAPI:

    def __init__(self):
        self.base_url = "http://{}".format(
            os.getenv("FAST_API_LINK")
        )

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
                    if not response.content: # Пустой ответ
                        return None
                    return response.json()
                except json.JSONDecodeError:
                    return response.content
                except Exception as e:
                    logger.error(f"Failed to process response: {e.__class__.__name__}")
                    return response.content
            elif response.status_code == 500:
                logger.error(f"Неопределенная ошибка, {method} {self.base_url}{endpoint} {str(data)} {str(params)}\n\n{str(response)}")
            return None
        
        except TimeoutError:
            logger.error(f"Не ответили за 20 сек, {method} {self.base_url}{endpoint} {str(data)} {str(params)}")



class SendBaseRequests(FastAPI):

    def send_backup(self, user_data: dict) -> Optional[Dict]:
        return self._sync_make_request("POST", "/send-backup/", user_data)

