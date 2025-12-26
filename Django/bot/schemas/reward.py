from pydantic import BaseModel


class RewardDataPydantic(BaseModel):
    starcoins_for_referer: int
    starcoins_for_referal: int
    starcoins_parent_bonus: int


reward_data = RewardDataPydantic(
    starcoins_for_referer=11, starcoins_for_referal=5, starcoins_parent_bonus=7
)
