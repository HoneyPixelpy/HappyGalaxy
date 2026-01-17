import random
from typing import Optional

from loguru import logger

from .models import Lumberjack_Game, Users
from .orm_requests import Lumberjack_GameMethods, Sigma_BoostsMethods, UserMethods


class Sigma_BoostsForms:

    async def add_passive_income(self, user: Users) -> Users:
        """
        Начисляет пассивный доход только за полные часы
        Возвращает количество начисленных монет
        """
        new_user = await Sigma_BoostsMethods().add_passive_income(user=user)
        if new_user:
            return new_user
        else:
            return user

    async def upgrade(self, user: Users, name: str) -> Optional[dict]:
        """
        Делаем прокачку буста
        """
        upgrade_data = await Sigma_BoostsMethods().upgrade_boost(user, name)
        if not upgrade_data:
            logger.warning(f"Пользователь не может улучшить буст {user.user_id}")
            return
        upgrade_data["user"] = Users(**upgrade_data["user"])
        return upgrade_data


class Lumberjack_GameForms:

    def __init__(self):
        self.min_stars = 2
        self.max_stars = 5
        self.energy_in_click = 1

    async def generate_new_grid(
        self, game_user: Lumberjack_Game, rows: int = 4, cols: int = 5
    ) -> Lumberjack_Game:
        """
        Генерация нового игрового поля с фиксированным количеством положительных ячеек (от 2 до 5)
        """
        # Определяем количество положительных ячеек (от 2 до 5)
        target_cells = random.randint(2, 5)

        # Создаем пустое поле
        grid = [[0 for _ in range(cols)] for _ in range(rows)]

        # Заполняем случайные ячейки единицами
        cells_placed = 0
        while cells_placed < target_cells:
            row = random.randint(0, rows - 1)
            col = random.randint(0, cols - 1)

            if grid[row][col] == 0:  # Если ячейка еще не занята
                grid[row][col] = 1
                cells_placed += 1

        # Сохраняем новое поле
        return await Lumberjack_GameMethods().update_grid(game_user.id, grid)

    async def click_cell(
        self, user: Users, game_user: Lumberjack_Game, row: str, col: str
    ) -> Optional[bool]:
        """
        Обработка клика по ячейке
        Делаем необходимые изменения в базах:
        Lumberjack_Game, Sigma_Boosts, Users
        """
        if (
            isinstance(game_user.current_grid[row][col], int)
            and game_user.current_grid[row][col] == 1
        ):
            return await Lumberjack_GameMethods().process_click(
                user.user_id, self.energy_in_click, row, col
            )

    async def restore_energy(
        self,
        game_user: Lumberjack_Game,
    ) -> None:
        """
        Восстановление энергии со временем
        """
        await Lumberjack_GameMethods().restore_energy(game_user.id)


class UsersForms:

    async def registration(self, user: Users, state_data: dict) -> Users:
        """
        Обновляем данные пользователя для регистрации
        """
        return await UserMethods().complete_registration(user, state_data)
