from typing import Union
from pydantic import BaseModel


class BoostPydantic(BaseModel):
    max_level: int
    value_by_level: dict[int,Union[int,float]]
    price: dict[int,int]

class BoostData:
    def __init__(self, pd: BoostPydantic):
        self.pd: BoostPydantic = pd
        self._emoji = {
            0: "🦣",
            1: "🦣",
            2: "🦣",
            3: "🦣",
            4: "🦣",
            5: "☀️",
            6: "☀️",
            7: "☀️",
            8: "☀️",
            9: "☀️",
            10: "🌈",
            11: "🌈",
            12: "🌈",
            13: "🌈",
            14: "🌈",
            15: "😱",
            16: "😱",
            17: "😱",
            18: "😱",
            19: "😱",
            20: "😱",
            21: "😱",
            22: "😱",
            23: "😱",
            24: "😱",
            25: "😱",
            26: "😱",
            27: "😱",
            28: "😱",
            29: "😱"
        }

    def max_level(self) -> int:
        return self.pd.max_level

    def value_by_level(self, level: int) -> Union[int,float]:
        try:
            return self.pd.value_by_level[level]
        except KeyError:
            if level <= 0:
                return self.pd.value_by_level[0]
            else:
                return self.pd.value_by_level[self.pd.max_level]

    def price(self, level: int) -> Union[int,float,str]:
        """
        Получаем цену для следущего уровня
        относительно нашего текущего уровня (level)
        """
        try:
            return self.pd.price[level+1]
        except KeyError:
            return "MAX"

    def emoji(self, level: int) -> str:
        try:
            return self._emoji[level]
        except KeyError:
            return "💪"

class BoostsPydantic(BaseModel):
    income_level: BoostData
    energy_capacity_level: BoostData
    recovery_level: BoostData
    passive_income_level: BoostData

    class Config:
        arbitrary_types_allowed = True  # Разрешает любые типы без валидации


boosts_data = BoostsPydantic(
    income_level = BoostData(
        BoostPydantic(
            max_level = 19,
            value_by_level = {
                0: 0.01,
                1: 0.02,
                2: 0.03,
                3: 0.04,
                4: 0.05,
                5: 0.06,
                6: 0.07,
                7: 0.08,
                8: 0.09,
                9: 0.1,
                10: 0.11,
                11: 0.12,
                12: 0.13,
                13: 0.14,
                14: 0.15,
                15: 0.16,
                16: 0.17,
                17: 0.18,
                18: 0.19,
                19: 0.2
            },
            price = {
                0: 0,
                1: 5,
                2: 10,
                3: 15,
                4: 25,
                5: 40,
                6: 60,
                7: 90,
                8: 130,
                9: 180,
                10: 240,
                11: 310,
                12: 400,
                13: 520,
                14: 670,
                15: 850,
                16: 1100,
                17: 1400,
                18: 1700,
                19: 2000
            }
        )
    ),
    energy_capacity_level = BoostData(
        BoostPydantic(
            max_level = 7,
            value_by_level = {
                0: 30,
                1: 40,
                2: 50,
                3: 60,
                4: 70,
                5: 80,
                6: 90,
                7: 100
            },
            price = {
                0: 0,
                1: 10,
                2: 15,
                3: 25,
                4: 40,
                5: 60,
                6: 85,
                7: 120
            }
        )
    ),
    recovery_level = BoostData(
        BoostPydantic(
            max_level = 2,
            value_by_level = {
                0: 240,
                1: 210,
                2: 180
            },
            price = {
                0: 0,
                1: 50,
                2: 150
            }
        )
    ),
    passive_income_level = BoostData(
        BoostPydantic(
            max_level = 3,
            value_by_level = {
                0: 0,
                1: 0.2,
                2: 0.4,
                3: 0.6
            },
            price = {
                0: 0,
                1: 60,
                2: 110,
                3: 160
            }
        )
    )
)

