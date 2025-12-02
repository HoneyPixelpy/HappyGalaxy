import abc


class AbstractSigmaBoosts(abc.ABC):
    @abc.abstractmethod
    def catalog(self):
        """
        Получаем данные о всех бустах пользователя
        """
    @abc.abstractmethod
    def info(self):
        """
        Получаем данные о конкретном бусте пользователя
        """
    @abc.abstractmethod
    def get_by_user(self):
        """
        Получаем информацию о бустах 
        пользователя в Играх
        """
    @abc.abstractmethod
    def add_passive_income(self):
        """
        Начисляет пассивный доход пользователю
        """
    @abc.abstractmethod
    def upgrade_boost(self):
        """
        Улучшает буст пользователя
        """
    @abc.abstractmethod
    def calculate_recovery_time(self):
        """
        Получаем время для восстановления энергии
        """

class AbstractLumberjackGame(abc.ABC):
    @abc.abstractmethod
    def update_grid(self):
        """
        Обновляет игровое поле пользователя
        """

class AbstractGame(abc.ABC):
    @abc.abstractmethod
    def retrieve(self):
        """
        Получаем игру пользователя
        """
    @abc.abstractmethod
    def active_games(self):
        """
        Получаем все активные игры
        """
    @abc.abstractmethod
    def game_state(self):
        """
        Получаем данные игры с инфой:
        - первый ли это клик;
        - время до восстановления энергии;
        - восстановление энергии если это необходимо
        """
    @abc.abstractmethod
    def process_click(self):
        """
        Обрабатывает клик в игре
        """
    @abc.abstractmethod
    def restore_energy(self):
        """
        Полностью восстанавливает энергию игрока
        """

