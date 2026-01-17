from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from zoneinfo import ZoneInfo

import texts
from dateutil.parser import parse
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RewardData(BaseModel):
    starcoins_for_referal: Optional[int] = Field(
        None, description="Награда приглашенному в бота"
    )
    starcoins_for_referer: Optional[int] = Field(
        None, description="Награда пригласившеми в бота"
    )
    starcoins_parent_bonus: Optional[int] = Field(
        None, description="Награда за вступление в семью"
    )


class PydanticBase(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Автоматическая сериализация datetime
        }
        arbitrary_types_allowed = True


class Users(PydanticBase):
    """Полная модель пользователя с сохранением всей бизнес-логики"""

    # Основные ID
    id: Optional[int] = Field(None, description="ID в базе данных")
    user_id: int = Field(..., description="Telegram ID")
    vk_id: Optional[int] = Field(None, description="VK ID")

    # Telegram данные
    tg_first_name: Optional[str] = Field(None, max_length=255)
    tg_last_name: Optional[str] = Field(None, max_length=255)
    tg_username: Optional[str] = Field(None, max_length=255)

    # Реферальная система
    referral_user_id: Optional[int] = Field(None)

    # Авторизация
    authorised: bool = Field(False)
    authorised_at: Optional[datetime] = Field(None)

    # Роли
    role_private: Optional[str] = Field(None)
    role: Optional[str] = Field(None)
    role_name: Optional[str] = Field(None)

    # Персональные данные
    gender: Optional[str] = Field(None)
    age: Optional[datetime] = Field(None)

    name: Optional[str] = Field(None)
    supername: Optional[str] = Field(None)
    patronymic: Optional[str] = Field(None)

    nickname: Optional[str] = Field(None)

    # Контакты
    phone: Optional[str] = Field(None)
    email: Optional[str] = Field(None)

    # Статусы
    active: bool = Field(False)
    ban: bool = Field(False)
    purch_ban: bool = Field(False)

    # Валюта
    starcoins: float = Field(0.0)
    all_starcoins: float = Field(0.0)
    purchases: int = Field(0)

    @field_validator("age", "authorised_at", mode="before")
    def parse_datetime(cls, value: Optional[str | datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo("UTC"))
            return value.astimezone(ZoneInfo("Europe/Moscow"))
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt.astimezone(ZoneInfo("Europe/Moscow"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("starcoins", "all_starcoins", mode="after")
    def round_starcoins(cls, value: float) -> float:
        """Автоматически округляет starcoins при создании/обновлении модели"""
        return int(value) if int(value) == value else round(value, 4)

    def __str__(self):
        return f"{self.user_id} {self.tg_first_name} {self.authorised}"


class Family_Ties(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    from_user: Optional[Users] = Field(None, description="Объект инициатора")
    to_user: Optional[Users] = Field(None, description="Объект получателя")

    @model_validator(mode="before")
    @classmethod
    def load_relationships(cls, data):
        """Автоматическая загрузка связанных объектов"""
        if isinstance(data, dict):
            return data
        # Для объектов Django автоматически подгружаем связи
        data.from_user = data.from_user
        data.to_user = data.to_user
        return data


class Purchases(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user: Optional[Users] = Field(None, description="Объект пользователя")
    purchase_date: Optional[datetime] = Field(None, description="Дата покупки")
    title: Optional[str] = Field(None, description="Название покупки")
    description: Optional[str] = Field(None, description="Описание покупки")
    cost: Optional[float] = Field(None, description="Стоимость покупки")
    delivery_data: Optional[str] = Field(None, description="Данные для выдачи")
    product_ids: List[int] = Field(default_factory=list, description="ID товаров")
    message_id: Optional[int] = Field(None, description="ID сообщения")
    completed: bool = Field(False, description="Статус завершения")
    completed_at: Optional[datetime] = Field(None, description="Дата завершения")

    @field_validator("purchase_date", "completed_at", mode="before")
    def parse_datetime(cls, value: Optional[str | datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo("UTC"))
            return value.astimezone(ZoneInfo("Europe/Moscow"))
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt.astimezone(ZoneInfo("Europe/Moscow"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("completed_at", mode="after")
    def convert_to_utc_for_storage(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("UTC"))

    @field_validator("cost", mode="after")
    def round_starcoins(cls, value: float) -> float:
        """Автоматически округляет starcoins при создании/обновлении модели"""
        return int(value) if int(value) == value else round(value, 4)


class Pikmi_Shop(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, alias="_price")
    role: Optional[str] = Field(None, max_length=255)
    delivery_instructions: Optional[str] = None
    quantity: int

    @field_validator("price", mode="after")
    def round_price(cls, value) -> Optional[float]:
        if value is None:
            return None
        try:
            value_float = float(value)
            return (
                int(value_float)
                if round(value_float, 4) == int(value_float)
                else round(value_float, 4)
            )
        except (TypeError, ValueError):
            raise ValueError("Price must be a valid number")

    class Config:
        from_attributes = True  # Заменяет orm_mode в Pydantic V2
        populate_by_name = True  # Заменяет allow_population_by_field_name
        use_enum_values = True


class Sigma_Boosts(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user_data: Optional[Users] = Field(None, description="Объект пользователя")
    income_level: int = Field(
        0, ge=0, le=19, description="Уровень дохода за клик (0-19)"
    )
    energy_capacity_level: int = Field(
        0, ge=0, le=7, description="Уровень запаса энергии (0-7)"
    )
    recovery_level: int = Field(
        0, ge=0, le=2, description="Скорость восстановления (0-2)"
    )
    passive_income_level: int = Field(
        0, ge=0, le=3, description="Пассивный доход (0-3)"
    )
    last_passive_claim: Optional[datetime] = Field(None, alias="_last_passive_claim")

    @field_validator("last_passive_claim", mode="before")
    def convert_to_moscow_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Парсим строку в datetime с учетом временной зоны
            dt = parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("last_passive_claim", mode="after")
    def convert_to_utc_for_storage(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("UTC"))

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class Lumberjack_Game(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user: Optional[Users] = Field(None, description="Объект пользователя")
    game_date: datetime = Field(
        default_factory=datetime.now, description="Дата создания игры"
    )
    current_energy: int = Field(0, ge=0, description="Текущая энергия")
    max_energy: int = Field(0, ge=0, description="Максимальная энергия")
    last_energy_update: Optional[datetime] = Field(None)
    total_clicks: int = Field(0, ge=0, description="Общее количество кликов")
    total_currency: float = Field(0.0, description="Заработанная валюта")
    current_grid: List[Any] = Field(
        default_factory=list, description="Текущее состояние поля 4x5"
    )

    @field_validator("game_date", "last_energy_update", mode="before")
    def parse_datetime(cls, value: Optional[str | datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Парсим строку в datetime с учетом временной зоны
            dt = parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("last_energy_update", mode="after")
    def convert_to_moscow_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("Europe/Moscow"))

    @field_validator("total_currency", mode="after")
    def round_currency(cls, value: float) -> float:
        return int(value) if round(value, 4) == int(value) else round(value, 4)


class GeoHunter(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user: Optional[Users] = Field(None, description="Объект пользователя")
    game_date: datetime = Field(
        default_factory=datetime.now, description="Дата создания игры"
    )
    current_energy: int = Field(0, ge=0, description="Текущая энергия")
    max_energy: int = Field(0, ge=0, description="Максимальная энергия")
    last_energy_update: Optional[datetime] = Field(None)
    total_true: int = Field(0, ge=0, description="Общее количество правильных ответов")
    total_false: int = Field(
        0, ge=0, description="Общее количество не правильных ответов"
    )
    total_currency: float = Field(0.0, description="Заработанная валюта")

    @field_validator("game_date", "last_energy_update", mode="before")
    def parse_datetime(cls, value: Optional[str | datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Парсим строку в datetime с учетом временной зоны
            dt = parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("last_energy_update", mode="after")
    def convert_to_moscow_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("Europe/Moscow"))

    @field_validator("total_currency", mode="after")
    def round_currency(cls, value: float) -> float:
        return int(value) if round(value, 4) == int(value) else round(value, 4)


class Work_Keys(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    from_user_id: Optional[int] = Field(
        None,
        description="ID пользователя, создавшего ключ",
        json_schema_extra={"foreign_key": "Users.id"},
    )
    key: str = Field(
        ...,
        max_length=8,
        description="Уникальный ключ работы",
        json_schema_extra={"example": "A1B2C3D4"},
    )

    class Config:
        from_attributes = True  # Ранее known_as orm_mode
        populate_by_name = True  # Разрешает использование alias
        json_schema_extra = {"example": {"from_user_id": 1, "key": "X5Y6Z7W8"}}


class BonusType(str, Enum):
    ADD_STARCOINS = "add_starcoins"
    CLICK_SCALE = "click_scale"
    ENERGY_RENEWAL = "energy_renewal"


class AddStarcoinsBonus(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_bonus: Literal[BonusType.ADD_STARCOINS] = BonusType.ADD_STARCOINS
    value: float = Field(..., alias="value")
    use_quantity: int = 0
    max_quantity: Optional[int] = None

    @field_validator("value", mode="after")
    def round_starcoins(cls, value: float) -> float:
        """Автоматически округляет starcoins при создании/обновлении модели"""
        return int(value) if int(value) == value else round(value, 4)


class ClickScaleBonus(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_bonus: Literal[BonusType.CLICK_SCALE] = BonusType.CLICK_SCALE
    value: float = Field(..., alias="value")
    duration_hours: float = Field(..., alias="duration_hours")

    @field_validator("value", "duration_hours", mode="after")
    def round_starcoins(cls, value: float) -> float:
        """Автоматически округляет starcoins при создании/обновлении модели"""
        return int(value) if int(value) == value else round(value, 4)


class EnergyRenewalBonus(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_bonus: Literal[BonusType.ENERGY_RENEWAL] = BonusType.ENERGY_RENEWAL
    duration_hours: float = Field(..., alias="duration_hours")

    @field_validator("duration_hours", mode="after")
    def round_starcoins(cls, value: float) -> float:
        """Автоматически округляет starcoins при создании/обновлении модели"""
        return int(value) if int(value) == value else round(value, 4)


class Bonuses(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_bonus: Optional[BonusType]
    active: bool = True
    expires_at: Optional[datetime] = Field(None, alias="expires_at")
    bonus_data: Union[AddStarcoinsBonus, ClickScaleBonus, EnergyRenewalBonus] = Field(
        ..., discriminator="type_bonus"
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_bonus_data(cls, data: Any) -> Dict[str, Any]:
        if isinstance(data, dict):
            bonus_type = data.get("type_bonus")
            bonus_data = data.get("bonus_data", {})

            # Добавляем type_bonus в bonus_data для совместимости
            if isinstance(bonus_data, dict):
                bonus_data["type_bonus"] = bonus_type

            if bonus_type == BonusType.ADD_STARCOINS:
                data["bonus_data"] = AddStarcoinsBonus(**bonus_data)
            elif bonus_type == BonusType.CLICK_SCALE:
                data["bonus_data"] = ClickScaleBonus(**bonus_data)
            elif bonus_type == BonusType.ENERGY_RENEWAL:
                data["bonus_data"] = EnergyRenewalBonus(**bonus_data)

        return data

    @field_validator("expires_at", mode="before")
    def convert_to_moscow_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Парсим строку в datetime с учетом временной зоны
            dt = parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("expires_at", mode="after")
    def convert_to_utc_for_storage(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("UTC"))

    class Config:
        from_attributes = True
        populate_by_name = True


class UseBonuses(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user_id: int = Field(
        ...,
        description="ID пользователя, который использует бонус",
        json_schema_extra={"foreign_key": "Users.id"},
    )
    bonus_id: int = Field(
        ...,
        description="ID бонуса, который используется",
        json_schema_extra={"foreign_key": "Bonuses.id"},
    )

    class Config:
        from_attributes = True  # Для работы с ORM
        populate_by_name = True  # Для поддержки alias
        json_schema_extra = {"example": {"user_id": 123, "bonus_id": 456}}


class QuestType(str, Enum):
    SUBSCRIBE = "subscribe"
    IDEA = "idea"
    DAILY = "daily"


class PlatformType(str, Enum):
    TG = "tg"
    VK = "vk"


class IdeaType(str, Enum):
    IDEA = "galactic_idea"
    DESCR = "descr_happy"
    SHOW = "show_happy"


class ResponseType(str, Enum):
    CONTENT = "content"
    BUTTON = "button"


class MessageType(str, Enum):
    # ONLY_TEXT = 'only_text'
    # ONLY_MEDIA = 'only_media'
    ANY = "any"
    VISIBLE = "visible"
    DESCRIPTION = "description"


class IdeaQuests(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_quest: QuestType = QuestType.IDEA  # Дискриминатор
    title: str = Field(..., max_length=255)
    description: str = Field(...)
    call_action: str = Field(...)
    content: MessageType = Field(...)
    count_use: Optional[int] = Field(1)
    reward_starcoins: float = Field(..., alias="_reward_starcoins")
    type: Optional[IdeaType] = None

    @field_validator("reward_starcoins", mode="after")
    def round_reward(cls, value: float) -> float:
        return int(value) if value == int(value) else round(value, 4)


class SubscribeQuest(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_quest: QuestType = QuestType.SUBSCRIBE  # Дискриминатор
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    url: str = Field(..., format="uri")
    chat_id_name: Optional[str] = Field(None, max_length=255)
    reward_starcoins: float = Field(..., alias="_reward_starcoins")
    type: Optional[PlatformType] = None
    group_token: Optional[str] = Field(...)

    @field_validator("reward_starcoins", mode="after")
    def round_reward(cls, value: float) -> float:
        return int(value) if value == int(value) else round(value, 4)

    class Config:
        from_attributes = True
        populate_by_name = True


class DailyQuests(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    type_quest: QuestType = QuestType.DAILY  # Дискриминатор
    title: str = Field(..., max_length=255)
    description: str = Field(...)
    call_action: str = Field(...)
    content: MessageType = Field(...)

    count_use: Optional[int] = Field(...)
    reward_starcoins: float = Field(..., alias="_reward_starcoins")
    scale_type: str = Field(..., max_length=255)
    type: Optional[ResponseType] = Field(...)

    @field_validator("reward_starcoins", mode="after")
    def round_reward(cls, value: float) -> float:
        return int(value) if value == int(value) else round(value, 4)

    class Config:
        from_attributes = True
        populate_by_name = True


class Quests(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    content_type: int = Field(..., description="ID ContentType")
    object_id: int = Field(..., description="ID связанного объекта")
    quest_data: Optional[Union[SubscribeQuest, IdeaQuests, DailyQuests]] = None
    type_quest: Optional[QuestType] = None
    role: Optional[str] = Field(...)
    active: bool = Field(...)
    min_rang_level: int = Field(..., description="Минимальный уровень ранга")
    max_rang_level: int = Field(..., description="Максимальный уровень ранга")
    success_admin: bool = Field(..., description="Подтверждать админом?")
    expires_at: Optional[datetime] = Field(None, alias="_expires_at")

    @model_validator(mode="before")
    @classmethod
    def resolve_quest_data(cls, data: Any) -> Dict[str, Any]:
        if isinstance(data, dict):
            quest_type = data.get("type_quest")
            quest_data = data.get("quest_data", {})

            # Добавляем type_quest в quest_data для совместимости
            if isinstance(quest_data, dict):
                quest_data["type_quest"] = quest_type

            if quest_type == QuestType.SUBSCRIBE:
                data["quest_data"] = SubscribeQuest(**quest_data)
            elif quest_type == QuestType.IDEA:
                data["quest_data"] = IdeaQuests(**quest_data)
            elif quest_type == QuestType.DAILY:
                data["quest_data"] = DailyQuests(**quest_data)

        return data

    @field_validator("expires_at", mode="before")
    def convert_to_moscow_time(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            # Парсим строку в datetime с учетом временной зоны
            dt = parse(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            return dt
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    @field_validator("expires_at", mode="after")
    def convert_to_utc_for_storage(
        cls, value: Optional[datetime]
    ) -> Optional[datetime]:
        if value is None:
            return None
        return value.astimezone(ZoneInfo("UTC"))

    class Config:
        from_attributes = True
        populate_by_name = True


class UseQuests(PydanticBase):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user_id: int = Field(..., description="ID пользователя")
    quest_id: int = Field(..., description="ID квеста")

    class Config:
        from_attributes = True
        populate_by_name = True


class Rangs(PydanticBase):
    # Основные ID
    id: Optional[int] = Field(None, description="ID в базе данных")
    all_starcoins: float = Field(0.0)
    # Роли
    role_private: Optional[str] = Field(None)
    role: Optional[str] = Field(None)
    role_name: Optional[str] = Field(None)

    emoji: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)

    class Config:
        from_attributes = True
        populate_by_name = True


class StarcoinsPromo(PydanticBase):
    # Основные ID
    id: Optional[int] = Field(None, description="ID в базе данных")
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    reward_starcoins: float = Field(0.0)

    class Config:
        from_attributes = True
        populate_by_name = True


class StatusType(str, Enum):
    MODERATION = "moderation"
    READY = "ready"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"
    ENDED = "ended"

    @classmethod
    def items(cls) -> Dict[str, str]:
        return {
            value.value: texts.InteractiveGame.Status.__dict__[value.value]
            for value in cls.__members__.values()
        }


class GameType(str, Enum):
    ALL = "all"
    DUEL = "duel"

    @classmethod
    def items(cls) -> Dict[str, str]:
        return {
            value.value: texts.InteractiveGame.Btns.__dict__[value.value]
            for value in cls.__members__.values()
        }


class RewardType(str, Enum):
    FROM_ALL_WINS = "from_all_wins"
    TO_EACH_WINNER = "to_each_winner"

    @classmethod
    def items(cls) -> Dict[str, str]:
        # logger.debug({value.value: texts.InteractiveGame.Btns.__dict__[value.value] for value in cls.__members__.values()})
        # logger.debug([value.value for value in cls.__members__.values()])
        return {
            value.value: texts.InteractiveGame.Btns.__dict__[value.value]
            for value in cls.__members__.values()
        }


class InteractiveGameBase(BaseModel):
    """Модель для создания новой игры"""

    id: Optional[int] = Field(None, description="ID в базе данных")
    user: Optional[Users] = Field(None, description="Пользователь")

    title: Optional[str] = Field(None, max_length=255, description="Название")
    description: Optional[str] = Field(None, description="Описание")

    reward_starcoins: Optional[float] = Field(None, description="Вознаграждение")
    reward_type: Optional[RewardType] = Field(
        None, description="Способ распределения вознаграждения"
    )

    min_rang: Optional[int] = Field(None, description="Минимальный уровень ранга")
    max_rang: Optional[int] = Field(None, description="Максимальный уровень ранга")

    min_players: Optional[int] = Field(
        None, description="Минимальное количество игроков"
    )
    max_players: Optional[int] = Field(
        None, description="Максимальное количество игроков"
    )

    type_game: Optional[GameType] = Field(None, description="Тип игры")

    game_status: Optional[StatusType] = Field(None, description="Статус")

    start_invite_at: Optional[datetime] = Field(
        None, description="Время начала приглашения"
    )
    start_game_at: Optional[datetime] = Field(None, description="Время начала игры")
    ended_game_at: Optional[datetime] = Field(None, description="Время окончания игры")

    @field_validator("reward_type", mode="after")
    def field_validator_reward_type(cls, value):
        result = RewardType.items().get(value)
        if not result:
            raise ValueError(f"Неверный тип: {value}")
        return result

    @field_validator("type_game", mode="after")
    def field_validator_type_game(cls, value):
        result = GameType.items().get(value)
        if not result:
            raise ValueError(f"Неверный тип: {value}")
        return result

    @field_validator("game_status", mode="after")
    def field_validator_game_status(cls, value):
        result = StatusType.items().get(value)
        if not result:
            raise ValueError(f"Неверный тип: {value}")
        return result


class InteractiveGameInfo(BaseModel):
    id: Optional[int] = Field(None, description="ID в базе данных")
    game: Optional[InteractiveGameBase] = Field(None, description="Игра")
    users: Optional[List[Users]] = Field(None, description="Игроки")


class InteractiveGameData(BaseModel):
    id: Optional[int] = Field(None, description="ID в базе данных")
    user: Optional[Users] = Field(None, description="Игрок")
    game: Optional[InteractiveGameBase] = Field(None, description="Игра")

    creator: Optional[bool] = Field(None, description="Создатель")
    completed: Optional[bool] = Field(None, description="Завершенность")
    reward_starcoins: Optional[float] = Field(None, description="Вознаграждение")

    result: Optional[str] = Field(None, description="Результат")


class InteractiveGameAllInfo(BaseModel):
    id: Optional[int] = Field(None, description="ID в базе данных")
    game: Optional[InteractiveGameBase] = Field(None, description="Игра")
    game_datas: Optional[List[InteractiveGameData]] = Field(
        None, description="Данные Играков"
    )
