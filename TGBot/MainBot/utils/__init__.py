import asyncio
from typing import Dict

_active_tasks: Dict[int, asyncio.Task] = {}  # {user_id: task}
