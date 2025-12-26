

from typing import Any, Dict, List

from .requests import (AggregatorRequests, CopyBaseRequests,
                       QuestModerationAttemptRequests, UserRequests)


class CopyBaseMethods:
    
    def __init__(self):
        self.api = CopyBaseRequests()

    def copy_base(
        self,
        ) -> str:
        return self.api.copy_base()


class UserMethods:
    
    def __init__(self):
        self.api = UserRequests()

    def unregistered_users(
        self,
        ) -> List[int]:
        return self.api.unregistered_users()


class AggregatorMethods:
    
    def __init__(self):
        self.api = AggregatorRequests()

    def aggregate_data(
        self,
        ) -> List[int]:
        return self.api.aggregate_data()


class QuestModerationAttemptMethods:
    
    def __init__(self):
        self.api = QuestModerationAttemptRequests()

    def old_quest_attempts(
        self,
        ) -> Any:
        return self.api.old_quest_attempts()


class DjangoAPIForms(CopyBaseMethods, UserMethods):
    
    def __init__(self):
        super().__init__()
