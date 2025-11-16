from datetime import timedelta
from typing import Any, List, Optional, Union
from loguru import logger
import pytz

from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from ..models import QuestModerationAttempt, Quests, Rangs, SubscribeQuest, UseQuests, Users
from ..serializers import DailyQuestsSerializer, IdeaQuestsSerializer, QuestsSerializer, SubscribeQuestSerializer, UserSerializer
from .error import RaisesResponse


class QuestMethods:
    @classmethod
    def all(
        cls
        ) -> List[Quests]:
        return Quests.objects.all()
    @classmethod
    def get(
        cls,
        pk: int
        ) -> Quests:
        try:
            if pk:
                return Quests.objects.get(pk=pk)
        except Quests.DoesNotExist:
            raise RaisesResponse(
                data={'error': 'Quests not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    @classmethod
    def get_sub_quests_by_chat(
        chat_id_name: Any
        ) -> Union[Response, List[SubscribeQuest]]:        
        # Находим ID всех SubscribeQuest с нужным chat_id_name
        subscribe_quest_ids = SubscribeQuest.objects.filter(
            chat_id_name=chat_id_name
        ).values_list('id', flat=True)
        
        if not subscribe_quest_ids:
            raise RaisesResponse(
                data={'error': 'No subscribe quest found with this chat_id_name'},
                status=status.HTTP_404_NOT_FOUND
            )
        else:
            return subscribe_quest_ids
    @classmethod
    def get_info(
        cls,
        user: Users,
        quest: Quests
        ) -> Response:
        serializer = QuestsSerializer(quest).data
        
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_date = timezone.now().astimezone(moscow_tz).date()
        user_quests = UseQuests.objects.filter(user=user, quest=quest).first()
        if user_quests:
            last_update_date = user_quests.updated_at.astimezone(moscow_tz).date()
            if quest.type_quest in ["idea", "daily"]:
                if quest.type_quest == "daily":
                    if current_date <= last_update_date:
                        raise RaisesResponse(
                            data="Квест уже был использован сегодня",
                            status=status.HTTP_404_NOT_FOUND
                        )
            
                count_use: Optional[int] = quest.quest_data.count_use
                
                if count_use:
                    attempt = QuestModerationAttempt.objects.filter(
                        use_quest=user_quests,
                        moderation_status='pending'
                    ).all()
                    if attempt:
                        user_quests.count_use += len(attempt)
                        
                    if count_use <= user_quests.count_use:
                        raise RaisesResponse(
                            data="Квест уже был использован столько раз сколько разрешено",
                            status=status.HTTP_404_NOT_FOUND
                        )
                
            else:
                raise RaisesResponse(
                    data="Квест уже был использован",
                    status=status.HTTP_404_NOT_FOUND
                )
        
        try: # NOTE это для того чтобы возвращать правильное вознаграждение для "x_count_use"
            if quest.quest_data.scale_type == "x_count_use":
                if user_quests and quest.type_quest == "daily":
                    days_passed = (current_date - last_update_date).days
                    
                    count_use: Optional[int] = user_quests.count_use
                    result_count_use: Optional[int] = count_use
                    
                    if days_passed == 1:
                        # Ровно 1 день прошел - увеличиваем счетчик
                        result_count_use += 1
                    elif days_passed > 1:
                        # Пропущен день или больше - сбрасываем счетчик
                        result_count_use = 1
                    else:
                        # Меньше дня прошло - квест уже выполнен сегодня
                        raise RaisesResponse(
                            data={'error': 'Quest already completed today'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                    serializer = dict(serializer)
                    serializer['quest_data']['_reward_starcoins'] = quest.quest_data.reward_starcoins * result_count_use
        except AttributeError:
            pass
        # except Exception:
        #     logger.exception("QuestsViewSet.retrieve")
        
        raise RaisesResponse(
            data=serializer,
            status=status.HTTP_200_OK
            )
    @classmethod
    def active(
        cls,
        user: Users,
        rang: Rangs
        ) -> Response:
        quests = []
        
        # Сначала получаем все подходящие квесты
        filtered_quests = Quests.objects.filter(
            active=True,
            min_rang_level__lte=rang.level,
            max_rang_level__gte=rang.level
        ).filter(
            Q(role=user._role) | Q(role__isnull=True)
        ).select_related('content_type')

        # Сортируем в Python после получения всех данных
        sorted_quests = sorted(
            filtered_quests,
            key=lambda x: (
                {'subscribe': 1, 'daily': 2, 'idea': 3}.get(x.type_quest, 4),
                -getattr(getattr(x, 'quest_data', None), 'reward_starcoins', 0) if hasattr(x, 'quest_data') and x.quest_data else 0
            )
        )
        
        for quest in sorted_quests:
            user_quests = UseQuests.objects.filter(user=user, quest=quest).first()
            if not user_quests:
                quests.append(quest)
            
            elif quest.type_quest in ["idea", "daily"]:
                count_use: Optional[int] = quest.quest_data.count_use
                
                if count_use:
                    attempt = QuestModerationAttempt.objects.filter(
                        use_quest=user_quests,
                        moderation_status='pending'
                    ).all()
                    if attempt:
                        user_quests.count_use += len(attempt)
                    
                    if count_use <= user_quests.count_use:
                        continue
                
                if quest.type_quest == "daily":
                    moscow_tz = pytz.timezone('Europe/Moscow')
                    last_update_date = user_quests.updated_at.astimezone(moscow_tz).date()
                    current_date = timezone.now().astimezone(moscow_tz).date()
                    if current_date <= last_update_date:
                        continue

                quests.append(quest)

        serializer = QuestsSerializer(quests, many=True)
        raise RaisesResponse(
            data=serializer.data,
            status=status.HTTP_200_OK
            )


class UseQuestMethods:
    @classmethod
    def get(
        cls,
        user: Users,
        quest: Quests
        ) -> Response:
        try:
            return UseQuests.objects.get(user=user, quest=quest)
        except UseQuests.DoesNotExist:
            raise RaisesResponse(
                data={'error': 'UseQuest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    @classmethod
    def get_quests(
        cls,
        user: Users,
        quest: Quests
        ) -> Response:
        user_quests = UseQuests.objects.filter(user=user, quest=quest).first()
        if user_quests and quest.type_quest == "idea":
            count_use: Optional[int] = quest.quest_data.count_use
            
            if count_use:
                if count_use <= user_quests.count_use:
                    raise RaisesResponse(
                        data=True,
                        status=status.HTTP_200_OK
                        )
                
            raise RaisesResponse(
                data=False,
                status=status.HTTP_200_OK
                )

        raise RaisesResponse(
            data=bool(user_quests),
            status=status.HTTP_200_OK
            )
    @classmethod
    def create(
        cls,
        user: Users,
        quest: Quests
        ) -> Response:
        use_quest_obj = UseQuests.objects.filter(user=user, quest=quest).first()
        if use_quest_obj:
            if quest.type_quest == "idea":
                count_use: Optional[int] = quest.quest_data.count_use
                
                if count_use:
                    if count_use > use_quest_obj.count_use:
                        use_quest_obj.count_use +=1
                        use_quest_obj.save()
                    else:
                        raise RaisesResponse(
                            data={'error': 'This quest is already assigned to the user'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            else:
                raise RaisesResponse(
                    data={'error': 'This quest is already assigned to the user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        UseQuests.objects.create(user=user, quest=quest)
        
        dop_quest = quest.quest_data
        reward = dop_quest.reward_starcoins
        user.starcoins += reward
        user.save()
        
        if quest.type_quest == "idea":
            serializer = IdeaQuestsSerializer(dop_quest)
        elif quest.type_quest == "subscribe":
            serializer = SubscribeQuestSerializer(dop_quest)
        elif quest.type_quest == "daily":
            serializer = DailyQuestsSerializer(dop_quest)
        
        raise RaisesResponse(
            data=serializer.data, 
            status=status.HTTP_201_CREATED
            )
    @classmethod
    def create_idea_daily(
        cls,
        user: Users,
        quest: Quests
        ) -> Response:
        use_quest_obj = UseQuests.objects.filter(user=user, quest=quest).first()
        
        if use_quest_obj:
            if quest.type_quest in ["idea","daily"]:
                moscow_tz = pytz.timezone('Europe/Moscow')
                last_update_date = use_quest_obj.updated_at.astimezone(moscow_tz).date()
                current_date = timezone.now().astimezone(moscow_tz).date()
                days_passed = (current_date - last_update_date).days
                
                count_use: Optional[int] = quest.quest_data.count_use
                
                # Если интервал истек, сбрасываем счетчик
                if quest.type_quest == "daily":
                    if days_passed == 1:
                        # Ровно 1 день прошел - увеличиваем счетчик
                        use_quest_obj.count_use += 1
                        use_quest_obj.save()
                    elif days_passed > 1:
                        # Пропущен день или больше - сбрасываем счетчик
                        use_quest_obj.count_use = 1
                        use_quest_obj.save()
                    else:
                        # Меньше дня прошло - квест уже выполнен сегодня
                        raise RaisesResponse(
                            data={'error': 'Quest already completed today'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                elif count_use:
                    if count_use > use_quest_obj.count_use:
                        use_quest_obj.count_use +=1
                        use_quest_obj.save()
                    else:
                        raise RaisesResponse(
                            data={'error': 'This quest is already assigned to the user'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    use_quest_obj.count_use +=1
                    use_quest_obj.save()
            else:
                raise RaisesResponse(
                    data={'error': 'This quest is already assigned to the user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            use_quest_obj = UseQuests.objects.create(user=user, quest=quest)
        
        # Расчет награды
        if not quest.success_admin:                
            if (quest.type_quest == "daily" and 
                quest.quest_data.scale_type == 'x_count_use'
                ):
                add_starcoins = quest.quest_data.reward_starcoins * use_quest_obj.count_use
            else:
                add_starcoins = quest.quest_data.reward_starcoins
                
            user.starcoins += add_starcoins
            user.save()
            result = add_starcoins
        else:
            QuestModerationAttempt.objects.create(
                use_quest=use_quest_obj,
                attempt_number=use_quest_obj.count_use
            )
            result = True
        
        # NOTE число будет означать что за квест сразу расчитались и нужно уведомить пользователя об выигрыше
        raise RaisesResponse(
            data=result, 
            status=status.HTTP_201_CREATED
            )
    @classmethod
    def sub_tg_chat(
        cls,
        quest: Quests
        ) -> Response:
        users = [use_quest.user for use_quest in UseQuests.objects.filter(
            quest=quest
            )]
        
        raise RaisesResponse(
            data=UserSerializer(users, many=True).data,
            status=status.HTTP_200_OK
            )
    @classmethod
    def sub_vk_chat(
        cls,
        quest: Quests
        ) -> Response:
        users = [use_quest.user for use_quest in UseQuests.objects.filter(
            quest=quest
            ) if use_quest.user.vk_id]
        
        raise RaisesResponse(
            data=UserSerializer(users, many=True).data,
            status=status.HTTP_200_OK
            )
    @classmethod
    def back_tg_quest(
        cls,
        user: Users,
        quest: Quests,
        use_quest: UseQuests
        ) -> Response:
        user.all_starcoins -= quest.quest_data.reward_starcoins
        user.starcoins -= quest.quest_data.reward_starcoins
        user.save()
        
        use_quest.delete()
        
        logger.info(
            f"Сняли за отпуску ТГ {quest.quest_data.reward_starcoins} у {user}"
        )
        
        raise RaisesResponse(
            data=True, 
            status=status.HTTP_200_OK
            )

class Quest_MA_Methods:
    @classmethod
    def success_idea_daily(
        cls, 
        user: Users, 
        quest: Quests,
        use_quest_obj: UseQuests
        ) -> Response:
        # NOTE создаем связь на случай если она не была создана, но такого не может быть
        attempt = QuestModerationAttempt.objects.filter(
            use_quest=use_quest_obj,
            moderation_status='pending'
        ).order_by('id').first()
        logger.debug(f"success_idea_daily {attempt=}")
        
        if not attempt:
            raise RaisesResponse(
                data={'error': 'Этот квест не в ожидании действий от модератора'},
                status=status.HTTP_404_NOT_FOUND
            )
        attempt.moderation_status = 'approved'
        attempt.save()

        # Расчет награды
        if (quest.type_quest == "daily" and 
            quest.quest_data.scale_type == 'x_count_use'
            ):
            add_starcoins = quest.quest_data.reward_starcoins * use_quest_obj.count_use
        else:
            add_starcoins = quest.quest_data.reward_starcoins
            
        user.starcoins += add_starcoins
        user.save()
        
        logger.debug(f"success_idea_daily +{add_starcoins} -> {attempt=}")
        raise RaisesResponse(
            data=add_starcoins, 
            status=status.HTTP_200_OK
            )
    @classmethod
    def delete_idea(
        cls,
        quest: Quests,
        use_quest_obj: UseQuests
        ) -> Response:
        attempt = QuestModerationAttempt.objects.filter(
            use_quest=use_quest_obj,
            moderation_status='pending'
        ).order_by('id').first()
        logger.debug(f"delete_idea {attempt=}")
        
        if not attempt:
            raise RaisesResponse(
                data={'error': 'Этот квест не в ожидании действий от модератора'},
                status=status.HTTP_404_NOT_FOUND
            )
        attempt.moderation_status = 'rejected'
        attempt.save()
        
        if quest.type_quest in ["idea", "daily"]:
            use_quest_obj.count_use -= 1
            if use_quest_obj.count_use:
                if quest.type_quest == "daily":
                    use_quest_obj.updated_at = use_quest_obj.updated_at - timedelta(days=1)
                    use_quest_obj.save(skip_auto_now=True)
                else:
                    use_quest_obj.save()
            else:
                use_quest_obj.delete()
            
        raise RaisesResponse(
            data={'type_quest': quest.type_quest, 'title': quest.quest_data.title}, 
            status=status.HTTP_200_OK
            )
    @classmethod
    def delete_old_quest(
        cls
        ) -> Response:
        cutoff_time = timezone.now() - timedelta(days=3)
        logger.debug(cutoff_time)
        
        # Находим все просроченные попытки
        old_attempts = QuestModerationAttempt.objects.filter(
            moderation_status='pending',
            created_at__lte=cutoff_time
        ).all()
        
        data = []
        for attempt in old_attempts:
            try:
                if "SMM" in attempt.use_quest.quest.quest_data.title: continue
                # Обновляем статус попытки
                attempt.moderation_status = 'auto_rejected'
                attempt.save()
                # attempt.delete()
                
                data.append(
                    {
                        'user_id': attempt.use_quest.user.user_id,
                        'quest_id': attempt.use_quest.quest.id,
                        'type_quest': attempt.use_quest.quest.type_quest,
                        'title': attempt.use_quest.quest.quest_data.title
                    }
                )
                if attempt.use_quest.count_use:
                    attempt.use_quest.count_use -= 1
                
                if attempt.use_quest.count_use:
                    if attempt.use_quest.quest.type_quest == "daily":
                        attempt.use_quest.updated_at = attempt.use_quest.updated_at - timedelta(days=1)
                        attempt.use_quest.save(skip_auto_now=True)
                    else:
                        attempt.use_quest.save()
                else:
                    attempt.use_quest.delete()
                
            except Exception as e:
                logger.exception(f"Error auto-rejecting attempt {attempt.id}: {e.__class__.__name__} {e}")
                continue

        raise RaisesResponse(
            data=data, 
            status=status.HTTP_200_OK
            )
