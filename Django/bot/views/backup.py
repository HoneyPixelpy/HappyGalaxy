import abc
import os
import json
import subprocess
import psycopg2
from io import StringIO
import shutil
import tempfile
from datetime import datetime, timedelta, date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from django.http import HttpResponse
from django.conf import settings
from loguru import logger

from rest_framework import status
from rest_framework.response import Response


class CopyBaseAbstractMethods(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def copy_base(self):
        pass

class SQLiteMethods(CopyBaseAbstractMethods):

    def copy_base(self) -> Response:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as tmp_file:
            backup_path = tmp_file.name
        
        DB_PATH = settings.BASE_DIR / 'db.sqlite3'
        
        # Копируем базу данных
        shutil.copy2(DB_PATH, backup_path)
        
        # Читаем содержимое
        with open(backup_path, 'rb') as f:
            content = f.read()
        
        # Удаляем временный файл
        os.remove(backup_path)
        
        # Формируем имя файла с датой
        formatted_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"db_backup_{formatted_time}.sqlite3"
        
        # Создаем правильный ответ с заголовками
        response = HttpResponse(
            content,
            content_type='application/x-sqlite3',
            status=status.HTTP_200_OK
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(content)
        
        return response

class PostgreSQLMethods(CopyBaseAbstractMethods):

    def copy_base(self) -> Response:
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
        dump_content = self._subprocess_pg_dump(db_host, db_port, db_user, db_password, db_name)
        # dump_content = self._create_python_dump(db_host, db_port, db_user, db_password, db_name)
        
        response = HttpResponse(
            dump_content,
            content_type='application/sql',
            status=status.HTTP_200_OK
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _subprocess_pg_dump(self, db_host, db_port, db_user, db_password, db_name):
        """Создание дампа средствами Python через psycopg2"""
        # Устанавливаем переменные окружения для пароля
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Команда pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', db_port,
            '-U', db_user,
            '-d', db_name,
            '--no-owner',
            '--no-privileges',
            '--clean',  # Добавляет DROP TABLE
            '--if-exists'
        ]
        
        try:
            # Выполняем pg_dump
            result = subprocess.run(
                cmd, 
                env=env,
                capture_output=True, 
                text=True,
                check=True
            )
            
            return result.stdout.encode('utf-8')
            
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            raise

    # def _create_python_dump(self, host, port, user, password, dbname):
    #     """Создание дампа средствами Python через psycopg2"""
    #     conn = psycopg2.connect(
    #         host=host,
    #         port=port,
    #         user=user,
    #         password=password,
    #         database=dbname
    #     )
        
    #     # Устанавливаем правильную кодировку для массивых данных
    #     conn.set_client_encoding('UTF8')
        
    #     dump = StringIO()
    #     cursor = conn.cursor()
        
    #     try:
    #         # Заголовок дампа
    #         dump.write(f"-- PostgreSQL database dump\n")
    #         dump.write(f"-- Database: {dbname}\n")
    #         dump.write(f"-- Dumped at: {datetime.now()}\n\n")
            
    #         # Устанавливаем правильный формат для массивых данных
    #         cursor.execute("SET bytea_output = 'escape';")
            
    #         # Получаем список таблиц
    #         cursor.execute("""
    #             SELECT table_name 
    #             FROM information_schema.tables 
    #             WHERE table_schema = 'public' 
    #             AND table_type = 'BASE TABLE'
    #             ORDER BY table_name
    #         """)
            
    #         tables = [row[0] for row in cursor.fetchall()]
            
    #         for table in tables:
    #             self._dump_table(cursor, dump, table)
            
    #         return dump.getvalue().encode('utf-8')
            
    #     finally:
    #         cursor.close()
    #         conn.close()

    # def _dump_table(self, cursor, dump, table_name):
    #     """Дамп конкретной таблицы с правильной обработкой массивов"""
    #     try:
    #         # Получаем информацию о колонках и их типах
    #         cursor.execute("""
    #             SELECT column_name, data_type, udt_name, is_nullable, column_default
    #             FROM information_schema.columns 
    #             WHERE table_name = %s 
    #             ORDER BY ordinal_position
    #         """, (table_name,))
            
    #         columns_info = cursor.fetchall()
            
    #         # DROP TABLE
    #         dump.write(f"DROP TABLE IF EXISTS \"{table_name}\" CASCADE;\n")
            
    #         # CREATE TABLE
    #         dump.write(f"CREATE TABLE \"{table_name}\" (\n")
            
    #         column_defs = []
    #         for col_info in columns_info:
    #             col_name, data_type, udt_name, is_nullable, col_default = col_info
    #             null_def = " NOT NULL" if is_nullable == 'NO' else ""
    #             default_def = f" DEFAULT {col_default}" if col_default else ""
    #             column_defs.append(f"    \"{col_name}\" {data_type}{null_def}{default_def}")
            
    #         dump.write(",\n".join(column_defs))
    #         dump.write("\n);\n\n")
            
    #         # Данные таблицы
    #         column_names = [col[0] for col in columns_info]
    #         column_types = [col[2] for col in columns_info]  # UDT names для определения массивов
            
    #         col_names_str = ", ".join([f'"{col}"' for col in column_names])
            
    #         cursor.execute(f'SELECT * FROM "{table_name}"')
    #         rows = cursor.fetchall()
            
    #         if rows:
    #             for row in rows:
    #                 values = []
    #                 for i, value in enumerate(row):
    #                     values.append(self._format_value(value, column_types[i]))
                    
    #                 values_str = ", ".join(values)
    #                 dump.write(f'INSERT INTO "{table_name}" ({col_names_str}) VALUES ({values_str});\n')
                
    #             dump.write("\n")
                
    #     except Exception as e:
    #         logger.error(f"Ошибка при дампе таблицы {table_name}: {str(e)}")
    #         raise

    # def _format_value(self, value, data_type):
    #     """Правильное форматирование значений для SQL, особенно массивов"""
    #     if value is None:
    #         return "NULL"
        
    #     # Обработка массивов (типы, начинающиеся с _)
    #     elif data_type and data_type.startswith('_'):
    #         return self._format_array_value(value, data_type)
        
    #     # Обработка JSON и подобных типов
    #     elif data_type in ('json', 'jsonb'):
    #         return self._format_json_value(value)
        
    #     # Обработка строк
    #     elif isinstance(value, str):
    #         escaped_value = value.replace("'", "''")
    #         return f"'{escaped_value}'"
        
    #     # Обработка дат и времени
    #     elif isinstance(value, (datetime, date)):
    #         return f"'{value.isoformat()}'"
        
    #     # Обработка булевых значений
    #     elif isinstance(value, bool):
    #         return 'TRUE' if value else 'FALSE'
        
    #     # Числовые типы и прочее
    #     else:
    #         return str(value)

    # def _format_array_value(self, value, data_type):
    #     """Правильное форматирование массивых значений"""
    #     try:
    #         if value is None:
    #             return "NULL"
            
    #         # Если значение уже является массивом
    #         if isinstance(value, (list, tuple)):
    #             # Форматируем каждый элемент массива
    #             formatted_elements = []
    #             for element in value:
    #                 if element is None:
    #                     formatted_elements.append('NULL')
    #                 elif isinstance(element, str):
    #                     escaped_element = element.replace('"', '""')
    #                     formatted_elements.append(f"'{escaped_element}'")
    #                 elif isinstance(element, (int, float)):
    #                     formatted_elements.append(str(element))
    #                 else:
    #                     escaped_element = str(element).replace('"', '""')
    #                     formatted_elements.append(f"'{escaped_element}'")
                
    #             elements_str = ", ".join(formatted_elements)
    #             return f"'{{{elements_str}}}'"
            
    #         # Если значение пришло как строка в формате массива
    #         elif isinstance(value, str) and value.startswith('{') and value.endswith('}'):
    #             return f"'{value}'"
            
    #         # Другие случаи - пытаемся обработать как массив
    #         else:
    #             return f"'{{{value}}}'"
                
    #     except Exception as e:
    #         logger.warning(f"Ошибка форматирования массива {value}: {e}")
    #         return "NULL"

    # def _format_json_value(self, value):
    #     """Форматирование JSON значений"""
    #     try:
    #         if value is None:
    #             return "NULL"
    #         elif isinstance(value, (dict, list)):
    #             json_str = json.dumps(value).replace("'", "''")
    #             return f"'{json_str}'"
    #         elif isinstance(value, str):
    #             # Проверяем, валидный ли это JSON
    #             try:
    #                 json.loads(value)
    #                 escaped_value = value.replace("'", "''")
    #                 return f"'{escaped_value}'"
    #             except:
    #                 escaped_value = value.replace("'", "''")
    #                 return f"'{escaped_value}'"
    #         else:
    #             str_value = str(value).replace("'", "''")
    #             return f"'{str_value}'"
    #     except Exception as e:
    #         logger.warning(f"Ошибка форматирования JSON {value}: {e}")
    #         return "NULL"

class CopyBaseMethods(CopyBaseAbstractMethods):
    
    def __init__(self):
        self.base = PostgreSQLMethods()
        # self.base = SQLiteMethods()

    def copy_base(
        self
        ) -> Response:
        return self.base.copy_base()



