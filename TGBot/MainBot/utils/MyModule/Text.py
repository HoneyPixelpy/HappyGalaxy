from typing import Optional, Tuple, List
import re
from loguru import logger

class TextProcessor:
    MAX_CAPTION_LENGTH = 1024
    MAX_MESSAGE_LENGTH = 4096
    
    # Регулярное выражение для поиска всех HTML-тегов, включая теги с атрибутами.
    # Это более надёжный вариант, который захватывает открывающие, закрывающие и самозакрывающиеся теги.
    TAG_REGEX = re.compile(r'<(\/?)(\w+)([^>]*)>')

    @classmethod
    def _get_tag_string(cls, tag_name: str, is_closing: bool = False) -> str:
        """Возвращает строку тега."""
        return f'</{tag_name}>' if is_closing else f'<{tag_name}>'

    @classmethod
    def _find_safe_split_point(cls, text: str, max_length: int) -> int:
        """
        Находит последнюю безопасную точку разделения текста (пробел)
        до максимальной длины, чтобы не обрезать слова.
        """
        # Ищем последнюю "безопасную" позицию для разделения,
        # которая не находится внутри HTML-тега.
        # Идём от конца к началу, чтобы найти ближайший пробел
        for i in range(min(max_length, len(text)), -1, -1):
            if text[i] == ' ':
                # Проверяем, находится ли этот пробел внутри тега
                is_inside_tag = False
                for match in cls.TAG_REGEX.finditer(text):
                    if match.start() <= i < match.end():
                        is_inside_tag = True
                        break
                if not is_inside_tag:
                    return i
        
        # Если пробел не найден, возвращаем максимальную длину
        return max_length

    @classmethod
    def split_text(
        cls, 
        text: str, 
        max_length: int
    ) -> Tuple[str, str]:
        """
        Разделяет текст на две части, сохраняя целостность HTML-разметки.
        """
        if len(text) <= max_length:
            return text, ""
            
        safe_split_index = cls._find_safe_split_point(text, max_length)
        if safe_split_index == 0:
            # Если не удалось найти безопасную точку, берём часть текста
            # до max_length. Это крайний случай.
            first_part = text[:max_length]
            remaining_text = text[max_length:]
        else:
            first_part = text[:safe_split_index]
            remaining_text = text[safe_split_index:]

        # Используем стек для отслеживания открытых тегов в первой части
        tag_stack = []
        matches = cls.TAG_REGEX.finditer(first_part)
        
        for match in matches:
            is_closing = match.group(1) == '/'
            tag_name = match.group(2)
            
            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                else:
                    # Логируем некорректную разметку, чтобы знать о проблеме
                    logger.warning(f"Найден закрывающий тег '</{tag_name}>' без соответствующего открывающего в первой части текста.")
            else:
                tag_stack.append(tag_name)

        # Формируем недостающие закрывающие теги для первой части
        closing_tags = [cls._get_tag_string(tag_name, is_closing=True) for tag_name in reversed(tag_stack)]
        first_part_with_tags = first_part + ''.join(closing_tags)
        
        # Формируем открывающие теги для второй части
        re_opening_tags = [cls._get_tag_string(tag_name) for tag_name in tag_stack]
        remaining_text = ''.join(re_opening_tags) + remaining_text
        
        return first_part_with_tags, remaining_text

    @classmethod
    def prepare_text_parts(
        cls, 
        text: Optional[str] = None,
        first_len: Optional[int] = None
    ) -> List[str]:
        """
        Разбивает текст на части для отправки сообщениями.
        """
        if not text:
            return ['']
        
        parts = []
        remaining_text = text
        
        # Первая часть текста (для caption) имеет свой лимит
        first_part, remaining_text = cls.split_text(
            remaining_text, 
            first_len if first_len else cls.MAX_CAPTION_LENGTH
            )
        parts.append(first_part)

        # Остальные части текста (для обычных сообщений) имеют другой лимит
        while remaining_text:
            part, remaining_text = cls.split_text(remaining_text, cls.MAX_MESSAGE_LENGTH)
            parts.append(part)
            
        return parts