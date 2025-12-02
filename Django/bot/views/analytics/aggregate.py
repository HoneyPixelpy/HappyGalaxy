import io
import json
from datetime import datetime, timedelta, time
import os
import subprocess
from typing import List, Dict, Tuple, Any
from collections import Counter, defaultdict

from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.conf import settings
from loguru import logger

from django.db import transaction
from django.db.models import Count, Min, Max, Avg, F, Q, Prefetch
from django.utils import timezone

from bot.models import AnalyticsSummary, CallbackAction, DailyButtonStats, DailyUserStats, MessageAction



class AggregationData:

    @transaction.atomic
    def process_data(
        self,
        aggregat_data: List[AnalyticsSummary]  # Изменил тип - это QuerySet объектов
        ):
        """
        Агрегируем данные из MessageAction и CallbackAction 
        в DailyUserStats и DailyButtonStats
        """
        logger.info(f"Начало агрегации данных для {len(aggregat_data)} дней")
        
        for summary in aggregat_data:
            logger.info(f"Обработка дня: {summary.date}")
            
            # Получаем данные для этого дня
            messages = getattr(summary, 'prefetched_messages', [])
            callbacks = getattr(summary, 'prefetched_callbacks', [])
            
            if not messages and not callbacks:
                logger.error(f"  Нет данных для дня {summary.date}, пропускаем")
                continue
            
            # 1. Агрегация по пользователям
            self._aggregate_user_stats(summary, messages, callbacks)
            
            # 2. Агрегация по кнопкам
            self._aggregate_button_stats(summary, callbacks)
            
            # 3. Обновляем общую статистику дня
            self._update_summary_stats(summary)
            
            logger.info(f"  ✓ Обработано: {len(messages)} сообщений, {len(callbacks)} колбэков")
    
    def _aggregate_user_stats(
        self,
        summary: AnalyticsSummary,
        messages: List[MessageAction],
        callbacks: List[CallbackAction]
        ) -> None:
        """
        Создаем DailyUserStats для каждого пользователя за день
        """
        user_data = defaultdict(lambda: {
            'messages': [],
            'callbacks': [],
            'message_types': Counter(),
            'button_clicks': Counter(),
            'active_hours': set()
        })
        
        # Обрабатываем сообщения
        for msg in messages:
            user_id = msg.user_id
            user_data[user_id]['messages'].append(msg)
            user_data[user_id]['message_types'][msg.content_type] += 1
            user_data[user_id]['active_hours'].add(msg.timestamp.hour)
        
        # Обрабатываем колбэки
        for cb in callbacks:
            user_id = cb.user_id
            user_data[user_id]['callbacks'].append(cb)
            user_data[user_id]['button_clicks'][(cb.text, cb.data)] += 1
            user_data[user_id]['active_hours'].add(cb.timestamp.hour)
        
        # Создаем записи DailyUserStats
        for user_id, data in user_data.items():
            if not data['messages'] and not data['callbacks']:
                continue
            
            # Временные метрики
            all_actions = data['messages'] + data['callbacks']
            timestamps = [action.timestamp for action in all_actions]
            
            first_action = min(timestamps)
            last_action = max(timestamps)
            
            # Подсчет метрик
            message_count = len(data['messages'])
            callback_count = len(data['callbacks'])
            total_actions = message_count + callback_count
                        
            # Популярные кнопки пользователя
            popular_buttons = [
                {'text': text, 'data': data, 'count': count}
                for (text, data), count in data['button_clicks'].most_common(5)
            ]
            
            # Средняя длина сообщений
            avg_message_length = 0
            if data['messages']:
                avg_message_length = sum(
                    m.message_length for m in data['messages']
                ) / len(data['messages'])
            
            # Часы активности (сортированные)
            active_hours = sorted(list(data['active_hours']))
            
            # Пиковый час активности
            peak_hour = None
            if active_hours:
                # Находим час с максимальным количеством действий
                hour_counts = Counter()
                for action in all_actions:
                    hour_counts[action.timestamp.hour] += 1
                peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else None
            
            # Создаем или обновляем запись
            DailyUserStats.objects.update_or_create(
                summary=summary,
                user_id=user_id,
                defaults={
                    'message_count': message_count,
                    'callback_count': callback_count,
                    'total_actions': total_actions,
                    'avg_message_length': avg_message_length,
                    'message_types': dict(data['message_types']),
                    'first_action': first_action,
                    'last_action': last_action,
                    'active_hours': active_hours,
                    'actions_per_hour': total_actions / max(len(active_hours), 1),
                    'peak_activity_hour': peak_hour,
                    'popular_buttons': popular_buttons
                }
            )
    
    def _aggregate_button_stats(
        self,
        summary: AnalyticsSummary,
        callbacks: List[CallbackAction]
        ) -> None:
        """
        Создаем DailyButtonStats для каждой кнопки за день
        """
        if not callbacks:
            return
        
        # Группируем клики по кнопкам
        button_data = defaultdict(lambda: {
            'clicks': [],
            'users': set(),
            'click_times': []
        })
        
        for cb in callbacks:
            key = (cb.text, cb.data)
            button_data[key]['clicks'].append(cb)
            button_data[key]['users'].add(cb.user_id)
            button_data[key]['click_times'].append(cb.timestamp)
        
        # Создаем записи DailyButtonStats
        for (button_text, button_data_str), data in button_data.items():
            clicks = data['clicks']
            unique_users = len(data['users'])
            total_clicks = len(clicks)
            
            # Временные метрики
            click_timestamps = [cb.timestamp for cb in clicks]
            first_click = min(click_timestamps)
            last_click = max(click_timestamps)
            
            # Часы кликов
            click_hours = [ts.hour for ts in click_timestamps]
            
            # Подсчет повторных пользователей
            user_click_counts = Counter()
            for cb in clicks:
                user_click_counts[cb.user_id] += 1
            
            repeat_users = sum(1 for count in user_click_counts.values() if count > 1)
            
            # Рассчитываем метрики
            click_frequency = total_clicks / unique_users if unique_users > 0 else 0
            user_retention_rate = (repeat_users / unique_users * 100) if unique_users > 0 else 0
            
            # Среднее время до клика (если есть данные о начале сессии)
            avg_time_to_click = None
            
            DailyButtonStats.objects.update_or_create(
                summary=summary,
                button_data=button_data_str,
                defaults={
                    'button_text': button_text,
                    'total_clicks': total_clicks,
                    'unique_users': unique_users,
                    'first_click': first_click,
                    'last_click': last_click,
                    'click_times': click_hours,
                    'click_frequency': click_frequency,
                    'repeat_users': repeat_users,
                    'user_retention_rate': user_retention_rate,
                    'avg_time_to_click': avg_time_to_click
                }
            )
    
    def _update_summary_stats(
        self, 
        summary: AnalyticsSummary
        ) -> None:
        """
        Обновляем общую статистику в AnalyticsSummary
        """
        # Получаем агрегированные данные
        user_stats = DailyUserStats.objects.filter(summary=summary)
        
        # Базовые метрики
        total_users = user_stats.count()
        total_messages = sum(stats.message_count for stats in user_stats)
        total_callbacks = sum(stats.callback_count for stats in user_stats)
        
        summary.total_users = total_users
        summary.total_messages = total_messages
        summary.total_callbacks = total_callbacks
        summary.save()
        
        logger.info(f"  Обновлена статистика дня: {total_users} пользователей, "
              f"{total_messages} сообщений, {total_callbacks} колбэков")        


class ClearData:
    
    @transaction.atomic
    def delete_work_data(
        self, 
        summary_id: List[int]
        ) -> None:
        """
        Удаляем старые данные
        """
        messages_deleted = MessageAction.objects.filter(
            summary_id__in=summary_id
        ).delete()
        callbacks_deleted = CallbackAction.objects.filter(
            summary_id__in=summary_id
        ).delete()
        
        logger.debug(f"🗑️ Удалено: {messages_deleted[0]} сообщений, {callbacks_deleted[0]} колбэков")


class BackupData:
    
    def create_backup(
        self, 
        summary_date: List[str]
        ) -> Response:
        """
        Создает дамп базы данных PostgreSQL через Python с правильной обработкой массивов
        """
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        formatted_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"postgres_backup_{formatted_time}.sql"

        # Создаем дамп средствами Python
        dump_content = self._subprocess_pg_dump(db_host, db_port, db_user, db_password, db_name, summary_date)
        
        response = HttpResponse(
            dump_content,
            content_type='application/sql',
            status=status.HTTP_200_OK
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _subprocess_pg_dump(
        self, 
        db_host: str, 
        db_port: int, 
        db_user: str, 
        db_password: str, 
        db_name: str, 
        summary_date: List[str]
        ) -> bytes:
        """
        Создание дампа средствами Python через psycopg2
        """
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '-t', 'user_message_actions',  # ваша таблица MessageAction
            '-t', 'user_callback_actions', # ваша таблица CallbackAction
            '--data-only',  # Только данные, без схемы
            '--no-owner',
            '--no-privileges',
            '--inserts',  # Использует INSERT вместо COPY (проще читать)
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                env=env,
                capture_output=True, 
                text=True,
                check=True
            )
            
            filtered_lines = []
            
            for line in result.stdout.split('\n'):
                if (
                    line.startswith('INSERT') and 
                    not any(date in line for date in summary_date)
                    ):
                    continue
                        
                filtered_lines.append(line)
            
            return '\n'.join(filtered_lines).encode('utf-8')
            
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            raise


class AdvancedStatsAggregator(AggregationData, BackupData, ClearData):
    
    def get_old_summaries(
        self,
        cutoff_date: datetime
        ) -> List[AnalyticsSummary]:
        """
        Вытаскиваем связанные AnalyticsSummary на каждый день 
        старше 7 дней без user_stats или button_stats
        """
        return AnalyticsSummary.objects.filter(
            date__lt=cutoff_date
        ).exclude(
            # Исключаем записи, у которых уже есть агрегированные данные
            user_stats__isnull=False  # или button_stats__isnull=False
        ).distinct().order_by('date')#.values_list('id', flat=True)
        
    def get_data(
        self,
        summary_id: List[int]
        ) -> List[Dict[str, Any]]:
        """
        Вытаскиваем интересующие данные
        """
        return AnalyticsSummary.objects.filter(
            id__in=summary_id
        ).prefetch_related(
            Prefetch(
                'message_actions',
                queryset=MessageAction.objects.all(),
                to_attr='prefetched_messages'
            ),
            Prefetch(
                'callback_action',
                queryset=CallbackAction.objects.all(),
                to_attr='prefetched_callbacks'
            )
        )
    
    @logger.catch
    def aggregate_stats(
        self,
        cutoff_date: datetime
        ) -> Response:
        """
        Процесс агрегации данных
        """
        if os.getenv('DEBUG'):
            cutoff_date = timezone.now().date() + timedelta(days=1)
            
        logger.debug(f"📊 Вычисляем статистику до {cutoff_date}")
        
        # 1. Получаем AnalyticsSummary за последние 7 дней так как к ней крепется вся стата за каждый день
        old_summaries = self.get_old_summaries(cutoff_date)
        if not old_summaries:
            return Response(
                data={
                    'message': 'Нет статистики за последние 7 дней'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        summary_id = [s.id for s in old_summaries]
        logger.debug(f"📊 ИД статистики: {summary_id}")
        
        # 2. Вытаскиваем все действия для агрегации
        aggregat_data = self.get_data(summary_id)
        if not aggregat_data:
            return Response(
                data={
                    'message': 'Нет данных для агрегации'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 3. Агрегируем данные (из идних данных создаем другие, которые более легкие)
        super().process_data(aggregat_data)
        
        # 4. Создаем резервную копию того что агрегировали
        response_backup = super().create_backup(
            [s.date.strftime('%Y-%m-%d') for s in old_summaries]
            )
        
        # 5. Удаляем старые данные
        super().delete_work_data(summary_id)
        
        return response_backup


