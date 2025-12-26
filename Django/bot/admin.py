from datetime import datetime

from django import forms
from django.contrib import admin
from loguru import logger

from .models import *


class UsersAdmin(admin.ModelAdmin):
    list_display = (
        "rang_level",
        "user_id",
        "tg_username",
        "_role",
        "_nickname",
        "_starcoins",
        "all_starcoins",
        "supername",
        "name",
        "gender",
        "_age",
        "phone",
        "ban",
        "purch_ban",
        "authorised",
        "_authorised_at",
    )
    list_display_links = (
        "rang_level",
        "_role",
        "name",
        "supername",
        "gender",
        "_age",
        "phone",
        "_starcoins",
        "all_starcoins",
        "authorised",
        "_authorised_at",
    )
    list_filter = (
        "ban",
        "purch_ban",
        "_role",
    )
    search_fields = (
        "user_id",
        "tg_username",
        "_nickname",
        "name",
        "supername",
        "phone",
    )
    list_editable = ("_nickname",)
    readonly_fields = (
        "_authorised_at",
        "purchases",
    )

    def rang_level(self, obj):
        """Возвращает уровень юзера"""
        if obj:
            current_rang = obj.get_current_rang()
            return current_rang.level
        return 0

    rang_level.short_description = "Уровень"
    rang_level.admin_order_field = "all_starcoins"  # Добавляем возможность сортировки

    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False


class Family_TiesAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    # Отключаем возможность изменения существующих записей
    def has_change_permission(self, request, obj=None):
        return False

    # Настройка отображения в списке
    list_display = ("id", "from_user", "to_user")

    # Поля только для чтения (если оставить возможность просмотра деталей)
    readonly_fields = ("from_user", "to_user")
    list_display_links = ("from_user", "to_user")
    search_fields = (
        "from_user__user_id",
        "from_user__tg_username",
        "to_user__user_id",
        "to_user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class Pikmi_ShopAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "description",
        "role",
        "_price",
        "quantity",
    )
    list_filter = ("role",)
    list_editable = (
        "_price",
        "quantity",
    )
    list_display_links = (
        "title",
        "description",
        "role",
    )
    search_fields = (
        "title",
        "description",
    )


class PurchasesAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    list_display = (
        "title",
        "user",
        "_purchase_date",
        "_cost",
        "completed",
        "_completed_at",
    )
    list_display_links = (
        "user",
        "_purchase_date",
        "title",
        "_cost",
        "_completed_at",
    )
    readonly_fields = (
        "user",
        "_purchase_date",
        "title",
        "description",
        "_cost",
        "_completed_at",
    )
    list_editable = ("completed",)
    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class Lumberjack_GameAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    list_display = (
        "user",
        "current_energy",
        "max_energy",
        "total_clicks",
        "_total_currency",
    )
    list_display_links = (
        "user",
        "current_energy",
        "max_energy",
        "total_clicks",
        "_total_currency",
    )
    readonly_fields = (
        "user",
        "current_energy",
        "max_energy",
        "total_clicks",
        "_total_currency",
        "game_date",
        "_last_energy_update",
        "current_grid",
    )
    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class GeoHunterAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    list_display = (
        "user",
        "current_energy",
        "max_energy",
        "kpd",
        "_total_currency",
    )
    list_display_links = (
        "user",
        "current_energy",
        "max_energy",
        "kpd",
        "_total_currency",
    )
    readonly_fields = (
        "user",
        "current_energy",
        "max_energy",
        "total_true",
        "total_false",
        "_total_currency",
        "game_date",
        "_last_energy_update",
    )
    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    def kpd(self, obj):
        """Возвращает title из связанной модели"""
        try:
            return "{}/{}/{}/{}%".format(
                obj.total_true + obj.total_false,
                obj.total_true,
                obj.total_false,
                round((obj.total_true * 100 / (obj.total_true + obj.total_false)), 2),
            )
        except:
            return "-"

    kpd.short_description = "all/true/false/%"

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class Sigma_BoostsAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    list_display = (
        "user",
        "income_level",
        "energy_capacity_level",
        "recovery_level",
        "passive_income_level",
    )
    list_display_links = (
        "user",
        "income_level",
        "energy_capacity_level",
        "recovery_level",
        "passive_income_level",
    )
    readonly_fields = (
        "user",
        "income_level",
        "energy_capacity_level",
        "recovery_level",
        "passive_income_level",
        "_last_passive_claim",
    )
    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class Work_KeysAdmin(admin.ModelAdmin):
    list_display = (
        "from_user",
        "key",
    )
    list_display_links = (
        "from_user",
        "key",
    )
    readonly_fields = ("key",)


class BonusesAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    list_display = (
        "active",
        "type_bonus",
        "bonus_data",
        "_expires_at",
    )
    list_display_links = (
        "active",
        "type_bonus",
        "bonus_data",
        "_expires_at",
    )
    readonly_fields = (
        "object_id",
        "active",
        "type_bonus",
        "content_type",
        "bonus_data",
        "_expires_at",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class UseBonusesAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    # Отключаем возможность изменения существующих записей
    def has_change_permission(self, request, obj=None):
        return False

    # Настройка отображения в списке
    list_display = ("id", "user", "bonus")

    # Поля только для чтения (если оставить возможность просмотра деталей)
    readonly_fields = ("user", "bonus")

    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class UseQuestsAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quest", "count_use", "updated_at")
    search_fields = (
        "user__user_id",
        "user__tg_username",
    )
    readonly_fields = ("user", "quest", "updated_at")
    list_editable = ("count_use",)

    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    # Отключаем возможность изменения существующих записей
    def has_change_permission(self, request, obj=None):
        return False


class QuestsForm(forms.ModelForm):
    # Добавляем выбор из определенных значений для subscribe_type
    SUBSCRIBE_TYPES = [
        ("tg", "Телеграмм"),
        ("vk", "Вконтакте"),
    ]
    CONTENTS = [
        ("any", "Любое"),
        ("visible", "Обязательно с медиафайлом"),
        ("description", "Обязательно с текстом"),
    ]
    SCALE_TYPES = [
        ("null", "Без"),
        ("x_count_use", "Умножается на кол-во непрерывных использований"),
    ]
    DAILY_TYPES = [
        ("content", "Нужно отправить что-то"),
        ("button", "Просто нажать на кнопку"),
    ]

    # Поля из SubscribeQuest
    subscribe_title = forms.CharField(max_length=255, required=False, label="Заголовок")
    subscribe_description = forms.CharField(
        widget=forms.Textarea, required=False, label="Описание"
    )
    subscribe_url = forms.URLField(required=False, label="URL")
    subscribe_chat_id_name = forms.CharField(
        max_length=255, required=False, label="chat_id или chat_name"
    )
    subscribe_reward_starcoins = forms.FloatField(
        required=False, label="Вознаграждение"
    )
    subscribe_type = forms.ChoiceField(
        choices=SUBSCRIBE_TYPES, required=False, label="Тип"
    )
    subscribe_group_token = forms.CharField(required=False, label="TOKEN группы VK")

    # Поля из IdeaQuests
    idea_title = forms.CharField(max_length=255, required=False, label="Заголовок")
    idea_description = forms.CharField(
        widget=forms.Textarea, required=False, label="Описание"
    )
    idea_call_action = forms.CharField(
        widget=forms.Textarea, required=False, label="Требования к контенту"
    )
    idea_content = forms.ChoiceField(
        choices=CONTENTS, required=False, label="Тип контента"
    )
    idea_count_use = forms.IntegerField(
        required=False, label="Количество использований"
    )
    idea_reward_starcoins = forms.FloatField(required=False, label="Вознаграждение")

    # Поля из DailyQuests
    daily_title = forms.CharField(max_length=255, required=False, label="Заголовок")
    daily_description = forms.CharField(
        widget=forms.Textarea, required=False, label="Описание"
    )
    daily_call_action = forms.CharField(
        widget=forms.Textarea, required=False, label="Требования к контенту"
    )
    daily_content = forms.ChoiceField(
        choices=CONTENTS, required=False, label="Тип контента"
    )
    daily_count_use = forms.IntegerField(
        required=False, label="Количество использований"
    )
    daily_reward_starcoins = forms.FloatField(required=False, label="Вознаграждение")
    daily_scale_type = forms.ChoiceField(
        choices=SCALE_TYPES, required=False, label="Тип скейла"
    )
    daily_type = forms.ChoiceField(
        choices=DAILY_TYPES, required=False, label="Тип выполнения"
    )

    class Meta:
        model = Quests
        fields = "__all__"


class QuestsAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "quest_title",
        "type_quest",
        "role",
        "active",
        "min_rang_level",
        "max_rang_level",
    ]
    list_display_links = [
        "id",
        "quest_title",
        "type_quest",
        "role",
        "min_rang_level",
        "max_rang_level",
    ]
    list_editable = ["active"]
    list_filter = ["type_quest", "role", "active"]

    def quest_title(self, obj):
        """Возвращает title из связанной модели"""
        if obj.quest_data and hasattr(obj.quest_data, "title"):
            return obj.quest_data.title
        return "-"

    quest_title.short_description = "Название квеста"

    form = QuestsForm

    def get_fieldsets(self, request, obj=None):
        """Всегда показываем все fieldsets"""
        fieldsets = [
            (
                "Основная информация",
                {
                    "fields": (
                        "type_quest",
                        "role",
                        "min_rang_level",
                        "active",
                        "max_rang_level",
                        "success_admin",  # , '_expires_at'
                    ),
                    "description": '"Проверка админом" - не учитывается в "Бонус за подписку"',
                },
            ),
            (
                "Бонус за подписку",
                {
                    "fields": (
                        "subscribe_title",
                        "subscribe_description",
                        "subscribe_url",
                        "subscribe_chat_id_name",
                        "subscribe_reward_starcoins",
                        "subscribe_type",
                        "subscribe_group_token",
                    ),
                    "description": 'Заполняйте эти поля только если тип квеста "Бонус за подписку" ; chat_name для телеграмма писать с @',
                },
            ),
            (
                "Идея",
                {
                    "fields": (
                        "idea_title",
                        "idea_description",
                        "idea_call_action",
                        "idea_content",
                        "idea_count_use",
                        "idea_reward_starcoins",
                    ),
                    "description": 'Заполняйте эти поля только если тип квеста "Идея"',
                },
            ),
            (
                "Раз в день",
                {
                    "fields": (
                        "daily_title",
                        "daily_description",
                        "daily_call_action",
                        "daily_content",
                        "daily_reward_starcoins",
                        "daily_scale_type",
                        "daily_type",
                    ),
                    "description": 'Заполняйте эти поля только если тип квеста "Раз в день"',
                },
            ),
        ]

        return fieldsets

    def save_model(self, request, obj, form, change):
        # Сначала сохраняем основной объект Quests
        super().save_model(request, obj, form, change)

        # Всегда создаем/обновляем quest_data в зависимости от type_quest
        self._create_or_update_quest_data(obj, form.cleaned_data)

    def _create_or_update_quest_data(self, quest, cleaned_data):
        """Создает или обновляет объект quest_data с данными из формы"""
        from django.contrib.contenttypes.models import ContentType

        # Если у квеста уже есть связанный объект, но тип изменился - удаляем старый
        if quest.content_type and quest.object_id:
            current_model = quest.content_type.model_class()
            if (
                (quest.type_quest == "subscribe" and current_model != SubscribeQuest)
                or (quest.type_quest == "idea" and current_model != IdeaQuests)
                or (quest.type_quest == "daily" and current_model != DailyQuests)
            ):
                # Тип изменился, удаляем старый объект
                current_model.objects.filter(id=quest.object_id).delete()
                quest.object_id = None
                quest.content_type = None

        if quest.type_quest == "subscribe":
            if quest.object_id:
                # Обновляем существующий объект
                quest_data = SubscribeQuest.objects.get(id=quest.object_id)
                quest_data.title = cleaned_data.get("subscribe_title", "")
                quest_data.description = cleaned_data.get("subscribe_description", "")
                quest_data.url = cleaned_data.get("subscribe_url", "")
                quest_data.chat_id_name = cleaned_data.get("subscribe_chat_id_name", "")
                quest_data.reward_starcoins = cleaned_data.get(
                    "subscribe_reward_starcoins", 0
                )
                quest_data.type = cleaned_data.get("subscribe_type", "tg")
                quest_data.group_token = cleaned_data.get("subscribe_group_token", "")
                quest_data.save()
            else:
                # Создаем новый объект
                quest_data = SubscribeQuest.objects.create(
                    title=cleaned_data.get("subscribe_title", ""),
                    description=cleaned_data.get("subscribe_description", ""),
                    url=cleaned_data.get("subscribe_url", ""),
                    chat_id_name=cleaned_data.get("subscribe_chat_id_name", ""),
                    reward_starcoins=cleaned_data.get("subscribe_reward_starcoins", 0),
                    type=cleaned_data.get("subscribe_type", "tg"),
                    group_token=cleaned_data.get("subscribe_group_token", ""),
                )
                quest.object_id = quest_data.id
                quest.content_type = ContentType.objects.get_for_model(SubscribeQuest)

        elif quest.type_quest == "idea":
            if quest.object_id:
                # Обновляем существующий объект
                quest_data = IdeaQuests.objects.get(id=quest.object_id)
                quest_data.title = cleaned_data.get("idea_title", "")
                quest_data.description = cleaned_data.get("idea_description", "")
                quest_data.call_action = cleaned_data.get("idea_call_action", "")
                quest_data.content = cleaned_data.get("idea_content", "")
                quest_data.count_use = cleaned_data.get("idea_count_use", "")
                quest_data.reward_starcoins = cleaned_data.get(
                    "idea_reward_starcoins", 0
                )
                quest_data.type = cleaned_data.get("idea_type", "galactic_idea")
                quest_data.save()
            else:
                # Создаем новый объект
                quest_data = IdeaQuests.objects.create(
                    title=cleaned_data.get("idea_title", ""),
                    description=cleaned_data.get("idea_description", ""),
                    call_action=cleaned_data.get("idea_call_action", ""),
                    content=cleaned_data.get("idea_content", ""),
                    count_use=cleaned_data.get("idea_count_use", ""),
                    reward_starcoins=cleaned_data.get("idea_reward_starcoins", 0),
                    type=cleaned_data.get("idea_type", "galactic_idea"),
                )
                quest.object_id = quest_data.id
                quest.content_type = ContentType.objects.get_for_model(IdeaQuests)

        elif quest.type_quest == "daily":
            if quest.object_id:
                # Обновляем существующий объект
                quest_data = DailyQuests.objects.get(id=quest.object_id)
                quest_data.title = cleaned_data.get("daily_title", "")
                quest_data.description = cleaned_data.get("daily_description", "")
                quest_data.call_action = cleaned_data.get("daily_call_action", "")
                quest_data.content = cleaned_data.get("daily_content", "")
                # quest_data.count_use = cleaned_data.get('daily_count_use', '')
                quest_data.reward_starcoins = cleaned_data.get(
                    "daily_reward_starcoins", 0
                )
                quest_data.scale_type = cleaned_data.get("daily_scale_type", "")
                quest_data.type = cleaned_data.get("daily_type", "content")
                quest_data.save()
            else:
                # Создаем новый объект
                quest_data = DailyQuests.objects.create(
                    title=cleaned_data.get("daily_title", ""),
                    description=cleaned_data.get("daily_description", ""),
                    call_action=cleaned_data.get("daily_call_action", ""),
                    content=cleaned_data.get("daily_content", ""),
                    # count_use=cleaned_data.get('daily_count_use', ''),
                    reward_starcoins=cleaned_data.get("daily_reward_starcoins", 0),
                    scale_type=cleaned_data.get("daily_scale_type", ""),
                    type=cleaned_data.get("daily_type", "content"),
                )
                quest.object_id = quest_data.id
                quest.content_type = ContentType.objects.get_for_model(DailyQuests)

        quest.save()

    def get_form(self, request, obj=None, **kwargs):
        """Заполняем форму данными из связанного объекта"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.content_type and obj.object_id:
            # Заполняем форму данными из связанного объекта в зависимости от типа квеста
            if obj.type_quest == "subscribe":
                form.base_fields["subscribe_title"].initial = obj.quest_data.title
                form.base_fields["subscribe_description"].initial = (
                    obj.quest_data.description
                )
                form.base_fields["subscribe_url"].initial = obj.quest_data.url
                form.base_fields["subscribe_chat_id_name"].initial = (
                    obj.quest_data.chat_id_name
                )
                form.base_fields["subscribe_reward_starcoins"].initial = (
                    obj.quest_data.reward_starcoins
                )
                form.base_fields["subscribe_type"].initial = obj.quest_data.type
                form.base_fields["subscribe_group_token"].initial = (
                    obj.quest_data.group_token
                )

            elif obj.type_quest == "idea":
                form.base_fields["idea_title"].initial = obj.quest_data.title
                form.base_fields["idea_description"].initial = (
                    obj.quest_data.description
                )
                form.base_fields["idea_call_action"].initial = (
                    obj.quest_data.call_action
                )
                form.base_fields["idea_content"].initial = obj.quest_data.content
                form.base_fields["idea_count_use"].initial = obj.quest_data.count_use
                form.base_fields["idea_reward_starcoins"].initial = (
                    obj.quest_data.reward_starcoins
                )

            elif obj.type_quest == "daily":
                form.base_fields["daily_title"].initial = obj.quest_data.title
                form.base_fields["daily_description"].initial = (
                    obj.quest_data.description
                )
                form.base_fields["daily_call_action"].initial = (
                    obj.quest_data.call_action
                )
                form.base_fields["daily_content"].initial = obj.quest_data.content
                form.base_fields["daily_count_use"].initial = obj.quest_data.count_use
                form.base_fields["daily_reward_starcoins"].initial = (
                    obj.quest_data.reward_starcoins
                )
                form.base_fields["daily_scale_type"].initial = obj.quest_data.scale_type
                form.base_fields["daily_type"].initial = obj.quest_data.type

        return form


class RangsAdmin(admin.ModelAdmin):
    list_display = (
        "level",
        "all_starcoins",
        "_role",
        "emoji",
        "name",
    )
    list_display_links = (
        "level",
        "all_starcoins",
        "_role",
        "emoji",
        "name",
    )
    list_filter = (
        "level",
        "all_starcoins",
        "_role",
    )


class PromocodesForm(forms.ModelForm):

    # Поля из SubscribeQuest
    starcoins_title = forms.CharField(max_length=255, required=False, label="Заголовок")
    starcoins_description = forms.CharField(
        widget=forms.Textarea, required=False, label="Описание"
    )
    starcoins_reward_starcoins = forms.FloatField(
        required=False, label="Вознаграждение"
    )

    class Meta:
        model = Promocodes
        fields = "__all__"


class PromocodesAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "promo_title",
        "type_promo",
        "role",
        "code",
        "active",
        "all_quantity",
        "used_quantity",
        "_expires_at",
    ]
    list_display_links = [
        "id",
        "promo_title",
        "type_promo",
        "all_quantity",
        "used_quantity",
        "_expires_at",
    ]
    list_editable = ["active", "code"]
    list_filter = ["type_promo", "role", "active"]

    def promo_title(self, obj):
        """Возвращает title из связанной модели"""
        if obj.promo_data and hasattr(obj.promo_data, "title"):
            return obj.promo_data.title
        return "-"

    promo_title.short_description = "Название Промика"

    form = PromocodesForm

    def get_fieldsets(self, request, obj=None):
        """Всегда показываем все fieldsets"""
        fieldsets = [
            (
                "Основная информация",
                {
                    "fields": (
                        "type_promo",
                        "role",
                        "code",
                        "active",
                        "all_quantity",
                        "_expires_at",
                    ),
                    "description": '"Роль" и "Действителен до" можно не указывать',
                },
            ),
            (
                "Выдача старкоинов",
                {
                    "fields": (
                        "starcoins_title",
                        "starcoins_description",
                        "starcoins_reward_starcoins",
                    ),
                    "description": '"Описание" можно не заполнять',
                },
            ),
        ]

        return fieldsets

    def save_model(self, request, obj, form, change):
        # Сначала сохраняем основной объект Promocodes
        super().save_model(request, obj, form, change)

        # Всегда создаем/обновляем promo_data в зависимости от type_promo
        self._create_or_update_promo_data(obj, form.cleaned_data)

    def _create_or_update_promo_data(self, promo, cleaned_data):
        """Создает или обновляет объект promo_data с данными из формы"""
        from django.contrib.contenttypes.models import ContentType

        # Если у квеста уже есть связанный объект, но тип изменился - удаляем старый
        if promo.content_type and promo.object_id:
            current_model = promo.content_type.model_class()
            if promo.type_promo == "starcoins" and current_model != StarcoinsPromo:
                # Тип изменился, удаляем старый объект
                current_model.objects.filter(id=promo.object_id).delete()
                promo.object_id = None
                promo.content_type = None

        if promo.type_promo == "starcoins":
            if promo.object_id:
                # Обновляем существующий объект
                promo_data = StarcoinsPromo.objects.get(id=promo.object_id)
                promo_data.title = cleaned_data.get("starcoins_title", "")
                promo_data.description = cleaned_data.get("starcoins_description", "")
                promo_data.reward_starcoins = cleaned_data.get(
                    "starcoins_reward_starcoins", 0
                )
                promo_data.save()
            else:
                # Создаем новый объект
                promo_data = StarcoinsPromo.objects.create(
                    title=cleaned_data.get("starcoins_title", ""),
                    description=cleaned_data.get("starcoins_description", ""),
                    _reward_starcoins=cleaned_data.get("starcoins_reward_starcoins", 0),
                )
                promo.object_id = promo_data.id
                promo.content_type = ContentType.objects.get_for_model(StarcoinsPromo)

        promo.save()

    def get_form(self, request, obj=None, **kwargs):
        """Заполняем форму данными из связанного объекта"""
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.content_type and obj.object_id:
            # Заполняем форму данными из связанного объекта в зависимости от типа квеста
            if obj.type_promo == "starcoins":
                form.base_fields["starcoins_title"].initial = obj.promo_data.title
                form.base_fields["starcoins_description"].initial = (
                    obj.promo_data.description
                )
                form.base_fields["starcoins_reward_starcoins"].initial = (
                    obj.promo_data.reward_starcoins
                )

        return form


class UsePromocodesAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    # Отключаем возможность изменения существующих записей
    def has_change_permission(self, request, obj=None):
        return False

    # Настройка отображения в списке
    list_display = ("id", "user", "promocode")

    # Поля только для чтения (если оставить возможность просмотра деталей)
    readonly_fields = ("user", "promocode")

    search_fields = (
        "user__user_id",
        "user__tg_username",
    )

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


class ManagementLinksAdmin(admin.ModelAdmin):
    list_display = (
        "link",
        "stat",
    )
    list_display_links = (
        "link",
        "stat",
    )

    def link(self, obj):
        if obj:
            return f"https://t.me/happygalaxy_bot?start={obj.code}"
        return "null"

    link.short_description = "Ссылка"

    def stat(self, obj):
        if obj:
            use_manage_links = UseManagementLinks.objects.filter(
                management_link=obj
            ).all()
            users = [use_manage_link.user for use_manage_link in use_manage_links]
            if obj.type_link == "authorised_start":
                start = len(users)
                authorised = len([user for user in users if user.authorised])
                return f"{authorised}/{start}"

        return "null"

    stat.short_description = "Стата"


class AnalyticsSummaryAdmin(admin.ModelAdmin):
    # Отключаем возможность добавления новых записей
    def has_add_permission(self, request):
        return False

    # Отключаем возможность изменения существующих записей
    def has_change_permission(self, request, obj=None):
        return False

    # Убираем кнопки "Добавить" и "Изменить"
    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    list_display = [
        "date",
        "total_user_stats",
        "total_shop_stats",
        "total_quest_stats",
        "total_game_stats",
    ]
    list_filter = ["date"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "date"

    def total_shop_stats(self, obj):
        summary = AnalyticsSummary.objects.get(date=obj.date)
        shop_stats = ShopStats.objects.filter(summary=summary)

        sold = 0
        revenue = 0.0
        unique_buyers = []
        for shop_stat in shop_stats:
            sold += shop_stat.items_sold
            revenue += shop_stat.total_revenue
            unique_buyers.extend(shop_stat.unique_buyers)

        return "{}★ / {}шт / {}users".format(revenue, sold, len(set(unique_buyers)))

    total_shop_stats.short_description = "Сводка по покупкам"

    def total_quest_stats(self, obj):
        summary = AnalyticsSummary.objects.get(date=obj.date)
        quest_stats = QuestStats.objects.filter(summary=summary)

        total_rewards = 0.0
        attempts = 0
        success = 0
        failed = 0
        unique_users = []
        for quest_stat in quest_stats:
            total_rewards += quest_stat.total_rewards
            attempts += quest_stat.attempts
            success += quest_stat.success
            failed += quest_stat.failed
            unique_users.extend(quest_stat.unique_users)

        return "{}★ / {}att / {}t / {}f / {}wait / {}users".format(
            total_rewards,
            attempts,
            success,
            failed,
            attempts - (success + failed),
            len(set(unique_users)),
        )

    total_quest_stats.short_description = "Сводка по квестам"

    def total_game_stats(self, obj):
        summary = AnalyticsSummary.objects.get(date=obj.date)
        quest_stats = GamesStats.objects.filter(summary=summary)

        lumberjack_profit = 0.0
        geohunter_profit = 0.0
        lumberjack_clicks = 0
        geohunter_true = 0
        geohunter_false = 0
        lumberjack_unique_users = []
        geohunter_unique_users = []
        for quest_stat in quest_stats:
            lumberjack_profit += quest_stat.lumberjack_profit
            geohunter_profit += quest_stat.geohunter_profit
            lumberjack_clicks += quest_stat.lumberjack_clicks
            geohunter_true += quest_stat.geohunter_true
            geohunter_false += quest_stat.geohunter_false
            if quest_stat.lumberjack_unique_users:
                lumberjack_unique_users.extend(quest_stat.lumberjack_unique_users)
            if quest_stat.geohunter_unique_users:
                geohunter_unique_users.extend(quest_stat.geohunter_unique_users)

        try:
            geohunt_stat = int(
                geohunter_true * 100 / (geohunter_true + geohunter_false)
            )
        except ZeroDivisionError:
            geohunt_stat = 0

        return "{} + {} = {}★ / {} + {}({}%) = {}clicks  / {} + {} = {}users".format(
            round(lumberjack_profit, 2),
            round(geohunter_profit, 2),
            round((lumberjack_profit + geohunter_profit), 2),
            lumberjack_clicks,
            geohunter_true + geohunter_false,
            geohunt_stat,
            geohunter_true + geohunter_false + lumberjack_clicks,
            len(set(lumberjack_unique_users)),
            len(set(geohunter_unique_users)),
            len(set(lumberjack_unique_users + geohunter_unique_users)),
        )

    total_game_stats.short_description = "Сводка по играм (l + g = all)"

    def total_user_stats(self, obj):
        message_users = (
            MessageAction.objects.filter(summary=obj)
            .values_list("user_id", flat=True)
            .distinct()
        )

        callback_users = (
            CallbackAction.objects.filter(summary=obj)
            .values_list("user_id", flat=True)
            .distinct()
        )

        all_users = len(set(list(message_users) + list(callback_users)))

        return f"{all_users} users"

    total_user_stats.short_description = "Активных пользователей"


class UnifiedUserActionAdmin(admin.ModelAdmin):
    list_display = ("user_id", "timestamp", "action_type", "get_content_preview")
    list_filter = (
        "action_type",
        ("timestamp", admin.DateFieldListFilter),  # Фильтр по дате
    )
    search_fields = ("user_id", "content")
    ordering = ("-timestamp",)  # Сортировка по времени (новые сверху)
    date_hierarchy = "timestamp"  # Навигация по датам
    list_per_page = 50  # Пагинация

    # Поля только для чтения
    readonly_fields = ("user_id", "timestamp", "action_type", "content")

    # Отключаем добавление и изменение
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Кастомные методы для отображения
    def get_content_preview(self, obj):
        """Сокращенное отображение контента"""
        if len(obj.content) > 100:
            return f"{obj.content[:100]}..."
        return obj.content

    get_content_preview.short_description = "Содержание"

    def get_queryset(self, request):
        """Оптимизируем запрос"""
        return super().get_queryset(request).select_related(None)

    # Кастомные действия
    actions = ["export_selected"]

    def export_selected(self, request, queryset):
        """Экспорт выбранных записей"""
        import csv
        import io

        from django.http import HttpResponse

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["User ID", "Timestamp", "Action Type", "Content"])

        for obj in queryset:
            writer.writerow([obj.user_id, obj.timestamp, obj.action_type, obj.content])

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="user_actions.csv"'
        return response

    export_selected.short_description = "Экспортировать выбранные записи в CSV"


admin.site.register(UnifiedUserAction, UnifiedUserActionAdmin)
admin.site.register(AnalyticsSummary, AnalyticsSummaryAdmin)
admin.site.register(Users, UsersAdmin)
admin.site.register(Family_Ties, Family_TiesAdmin)
admin.site.register(Pikmi_Shop, Pikmi_ShopAdmin)
admin.site.register(Purchases, PurchasesAdmin)
admin.site.register(Lumberjack_Game, Lumberjack_GameAdmin)
admin.site.register(GeoHunter, GeoHunterAdmin)
admin.site.register(Sigma_Boosts, Sigma_BoostsAdmin)
admin.site.register(Work_Keys, Work_KeysAdmin)
admin.site.register(Bonuses, BonusesAdmin)
admin.site.register(UseBonuses, UseBonusesAdmin)
admin.site.register(UseQuests, UseQuestsAdmin)
admin.site.register(Quests, QuestsAdmin)
admin.site.register(Rangs, RangsAdmin)
admin.site.register(Promocodes, PromocodesAdmin)
admin.site.register(UsePromocodes, UsePromocodesAdmin)
admin.site.register(ManagementLinks, ManagementLinksAdmin)
