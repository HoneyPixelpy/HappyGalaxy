import abc


class AbstractSigmaBoosts:
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


