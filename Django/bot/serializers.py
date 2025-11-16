from datetime import datetime
from loguru import logger
from rest_framework import serializers
from bot.models import AddStarcoinsBonus, Bonuses, ClickScaleBonus, DailyQuests, EnergyRenewalBonus, GameData, GeoHunter, IdeaQuests, InteractiveGames, Lumberjack_Game, Pikmi_Shop, Quests, Rangs, Sigma_Boosts, StarcoinsPromo, SubscribeQuest, UseBonuses, UsePromocodes, UseQuests, Users, Purchases, Family_Ties, Work_Keys



class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def create(self, validated_data):
        validated_data['created_at'] = datetime.now()
        validated_data['updated_at'] = datetime.now()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['updated_at'] = datetime.now()
        return super().update(instance, validated_data)


class UserSerializer(BaseSerializer):
    # Явно объявляем вычисляемые поля
    authorised_at = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    role_private = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    starcoins = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            '_authorised_at': {'write_only': True},
            '_age': {'write_only': True},
            '_role': {'write_only': True},
            '_nickname': {'write_only': True},
            '_starcoins': {'write_only': True}
        }

    def get_authorised_at(self, obj):
        return obj.authorised_at

    def get_age(self, obj):
        return obj.age

    def get_role(self, obj):
        return obj.role

    def get_role_name(self, obj):
        return obj.role_name

    def get_role_private(self, obj):
        return obj._role

    def get_nickname(self, obj):
        return obj._nickname

    def get_starcoins(self, obj):
        return obj.starcoins

    def to_representation(self, instance):
        """Основной метод преобразования данных"""
        representation = super().to_representation(instance)
        
        # Удаляем приватные поля из вывода
        for field in ['_authorised_at', '_age', '_role', '_nickname', '_starcoins']:
            representation.pop(field, None)
            
        return representation


class FamilyTiesSerializer(BaseSerializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Family_Ties
        fields = ['id', 'from_user', 'to_user', 'created_at', 'from_user', 'to_user']
        extra_kwargs = {
            'from_user': {'write_only': True},
            'to_user': {'write_only': True}
        }

    def get_from_user(self, obj):
        return UserSerializer(obj.from_user).data

    def get_to_user(self, obj):
        return UserSerializer(obj.to_user).data


class PurchasesSerializer(BaseSerializer):
    # Вычисляемые поля для замены приватных атрибутов
    purchase_date = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Purchases
        fields = '__all__'

    def get_purchase_date(self, obj):
        return obj.purchase_date  # Используем геттер Django

    def get_completed_at(self, obj):
        return obj.completed_at  # Используем геттер Django

    def get_cost(self, obj):
        return obj.cost  # Используем геттер Django

    def get_user(self, obj):
        return UserSerializer(obj.user).data

    def to_representation(self, instance):
        """Преобразование данных перед отправкой"""
        representation = super().to_representation(instance)
        
        # Удаляем приватные поля из вывода
        for field in ['_purchase_date', '_completed_at', '_cost']:
            representation.pop(field, None)
            
        return representation


class PikmiShopSerializer(BaseSerializer):
    # Вычисляемые поля для замены приватных атрибутов
    price = serializers.SerializerMethodField()
    
    class Meta:
        model = Pikmi_Shop
        fields = ['id', 'title', 'description', 'price', 'role', 'quantity']
        extra_kwargs = {
            '_price': {'write_only': True}  # Скрываем приватное поле
        }

    def get_price(self, obj):
        return obj.price  # Используем геттер Django

    def to_representation(self, instance):
        """Преобразование данных перед отправкой"""
        representation = super().to_representation(instance)
        representation.pop('_price', None)  # Удаляем приватное поле
        return representation

    def to_internal_value(self, data):
        """Преобразование входящих данных"""
        if 'price' in data:
            data['_price'] = data.pop('price')  # Преобразуем price → _price
        return super().to_internal_value(data)


class SigmaBoostsSerializer(BaseSerializer):
    last_passive_claim = serializers.SerializerMethodField()
    user_data = serializers.SerializerMethodField()

    class Meta:
        model = Sigma_Boosts
        fields = [
            'id', 'user', 'user_data',
            'income_level', 'energy_capacity_level',
            'recovery_level', 'passive_income_level',
            'last_passive_claim'
        ]
        extra_kwargs = {
            '_last_passive_claim': {'write_only': True},
            'user': {'write_only': True}
        }

    def get_last_passive_claim(self, obj):
        return obj.last_passive_claim  # Используем геттер Django

    def get_user_data(self, obj):
        return UserSerializer(obj.user).data

    def to_representation(self, instance):
        """Преобразование данных перед отправкой"""
        representation = super().to_representation(instance)
        representation.pop('_last_passive_claim', None)  # Удаляем приватное поле
        return representation

    def to_internal_value(self, data):
        """Преобразование входящих данных"""
        if 'last_passive_claim' in data:
            data['_last_passive_claim'] = data.pop('last_passive_claim')
        return super().to_internal_value(data)


class LumberjackGameSerializer(BaseSerializer):
    last_energy_update = serializers.SerializerMethodField()
    total_currency = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Lumberjack_Game
        fields = '__all__'

    def get_last_energy_update(self, obj):
        return obj.last_energy_update  # Используем геттер Django

    def get_total_currency(self, obj):
        return obj.total_currency  # Используем геттер Django

    def get_user(self, obj):
        return UserSerializer(obj.user).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('_last_energy_update', None)
        representation.pop('_total_currency', None)
        return representation

    def to_internal_value(self, data):
        if 'last_energy_update' in data:
            data['_last_energy_update'] = data.pop('last_energy_update')
        if 'total_currency' in data:
            data['_total_currency'] = data.pop('total_currency')
        return super().to_internal_value(data)


class GeoHunterSerializer(BaseSerializer):
    last_energy_update = serializers.SerializerMethodField()
    total_currency = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = GeoHunter
        fields = '__all__'

    def get_last_energy_update(self, obj):
        return obj.last_energy_update  # Используем геттер Django

    def get_total_currency(self, obj):
        return obj.total_currency  # Используем геттер Django

    def get_user(self, obj):
        return UserSerializer(obj.user).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('_last_energy_update', None)
        representation.pop('_total_currency', None)
        return representation

    def to_internal_value(self, data):
        if 'last_energy_update' in data:
            data['_last_energy_update'] = data.pop('last_energy_update')
        if 'total_currency' in data:
            data['_total_currency'] = data.pop('total_currency')
        return super().to_internal_value(data)


class WorkKeysSerializer(BaseSerializer):
    from_user_data = serializers.SerializerMethodField()

    class Meta:
        model = Work_Keys
        fields = ['id', 'key', 'from_user', 'from_user_data']
        extra_kwargs = {
            'from_user': {'write_only': True}
        }

    def get_from_user_data(self, obj):
        if not obj.from_user:
            return None
        return UserSerializer(obj.from_user).data


class AddStarcoinsBonusSerializer(BaseSerializer):
    value = serializers.SerializerMethodField()
    
    class Meta:
        model = AddStarcoinsBonus
        fields = ['id', 'value', 'use_quantity', 'max_quantity']
        extra_kwargs = {
            '_value': {'write_only': True}
        }
    
    def get_value(self, obj):
        return obj.value


class ClickScaleBonusSerializer(BaseSerializer):
    value = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = ClickScaleBonus
        fields = ['id', 'value', 'duration_hours']
        extra_kwargs = {
            '_value': {'write_only': True},
            '_duration_hours': {'write_only': True}
        }
    
    def get_value(self, obj):
        return obj.value
    
    def get_duration_hours(self, obj):
        return obj.duration_hours


class EnergyRenewalBonusSerializer(BaseSerializer):
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = EnergyRenewalBonus
        fields = ['id', 'duration_hours']
        extra_kwargs = {
            '_duration_hours': {'write_only': True}
        }
    
    def get_duration_hours(self, obj):
        return obj.duration_hours


class BonusesSerializer(BaseSerializer):
    bonus_data = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Bonuses
        fields = [
            'id', 'content_type', 'object_id', 'bonus_data',
            'type_bonus', 'active', 'expires_at'
        ]
        extra_kwargs = {
            '_expires_at': {'write_only': True}
        }
    
    def get_bonus_data(self, obj):
        if obj.type_bonus == 'add_starcoins':
            serializer = AddStarcoinsBonusSerializer(obj.bonus_data)
        elif obj.type_bonus == 'click_scale':
            serializer = ClickScaleBonusSerializer(obj.bonus_data)
        elif obj.type_bonus == 'energy_renewal':
            serializer = EnergyRenewalBonusSerializer(obj.bonus_data)
        else:
            return None
        return serializer.data
    
    def get_expires_at(self, obj):
        return obj.expires_at
    
    def to_internal_value(self, data):
        if 'expires_at' in data:
            data['_expires_at'] = data.pop('expires_at')
        return super().to_internal_value(data)


class UseBonusesSerializer(BaseSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    bonus = serializers.PrimaryKeyRelatedField(queryset=Bonuses.objects.all())
    
    class Meta:
        model = UseBonuses
        fields = ['id', 'user', 'bonus']


class SubscribeQuestSerializer(BaseSerializer):
    reward_starcoins = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscribeQuest
        fields = '__all__'
    
    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins


class IdeaQuestsSerializer(BaseSerializer):
    reward_starcoins = serializers.SerializerMethodField()
    
    class Meta:
        model = IdeaQuests
        fields = '__all__'
    
    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins


class DailyQuestsSerializer(BaseSerializer):
    reward_starcoins = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyQuests
        fields = '__all__'
    
    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins


class QuestsSerializer(BaseSerializer):
    quest_data = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Quests
        fields = '__all__'
    
    def get_quest_data(self, obj):
        if obj.type_quest == 'subscribe':
            serializer = SubscribeQuestSerializer(obj.quest_data)
            return serializer.data
        elif obj.type_quest == 'idea':
            serializer = IdeaQuestsSerializer(obj.quest_data)
            return serializer.data
        elif obj.type_quest == 'daily':
            serializer = DailyQuestsSerializer(obj.quest_data)
            return serializer.data
        return None
    
    def get_expires_at(self, obj):
        return obj.expires_at
    
    def to_internal_value(self, data):
        if 'expires_at' in data:
            data['_expires_at'] = data.pop('expires_at')
        return super().to_internal_value(data)


class UseQuestsSerializer(BaseSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    quest = serializers.PrimaryKeyRelatedField(queryset=Quests.objects.all())
    
    class Meta:
        model = UseQuests
        fields = ['id', 'user', 'quest']


class RangsSerializer(BaseSerializer):
    # Явно объявляем вычисляемые поля
    role = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    role_private = serializers.SerializerMethodField()

    class Meta:
        model = Rangs
        fields = '__all__'

    def get_role(self, obj):
        return obj.role

    def get_role_name(self, obj):
        return obj.role_name

    def get_role_private(self, obj):
        return obj._role


class StarcoinsPromoSerializer(BaseSerializer):
    reward_starcoins = serializers.SerializerMethodField()
    
    class Meta:
        model = StarcoinsPromo
        fields = '__all__'
    
    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins


class InteractiveGamesSerializer(BaseSerializer):
    reward_starcoins = serializers.SerializerMethodField()
    user = UserSerializer()
    start_invite_at = serializers.SerializerMethodField()
    start_game_at = serializers.SerializerMethodField()
    ended_game_at = serializers.SerializerMethodField()
    
    class Meta:
        model = InteractiveGames
        fields = '__all__'

    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins
    
    def get_start_invite_at(self, obj):
        return obj.start_invite_at
    
    def get_start_game_at(self, obj):
        return obj.start_game_at
    
    def get_ended_game_at(self, obj):
        return obj.ended_game_at
    
    # def get_user(self, obj):
    #     return UserSerializer(obj.user).data


class GameDataSerializer(BaseSerializer):
    user = UserSerializer()
    game = InteractiveGamesSerializer()
    reward_starcoins = serializers.SerializerMethodField()
    
    class Meta:
        model = GameData
        fields = '__all__'

    def get_reward_starcoins(self, obj):
        return obj.reward_starcoins
    
    # def get_user(self, obj):
    #     return UserSerializer(obj.user).data
    
    # def get_game(self, obj):
    #     return InteractiveGamesSerializer(obj.game).data



