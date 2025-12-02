from datetime import datetime, timezone as datetime_timezone
import random
import string
from typing import Optional, Union
from zoneinfo import ZoneInfo

from django.db import models
from django.db.models import Q
from django.forms import JSONField
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from loguru import logger
from bot.service.rang import RangService

# TODO базовый класс с колонками создания и зменения записи (автозаполняющиеся)

def generate_key() -> str:
    characters = string.ascii_letters + string.digits  # буквы (A-Z, a-z) + цифры (0-9)
    return ''.join(random.choice(characters) for _ in range(8))


roles = {
    'parent': 'Родитель',
    'child': 'Ребенок',
    'worker': 'Современник',
    'manager': 'Менеджер',
    None: 'Без роли'
}

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True  # Это ключевое изменение
    
    def _convert_to_utc(self, value):
        if value is None:
            return None
            
        if not isinstance(value, datetime):
            raise ValueError("Должен быть объект datetime")
            
        if value.tzinfo is None:
            value = value.replace(tzinfo=ZoneInfo("Europe/Moscow"))
            
        return value.astimezone(datetime_timezone.utc)
    

class Users(BaseModel):
    
    user_id = models.BigIntegerField(unique=True, verbose_name='Telegram ID') # BigIntegerField
    vk_id = models.BigIntegerField(unique=True, null=True, blank=True, verbose_name='VK ID') # BigIntegerField

    tg_first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='TG Имя')
    tg_last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='TG Фамилия')
    tg_username = models.CharField(max_length=255, blank=True, null=True, verbose_name='TG Юзернейм')

    referral_user_id = models.BigIntegerField(blank=True, null=True, verbose_name='Telegram ID Реферала') # BigIntegerField

    authorised = models.BooleanField(default=False, verbose_name='Авторизован')
    _authorised_at = models.DateTimeField(null=True, blank=True, db_column='authorised_at', verbose_name='Время авторизации')

    _role = models.CharField(max_length=255, blank=True, null=True, db_column='role', choices=roles, verbose_name='Роль')

    gender = models.CharField(max_length=255, blank=True, null=True, verbose_name='Пол')
    _age = models.DateTimeField(blank=True, null=True, db_column='age', verbose_name='Дата рождения')

    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя')
    supername = models.CharField(max_length=255, blank=True, null=True, verbose_name='Фамилия')
    patronymic = models.CharField(max_length=255, blank=True, null=True, verbose_name='Отчество')

    _nickname = models.CharField(max_length=255, blank=True, null=True, db_column="nickname", verbose_name='Никнейм')

    phone = models.CharField(max_length=255, blank=True, null=True, verbose_name='Телефон')
    email = models.CharField(max_length=255, blank=True, null=True, verbose_name='Почта')

    active = models.BooleanField(default=False, verbose_name='На этаже')
    ban = models.BooleanField(default=False, verbose_name='Бан')
    purch_ban = models.BooleanField(default=False, verbose_name='Бан Покупок')
    
    _starcoins = models.FloatField(default=0.0, verbose_name='Starcoins')
    all_starcoins = models.FloatField(default=0.0, verbose_name='All Starcoins')
    purchases = models.IntegerField(default=0, verbose_name='Покупок')

    @property
    def authorised_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._authorised_at is None:
            return None
        return timezone.localtime(
            self._authorised_at,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @authorised_at.setter
    def authorised_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._authorised_at = super()._convert_to_utc(value)
    
    @property
    def age(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._age is None:
            return None
        return timezone.localtime(
            self._age,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @age.setter
    def age(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._age = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._authorised_at and self._authorised_at.tzinfo != datetime_timezone.utc:
            self._authorised_at = self._authorised_at.astimezone(datetime_timezone.utc)
        if self._age and self._age.tzinfo != datetime_timezone.utc:
            self._age = self._age.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)
    
    @property
    def role_name(self):
        if self._role == "child":
            return "⚡️ Главный герой"
        elif self._role == "parent":
            return "❤️ Родитель"
        elif self._role == "worker":
            return "🎖 Современник Галактики"
        elif self._role == "manager":
            return "🛠 Работник"
        else:
            return "Незнакомец"
        
    @property
    def role(self):
        name = roles.get(self._role, "Без роли")
        return f"<u>{name}</u>" if self._role == "child" else name
        
    @role.setter
    def role(self, value):
        self._role = value
    
    @property
    def nickname(self):
        return self._nickname if self._nickname else "Без никнейма"
    
    @nickname.setter
    def nickname(self, value):
        self._nickname = value
    
    @property
    def starcoins(self):
        return int(self._starcoins) if round(self._starcoins, 4) == int(self._starcoins) else round(self._starcoins, 4)
    
    @starcoins.setter
    def starcoins(self, value):
        logger.info(
            "Change Balance: UserID:{0} |Old Balance:{1} |New Balance:{2} |Edit:{3}".format(
                self.user_id,
                self._starcoins,
                value,
                self._starcoins - value
            )
        )
        
        current_rang = self.get_current_rang()
        if self._starcoins < value:
            self.all_starcoins += value - self._starcoins
        
        previous_rang = self.get_current_rang()
        if previous_rang and current_rang and previous_rang.level > current_rang.level:
            self.send_rang_notification(current_rang, previous_rang)
        
        self._starcoins = round(float(value), 4)
    
    def get_current_rang(self) -> Optional['Rangs']:
        """Получить текущий ранг пользователя"""
        return RangService().get_user_rang(self)
    
    def send_rang_notification(self: 'Users', current_rang: 'Rangs', previous_rang: 'Rangs') -> None:
        """Уведомляем пользователя о повышении"""
        new_quests = Quests.objects.filter(
                min_rang_level=previous_rang.level,
                active=True
            ).filter(
                Q(role=self._role) | Q(role__isnull=True)  # ← Явная проверка на NULL
            ).select_related('content_type')
        RangService().send_rang_notification(
            self, 
            current_rang, 
            previous_rang,
            bool(new_quests)
            )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return "{user_id}{tg_username} {f}{i}".format(
                user_id=self.user_id,
                tg_username=f" @{self.tg_username}" if self.tg_username else "",
                f=f" {self.supername}" if self.supername else "",
                i=f" {self.name}" if self.name else ""
            )


class Family_Ties(BaseModel):
    
    from_user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='from_relationships' # django автоматол создает этот слолбик в другой таблице
    )
    to_user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='to_relationships'
    )

    class Meta:
        db_table = 'family_ties'
        verbose_name = 'Родственная связь'
        verbose_name_plural = 'Родственные связи'

    def __str__(self):
        return f"{self.id}"


class Purchases(BaseModel):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='purchase_records',  # Уникальное имя
        verbose_name="Покупатель"
    )
    
    _purchase_date = models.DateTimeField(auto_now_add=True, db_column='purchase_date', verbose_name="Дата покупки")

    title = models.CharField(blank=True, null=True, max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    _cost = models.FloatField(null=True, blank=True, verbose_name="Цена")

    completed = models.BooleanField(default=False, verbose_name="Статус выдачи")
    _completed_at = models.DateTimeField(null=True, blank=True, db_column='completed_at', verbose_name="Дата выдачи")

    @property
    def purchase_date(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._purchase_date is None:
            return None
        return timezone.localtime(
            self._purchase_date,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @property
    def completed_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._completed_at is None:
            return None
        return timezone.localtime(
            self._completed_at,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @completed_at.setter
    def completed_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._completed_at = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._completed_at and self._completed_at.tzinfo != datetime_timezone.utc:
            self._completed_at = self._completed_at.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    @property
    def cost(self):
        return int(self._cost) if round(self._cost, 4) == int(self._cost) else round(self._cost, 4)
    
    @cost.setter
    def cost(self, value):
        self._cost = round(float(value), 4)

    class Meta:
        db_table = 'purchases'
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        return f"{self.user} -> {self.title}. Статус: {self.completed}"


class Pikmi_Shop(BaseModel):
    title = models.CharField(blank=True, null=True, max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    _price = models.FloatField(null=True, blank=True, db_column='price', verbose_name="Цена")
    role = models.CharField(default='child', max_length=255, blank=True, null=True, choices=roles, verbose_name="Роль") # , choices=ROLES

    quantity = models.IntegerField(verbose_name="Осталось")

    @property
    def price(self):
        return int(self._price) if round(self._price, 4) == int(self._price) else round(self._price, 4)
    
    @price.setter
    def price(self, value):
        self._price = round(float(value), 4)

    class Meta:
        db_table = 'pikmi_shop'
        verbose_name = 'Товар'
        verbose_name_plural = 'Магазин'

    def __str__(self):
        return f"{self.title}. Осталось {self.quantity} шт. по {self.price}★"


class Sigma_Boosts(BaseModel):
    user = models.OneToOneField(
        Users, 
        on_delete=models.CASCADE, 
        related_name='boosts',
        verbose_name="Игрок"
        )
    # Улучшения
    income_level = models.IntegerField(default=0, verbose_name="lvl За клик")                  # Уровень дохода за клик (0-19)
    energy_capacity_level = models.IntegerField(default=0, verbose_name="lvl Макс. энергии")         # Уровень запаса энергии (0-7)
    recovery_level = models.IntegerField(default=0, verbose_name="lvl Время восстановления")                # Скорость восстановления (0-2) РАБОТАЕМ С МИНУТАМИ
    passive_income_level = models.IntegerField(default=0, verbose_name="lvl Пассивный заработок")          # Пассивный доход (0-3)
    _last_passive_claim = models.DateTimeField(
        default=timezone.now, db_column='last_passive_claim')         # Последний сбор пассивного дохода
    # TODO кол-во расход энергии за клик

    @property
    def last_passive_claim(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._last_passive_claim is None:
            return None
        return timezone.localtime(
            self._last_passive_claim,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @last_passive_claim.setter
    def last_passive_claim(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._last_passive_claim = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._last_passive_claim and self._last_passive_claim.tzinfo != datetime_timezone.utc:
            self._last_passive_claim = self._last_passive_claim.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'sigma_boosts'
        verbose_name = 'Буст'
        verbose_name_plural = 'Бусты'

    def __str__(self):
        return f"{self.income_level}: {self.energy_capacity_level}: {self.recovery_level}: {self.passive_income_level}"


class Lumberjack_Game(BaseModel):
    user = models.ForeignKey(
        Users, 
        on_delete=models.CASCADE, 
        related_name='games',
        verbose_name="Игрок"
        )
    game_date = models.DateTimeField(auto_now_add=True) # NOTE ненужен
    current_energy = models.IntegerField(default=0, verbose_name="Текущая энергия")
    max_energy = models.IntegerField(default=0, verbose_name="Макс. энергия")
    _last_energy_update = models.DateTimeField(default=timezone.now, db_column='last_energy_update')  # Последнее обновление энергии
    total_clicks = models.BigIntegerField(default=0, verbose_name="Всего кликов") # BigIntegerField
    _total_currency = models.FloatField(default=0.0, verbose_name="Всего заработал")
    current_grid = models.JSONField(default=list)    # Текущее состояние поля 4x5
    # clicks_remaining = models.IntegerField(default=0) # Осталось кликов до обновления поля

    @property
    def last_energy_update(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._last_energy_update is None:
            return None
        return timezone.localtime(
            self._last_energy_update,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @last_energy_update.setter
    def last_energy_update(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._last_energy_update = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._last_energy_update and self._last_energy_update.tzinfo != datetime_timezone.utc:
            self._last_energy_update = self._last_energy_update.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    @property
    def total_currency(self):
        return int(self._total_currency) if round(self._total_currency, 4) == int(self._total_currency) else round(self._total_currency, 4)
    
    @total_currency.setter
    def total_currency(self, value):
        self._total_currency = round(float(value), 4)

    class Meta:
        db_table = 'lumberjack_game'
        verbose_name = 'ГАЛАКТИЧЕСКИЙ КЛИКЕР'
        verbose_name_plural = 'ГАЛАКТИЧЕСКИЙ КЛИКЕР'

    def __str__(self):
        return f"{self.pk} -> {self.user}"


class GeoHunter(BaseModel):
    user = models.ForeignKey(
        Users, 
        on_delete=models.CASCADE, 
        related_name='geo_hunter',
        verbose_name="Игрок"
        )
    game_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания игры") # NOTE ненужен
    current_energy = models.IntegerField(default=0, verbose_name="Текущая энергия")
    max_energy = models.IntegerField(default=0, verbose_name="Макс. энергия")
    _last_energy_update = models.DateTimeField(default=timezone.now, db_column='last_energy_update')  # Последнее обновление энергии
    total_true = models.BigIntegerField(default=0, verbose_name="Общее количество правильных ответов") # BigIntegerField
    total_false = models.BigIntegerField(default=0, verbose_name="Общее количество не правильных ответов") # BigIntegerField
    _total_currency = models.FloatField(default=0.0, verbose_name="Всего заработал")

    @property
    def last_energy_update(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._last_energy_update is None:
            return None
        return timezone.localtime(
            self._last_energy_update,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @last_energy_update.setter
    def last_energy_update(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._last_energy_update = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._last_energy_update and self._last_energy_update.tzinfo != datetime_timezone.utc:
            self._last_energy_update = self._last_energy_update.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    @property
    def total_currency(self):
        return int(self._total_currency) if round(self._total_currency, 4) == int(self._total_currency) else round(self._total_currency, 4)
    
    @total_currency.setter
    def total_currency(self, value):
        self._total_currency = round(float(value), 4)

    class Meta:
        db_table = 'geo_hunter'
        verbose_name = 'ГЕО ХАНТЕР'
        verbose_name_plural = 'ГЕО ХАНТЕР'

    def __str__(self):
        return f"{self.pk} -> {self.user}"


class Work_Keys(BaseModel):
    from_user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='work_key',
        blank=True,
        null=True
    )
    key = models.CharField(max_length=8, unique=True, default=generate_key)

    class Meta:
        db_table = 'work_keys'
        verbose_name = 'Ключ'
        verbose_name_plural = 'Ключи для админов'

    def __str__(self):
        return f"{self.from_user} -> {self.key}"


class AddStarcoinsBonus(BaseModel):
    _value = models.FloatField(db_column='value')
    use_quantity = models.IntegerField(default=0)
    max_quantity = models.IntegerField()

    @property
    def value(self):
        return int(self._value) if round(self._value, 4) == int(self._value) else round(self._value, 4)

    class Meta:
        db_table = 'add_starcoins_bonus'

    def __str__(self):
        return f"Пополнение на {self._value}★ {self.use_quantity}/{self.max_quantity} шт. использований"


class ClickScaleBonus(BaseModel):
    _value = models.FloatField(db_column='value')
    _duration_hours = models.FloatField(db_column='duration_hours')

    @property
    def value(self):
        return int(self._value) if round(self._value, 4) == int(self._value) else round(self._value, 4)

    @property
    def duration_hours(self):
        return int(self._duration_hours) if round(self._duration_hours, 4) == int(self._duration_hours) else round(self._duration_hours, 4)

    class Meta:
        db_table = 'click_scale_bonus'

    def __str__(self):
        return f"Скейл {self._value} на {self._duration_hours} ч. действия"


class EnergyRenewalBonus(BaseModel):
    _duration_hours = models.FloatField(db_column='duration_hours')

    @property
    def duration_hours(self):
        return int(self._duration_hours) if round(self._duration_hours, 4) == int(self._duration_hours) else round(self._duration_hours, 4)

    class Meta:
        db_table = 'energy_renewal_bonus'

    def __str__(self):
        return f"{self._duration_hours} ч. действия"


class Bonuses(BaseModel):
    BONUS_TYPES = (
        ('add_starcoins', 'Starcoin Бонус'),
        ('click_scale', 'Бонус за клик'),
        ('energy_renewal', 'Обновление энергии'),
    )
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    bonus_data = GenericForeignKey('content_type', 'object_id')
    
    type_bonus = models.CharField(max_length=255, choices=BONUS_TYPES, blank=True, null=True, verbose_name="Тип")

    active = models.BooleanField(default=True, verbose_name="Статус")

    _expires_at = models.DateTimeField(db_column='expires_at', blank=True, null=True, verbose_name="Дата истечения")

    @property
    def expires_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._expires_at is None:
            return None
        return timezone.localtime(
            self._expires_at,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @expires_at.setter
    def expires_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._expires_at = super()._convert_to_utc(value)

    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._expires_at and self._expires_at.tzinfo != datetime_timezone.utc:
            self._expires_at = self._expires_at.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'bonuses'
        verbose_name = 'Бонус'
        verbose_name_plural = 'Бонусы'

    def __str__(self):
        return f"Bonus {self.id} - {self.type_bonus} ({'active' if self.active else 'inactive'})"


class UseBonuses(BaseModel):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_bonus'
    )
    bonus = models.ForeignKey(
        Bonuses,
        on_delete=models.CASCADE,
        related_name='use_bonus'
    )

    class Meta:
        db_table = 'use_bonuses'
        verbose_name = 'Ипользованный Бонус'
        verbose_name_plural = 'Использованные Бонусы'

    def __str__(self):
        return f"{self.id}"


class SubscribeQuest(BaseModel):
    types = {
        'tg': 'Телеграмм',
        'vk': 'Вконтакте',
    }

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    url = models.URLField(verbose_name="URL")

    chat_id_name = models.CharField(max_length=255, null=True, verbose_name="chat_id или chat_name")
    _reward_starcoins = models.FloatField(db_column='reward_starcoins', verbose_name="Вознаграждение")
    type = models.CharField(max_length=255, null=True, choices=types, verbose_name="Тип") # tg ; vk ; wa
    group_token = models.CharField(null=True, verbose_name="TOKEN VK бота")

    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    class Meta:
        db_table = 'subscribe_quest'

    def __str__(self):
        return f"{self.title} - {self.url} - {self._reward_starcoins}"


class IdeaQuests(BaseModel):
    contents = {
        'visible': 'Обязательно с медиафайлом',
        'description': 'Обязательно с текстом',
        'any': 'Любое',
    }

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    call_action = models.TextField(blank=True, null=True, verbose_name="Требования к контенту")
    content = models.CharField(max_length=255, null=True, choices=contents, verbose_name="Тип контента")

    count_use = models.IntegerField(null=True, verbose_name="Количество использований")
    _reward_starcoins = models.FloatField(db_column='reward_starcoins', verbose_name="Вознаграждение")
    type = models.CharField(max_length=255, null=True, default="galactic_idea") # galactic_idea ; descr_happy ; show_happy

    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    class Meta:
        db_table = 'idea_quest'

    def __str__(self):
        return f"{self.title} - {self.count_use} - {self._reward_starcoins}"


class DailyQuests(BaseModel):
    contents = {
        'visible': 'Обязательно с медиафайлом',
        'description': 'Обязательно с текстом',
        'any': 'Любое',
    }
    scale_types = {
        'null': 'Без',
        'x_count_use': 'Умножается на кол-во непрерывных использований',
    }
    types = {
        'content': 'Нужно отправить что-то',
        'button': 'Просто нажать на кнопку',
    }

    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    call_action = models.TextField(blank=True, null=True, verbose_name="Требования к контенту")
    content = models.CharField(max_length=255, null=True, choices=contents, verbose_name="Тип контента")

    count_use = models.IntegerField(null=True, verbose_name="Количество использований")
    _reward_starcoins = models.FloatField(db_column='reward_starcoins', verbose_name="Вознаграждение")
    scale_type = models.CharField(max_length=255, null=True, choices=scale_types, verbose_name="Тип скейла") # null ; x_count_use
    type = models.CharField(max_length=255, null=True, default='content', choices=types, verbose_name="Тип выполнения") # button ; content

    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    class Meta:
        db_table = 'daily_quest'

    def __str__(self):
        return f"{self.title} - {self.updated_at.date()}"


class Quests(BaseModel):
    QUEST_TYPES = (
        ('subscribe', 'Бонус за подписку'),
        ('idea', 'Идея'),
        ('daily', 'Раз в день'),
    )

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)
    quest_data = GenericForeignKey('content_type', 'object_id')
    
    type_quest = models.CharField(max_length=255, choices=QUEST_TYPES, blank=True, null=True, verbose_name="Тип квеста")
    role = models.CharField(max_length=255, blank=True, null=True, db_column='role', choices=roles, verbose_name="Роль") # , choices=ROLES

    active = models.BooleanField(default=True)
    min_rang_level = models.IntegerField(default=1, verbose_name='Минимальный уровень ранга')
    max_rang_level = models.IntegerField(default=999999, verbose_name='Максимальный уровень ранга')
    success_admin = models.BooleanField(default=True, verbose_name="Проверка админом")

    _expires_at = models.DateTimeField(db_column='expires_at', blank=True, null=True, verbose_name="Дата просрочки")

    @property
    def expires_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._expires_at is None:
            return None
        return timezone.localtime(
            self._expires_at,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @expires_at.setter
    def expires_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._expires_at = super()._convert_to_utc(value)

    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._expires_at and self._expires_at.tzinfo != datetime_timezone.utc:
            self._expires_at = self._expires_at.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'quests'
        verbose_name = 'Квест'
        verbose_name_plural = 'Квесты'

    def __str__(self):
        return f"Quests {self.id} - {self.type_quest} - {self.quest_data}"


class UseQuests(BaseModel):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_quests'
    )
    quest = models.ForeignKey(
        Quests,
        on_delete=models.CASCADE,
        related_name='use_quest'
    )
    count_use = models.IntegerField(default=1, null=True, verbose_name='Использован раз')

    class Meta:
        db_table = 'use_quests'
        verbose_name = 'Ипользованный Квест'
        verbose_name_plural = 'Использованные Квесты'

    def __str__(self):
        return f"{self.id}"

    def save(self, *args, **kwargs):
        # Проверяем, хотим ли мы сохранить без auto_now
        skip_auto_now = kwargs.pop('skip_auto_now', False)
        
        if skip_auto_now:
            # Временно отключаем auto_now
            updated_at_field = self._meta.get_field('updated_at')
            original_auto_now = updated_at_field.auto_now
            updated_at_field.auto_now = False
            
            try:
                super().save(*args, **kwargs)
            finally:
                # Восстанавливаем auto_now
                updated_at_field.auto_now = original_auto_now
        else:
            super().save(*args, **kwargs)


class QuestModerationAttempt(BaseModel):
    use_quest = models.ForeignKey(
        UseQuests, 
        on_delete=models.CASCADE, 
        related_name='moderation_attempts'
        )
    attempt_number = models.IntegerField(verbose_name='Номер попытки')
    moderation_status = models.CharField(
        max_length=20, 
        choices=(
            ('pending', 'На модерации'),
            ('approved', 'Одобрено'),
            ('rejected', 'Отклонено'),
            ('auto_rejected', 'Авто-отклонено')
        ), 
        default='pending'
        )

    class Meta:
        db_table = 'quest_moderation_attempts'

    def __str__(self):
        return f"Статус {self.moderation_status} у попытки {self.attempt_number} для квеста {self.use_quest.id}"


class ReferralConnections(BaseModel):
    referer = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_referer'
    )
    referal = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_referal'
    )
    referer_starcoins = models.IntegerField(verbose_name="Бонус пригласившему")
    referal_starcoins = models.IntegerField(verbose_name="Бонус приглашенному")
    activate = models.BooleanField(default=True, verbose_name="Был ли выдан бонус за приглашение")

    class Meta:
        db_table = 'referral_connections'
        verbose_name = 'Реферальная связь'
        verbose_name_plural = 'Реферальные связи'

    def __str__(self):
        return f"{self.id}"


class Rangs(BaseModel):

    level = models.IntegerField(verbose_name='Уровень ранга')
    all_starcoins = models.FloatField(default=0.0, verbose_name='All Starcoins')
    _role = models.CharField(max_length=255, blank=True, null=True, db_column='role', choices=roles, verbose_name='Роль')

    emoji = models.CharField(blank=True, verbose_name='Эмоджи')
    name = models.CharField(blank=True, verbose_name='Название')
    
    @property
    def role_name(self):
        if self._role == "child":
            return "⚡️ Главный герой"
        elif self._role == "parent":
            return "❤️ Родитель"
        elif self._role == "worker":
            return "🎖 Современник Галактики"
        elif self._role == "manager":
            return "🛠 Работник"
        else:
            return "Незнакомец"
        
    @property
    def role(self):
        name = roles.get(self._role, "Без роли")
        return f"<u>{name}</u>" if self._role == "child" else name
        
    class Meta:
        db_table = 'rangs'
        verbose_name = 'Ранг'
        verbose_name_plural = 'Ранги'

    def __str__(self):
        return f"{self.level} {self.all_starcoins} {self._role} {self.emoji} {self.name}"


class StarcoinsPromo(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    _reward_starcoins = models.FloatField(db_column='reward_starcoins', verbose_name="Вознаграждение")

    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    class Meta:
        db_table = 'starcoins_promo'

    def __str__(self):
        return f"{self.title} - {self.description} - {self._reward_starcoins}"


class Promocodes(BaseModel):
    PROMO_TYPES = (
        # ('discount', 'скидка на следующий продукт'),
        # ('product', 'заказ'),
        ('starcoins', 'Выдача старкоинов'),
    )

    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)
    promo_data = GenericForeignKey('content_type', 'object_id')
    
    type_promo = models.CharField(max_length=255, choices=PROMO_TYPES, blank=True, null=True, default='starcoins', verbose_name="Тип квеста")
    role = models.CharField(max_length=255, blank=True, null=True, db_column='role', choices=roles, verbose_name="Роль") # , choices=ROLES

    code = models.CharField(unique=True, verbose_name='Код')

    all_quantity = models.IntegerField(verbose_name="Максимальное количество")
    used_quantity = models.IntegerField(default=0, verbose_name="Количество использованных")

    # min_rang_level = models.IntegerField(default=1, verbose_name='Минимальный уровень ранга')
    # max_rang_level = models.IntegerField(default=999999, verbose_name='Максимальный уровень ранга')

    active = models.BooleanField(default=True, verbose_name="Активен")

    _expires_at = models.DateTimeField(blank=True, null=True, db_column='expires_at', verbose_name="Действителен до")

    @property
    def expires_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._expires_at is None:
            return None
        return timezone.localtime(
            self._expires_at,
            timezone=ZoneInfo("Europe/Moscow")
        )

    @expires_at.setter
    def expires_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._expires_at = super()._convert_to_utc(value)
    
    def save(self, *args, **kwargs):
        # Перед сохранением убедимся, что время в UTC
        if self._expires_at and self._expires_at.tzinfo != datetime_timezone.utc:
            self._expires_at = self._expires_at.astimezone(datetime_timezone.utc)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'promocodes'
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
    
    def __str__(self):
        return f"{self.code} - {self.type_promo} - {self.used_quantity}/{self.all_quantity}"


class UsePromocodes(BaseModel):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_promocode'
    )
    promocode = models.ForeignKey(
        Promocodes,
        on_delete=models.CASCADE,
        related_name='use_promocode'
    )

    class Meta:
        db_table = 'use_promocode'
        verbose_name = 'Использованный Промокод'
        verbose_name_plural = 'Использованные Промокоды'

    def __str__(self):
        return f"{self.id}"


class ManagementLinks(BaseModel):
    LINK_TYPES = (
        ('authorised_start', 'регистрация-старт'),
    )

    type_link = models.CharField(max_length=255, choices=LINK_TYPES, blank=True, verbose_name="Тип ссылки")
    # parameters = JSONField(
    #     default=dict,  # или default=list
    #     blank=True,
    #     verbose_name="Параметры"
    # )

    code = models.CharField(unique=True, verbose_name='UTM Code')

    class Meta:
        db_table = 'management_links'
        verbose_name = 'UTM Link'
        verbose_name_plural = 'UTM Links'
    
    def __str__(self):
        return f"{self.code} - {self.type_link}"


class UseManagementLinks(BaseModel):
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='user_management'
    )
    management_link = models.ForeignKey(
        ManagementLinks,
        on_delete=models.CASCADE,
        related_name='management_link'
    )

    class Meta:
        db_table = 'use_management_link'
        verbose_name = 'Использованный UTM Link'
        verbose_name_plural = 'Использованные UTM Links'

    def __str__(self):
        return f"{self.id}"


class InteractiveGames(BaseModel):
    GAME_TYPES = (
        ('all', 'массовое'),
        ('duel', 'дуэль'),
    )
    STATUS_TYPES = (
        ('moderation', 'на модерации'),
        ('ready', 'готов'),
        ('active', 'активная'),
        ('expired', 'просрочена'),
        ('canceled', 'отменена'),
        ('ended', 'завершена'),
    )
    REWARD_TYPES = (
        ('from_all_wins', 'между победителями'),
        ('to_each_winner', 'каждому победителю'),
    )
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='created_interactive_games'
    )
    
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    
    _reward_starcoins = models.FloatField(db_column='reward_starcoins', verbose_name="Вознаграждение")
    reward_type = models.CharField(max_length=255, default='to_each_winner', choices=REWARD_TYPES, blank=True, verbose_name="Способ распределения вознаграждения")
    
    min_rang = models.IntegerField(default=0, verbose_name="Минимальный уровень ранга")
    max_rang = models.IntegerField(default=999999, verbose_name="Максимальный уровень ранга")
    
    min_players = models.IntegerField(default=0, verbose_name="Минимальное количество игроков")
    max_players = models.IntegerField(default=999999, verbose_name="Максимальное количество игроков")
    
    type_game = models.CharField(max_length=255, choices=GAME_TYPES, blank=True, verbose_name="Тип игры")
    
    game_status = models.CharField(max_length=255, choices=STATUS_TYPES, blank=True, default='moderation', verbose_name="Статус")

    _start_invite_at = models.DateTimeField(null=True, verbose_name="Время начала приглашения")
    _start_game_at = models.DateTimeField(null=True, verbose_name="Время начала игры")
    _ended_game_at = models.DateTimeField(null=True, verbose_name="Время завершения игры")

    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    @property
    def start_invite_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._start_invite_at is None:
            return None
        return timezone.localtime(
            self._start_invite_at,
            timezone=ZoneInfo("Europe/Moscow")
        )
    @start_invite_at.setter
    def start_invite_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._start_invite_at = super()._convert_to_utc(value)

    @property
    def start_game_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._start_game_at is None:
            return None
        return timezone.localtime(
            self._start_game_at,
            timezone=ZoneInfo("Europe/Moscow")
        )
    @start_game_at.setter
    def start_game_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._start_game_at = super()._convert_to_utc(value)

    @property
    def ended_game_at(self):
        """Геттер: возвращает время в московском часовом поясе"""
        if self._ended_game_at is None:
            return None
        return timezone.localtime(
            self._ended_game_at,
            timezone=ZoneInfo("Europe/Moscow")
        )
    @ended_game_at.setter
    def ended_game_at(self, value):
        """Сеттер: конвертирует входящее время в UTC перед сохранением"""
        self._ended_game_at = super()._convert_to_utc(value)

    class Meta:
        db_table = 'interactive_games'
        verbose_name = 'Интерактивная игра'
        verbose_name_plural = 'Интерактивные игры'
    
    def __str__(self):
        return f"{self.user} - {self.title}"


class GameData(BaseModel):
    RESULT_TYPES = (
        ('in_game', 'В игре'),
        ('win', 'Победа'),
        ('lose', 'Поражение'),
        ('draw', 'Ничья'),
    )
    
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='game_results'
    )
    game = models.ForeignKey(
        InteractiveGames,
        on_delete=models.CASCADE,
        related_name='game_results'
    )
    creator = models.BooleanField(default=False, verbose_name="Создатель")
    completed = models.BooleanField(default=False, verbose_name="Завершенность")
    _reward_starcoins = models.FloatField(default=0.0, verbose_name="Вознаграждение")

    result = models.CharField(default='in_game', max_length=255, choices=RESULT_TYPES, blank=True, verbose_name="Результат")
    
    @property
    def reward_starcoins(self):
        return int(self._reward_starcoins) if round(self._reward_starcoins, 4) == int(self._reward_starcoins) else round(self._reward_starcoins, 4)
    @reward_starcoins.setter
    def reward_starcoins(self, value):
        self._reward_starcoins = round(float(value), 4)

    class Meta:
        db_table = 'game_results'
        verbose_name = 'Результат игры'
        verbose_name_plural = 'Результаты игр'
    
    def __str__(self):
        return f"{self.user} - {self.game} - {self.result}"


class AnalyticsSummary(BaseModel):
    date = models.DateField(unique=True)

    total_users = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    total_callbacks = models.IntegerField(default=0)

    class Meta:
        db_table = 'analytics_summary'
        verbose_name = 'Analytics Summary'
        verbose_name_plural = 'Analytics Summary'
    
    def __str__(self):
        return f"Analytics for {self.date}"


class BaseUserAction(BaseModel):
    user_id = models.BigIntegerField()  # ID пользователя
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Action'
        verbose_name_plural = 'User Actions'
        abstract = True
        indexes = [
            models.Index(fields=['summary', 'timestamp']),
            models.Index(fields=['user_id', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]


class MessageAction(BaseUserAction):
    summary = models.ForeignKey(
        AnalyticsSummary,
        on_delete=models.CASCADE,
        related_name='message_actions' # message_action
    )

    text = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=50)  # text, photo, document etc.
    message_length = models.IntegerField(default=0)  # Длина сообщения в символах
    
    class Meta:
        db_table = 'user_message_actions'


class CallbackAction(BaseUserAction):
    summary = models.ForeignKey(
        AnalyticsSummary,
        on_delete=models.CASCADE,
        related_name='callback_action' 
    )

    text = models.CharField(max_length=200)
    data = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'user_callback_actions'
        indexes = BaseUserAction.Meta.indexes + [
            models.Index(fields=['data']),
        ]


class UnifiedUserAction(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    user_id = models.BigIntegerField()
    timestamp = models.DateTimeField()
    action_type = models.CharField(max_length=20)
    content = models.TextField()
    
    class Meta:
        managed = False
        db_table = 'user_actions_unified'


class DailyUserStats(BaseModel):
    summary = models.ForeignKey(
        AnalyticsSummary, 
        on_delete=models.CASCADE,
        related_name='user_stats'
    )
    user_id = models.BigIntegerField()
    
    # Основные метрики
    message_count = models.IntegerField(default=0)
    callback_count = models.IntegerField(default=0)
    total_actions = models.IntegerField(default=0)
    
    # Метрики сообщений
    avg_message_length = models.FloatField(default=0)
    message_types = models.JSONField(default=dict)  # {"text": 5, "photo": 2, ...}
    
    # Временные метрики
    first_action = models.DateTimeField()
    last_action = models.DateTimeField()
    active_hours = models.JSONField(default=list)
    
    # Частота действий
    actions_per_hour = models.FloatField(default=0)
    peak_activity_hour = models.IntegerField(null=True)  # Час с максимальной активностью (0-23)
    
    # Поведенческие метрики
    popular_buttons = models.JSONField(default=list)  # Топ-5 кнопок пользователя
    
    class Meta:
        unique_together = ['summary', 'user_id']
        verbose_name = 'Daily User Statistics'
        verbose_name_plural = 'Daily User Statistics'


class DailyButtonStats(BaseModel):
    summary = models.ForeignKey(
        AnalyticsSummary, 
        on_delete=models.CASCADE,
        related_name='button_stats'
    )
    button_text = models.CharField(max_length=200)
    button_data = models.CharField(max_length=100)
    
    # Основные метрикиDailyButtonStats
    total_clicks = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    
    # Временные метрики
    first_click = models.DateTimeField()
    last_click = models.DateTimeField()
    click_times = models.JSONField(default=list)  # Часы кликов для анализа пиков
    
    # Углубленные метрики
    click_frequency = models.FloatField(default=0)  # Кликов/пользователя
    repeat_users = models.IntegerField(default=0)  # Пользователей с >1 кликом
    user_retention_rate = models.FloatField(default=0)  # % повторных пользователей
    
    # Конверсия (если есть последовательность действий)
    avg_time_to_click = models.DurationField(null=True)  # Среднее время до клика с начала сессии
    
    class Meta:
        unique_together = ['summary', 'button_data']
        verbose_name = 'Daily Button Statistics'
        verbose_name_plural = 'Daily Button Statistics'
    
    @property
    def avg_clicks_per_user(self):
        return self.click_frequency


class ShopStats(BaseModel):
    """Статистика по магазину по дням"""
    product = models.ForeignKey(
        Pikmi_Shop,
        on_delete=models.CASCADE,
        related_name='shop_stats',
        verbose_name="Товар"
    )
    summary = models.ForeignKey(
        AnalyticsSummary,
        on_delete=models.CASCADE,
        related_name='shop_stats',
        verbose_name="Дата"
    )
    
    items_sold = models.IntegerField(default=0, verbose_name="Всего выводов")
    total_revenue = models.FloatField(default=0.0, verbose_name="Сумма выводов")
    
    unique_buyers = models.JSONField(
        default=list, 
        verbose_name="Уникальные пользователи"
        ) # NOTE их будет не сильно много
    
    class Meta:
        db_table = 'shop_stats'
        verbose_name = 'Статистика магазина'
        verbose_name_plural = 'Статистика магазина'
        unique_together = ['product', 'summary']
        indexes = [
            models.Index(fields=['summary', 'product']),
        ]

    def __str__(self):
        return f"{self.product.title} - {self.summary}"


class QuestStats(BaseModel):
    """Статистика по квестам по дням"""
    quest = models.ForeignKey(
        Quests,
        on_delete=models.CASCADE,
        related_name='quest_stats',
        verbose_name="Квест"
    )
    summary = models.ForeignKey(
        AnalyticsSummary,
        on_delete=models.CASCADE,
        related_name='quest_stats',
        verbose_name="Дата"
    )
    
    total_rewards = models.FloatField(default=0.0, verbose_name="Всего наград") # NOTE переименовать в rewards
    attempts = models.IntegerField(default=0, verbose_name="Попыток")
    success = models.IntegerField(default=0, verbose_name="Успешных")
    failed = models.IntegerField(default=0, verbose_name="Неудачных")
    unique_users = models.JSONField(
        default=list, 
        verbose_name="Уникальные пользователи"
        ) # NOTE их будет не сильно много
    
    class Meta:
        db_table = 'quest_stats'
        verbose_name = 'Статистика квестов'
        verbose_name_plural = 'Статистика квестов'
        unique_together = ['quest', 'summary']
        indexes = [
            models.Index(fields=['summary', 'quest']),
        ]

    def __str__(self):
        return f"{self.quest} - {self.summary}"


class GamesStats(BaseModel):
    """Статистика по игровой сессии"""
    summary = models.ForeignKey(
        AnalyticsSummary,
        on_delete=models.CASCADE,
        related_name='game_stats',
        verbose_name="Дата"
    )
    
    lumberjack_clicks = models.IntegerField(default=0, verbose_name="Кликов в кликере")
    lumberjack_profit = models.FloatField(default=0.0, verbose_name="Доход в кликере")
    lumberjack_unique_users = models.JSONField(
        default=list, 
        verbose_name="Уникальные пользователи"
        ) # NOTE их будет не сильно много

    geohunter_true = models.IntegerField(default=0, verbose_name="Успешных попаданий")
    geohunter_false = models.IntegerField(default=0, verbose_name="Неудачных попаданий")
    geohunter_profit = models.FloatField(default=0.0, verbose_name="Доход в геохутере")
    geohunter_unique_users = models.JSONField(
        default=list, 
        verbose_name="Уникальные пользователи"
        ) # NOTE их будет не сильно много


    class Meta:
        db_table = 'games_actions'
        verbose_name = 'Статистика игр'
        verbose_name_plural = 'Статистика игр'
        indexes = [
            models.Index(fields=['summary']),
        ]
    
    def __str__(self):
        return f"{self.summary} - {self.lumberjack_profit} - {self.geohunter_profit}"



