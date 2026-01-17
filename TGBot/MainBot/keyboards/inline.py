from typing import Dict, List, Optional

import texts
from aiogram import types


class IKB:
    @classmethod
    async def main_menu(
        cls, *args, **kwargs
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        keyboard.extend((
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.profile,
                    callback_data="main_menu|profile"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.game,
                    callback_data="main_menu|game"
                ),
                types.InlineKeyboardButton(
                    text=texts.Btns.quests,
                    callback_data="main_menu|quests"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.invite_friend,
                    callback_data="main_menu|invite_friend"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.shop,
                    callback_data="main_menu|shop"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.rang,
                    callback_data="main_menu|rang"
                ),
                types.InlineKeyboardButton(
                    text=texts.Btns.rating,
                    callback_data="main_menu|rating"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.help,
                    callback_data="main_menu|help"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.who_are_we,
                    url="https://t.me/happiness34vlz/102"
                )
            ]
        ))
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def rating_menu(
        cls
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        keyboard.extend((
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.daily_login,
                    callback_data="rating_menu|daily_login"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.collect_starcoins,
                    callback_data="rating_menu|collect_starcoins"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.guess_country,
                    callback_data="rating_menu|guess_country"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.make_clicks,
                    callback_data="rating_menu|make_clicks"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.completed_quests,
                    callback_data="rating_menu|completed_quests"
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Rating.Btns.invited_friends,
                    callback_data="rating_menu|invited_friends"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.back,
                    callback_data="main_menu|back"
                )
            ]
        ))
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def rating_back(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back,
                        callback_data="main_menu|rating"
                    )
                ]
            ]
        )

    @classmethod
    async def back_to_main(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back,
                        callback_data="main_menu|back"
                    )
                ]
            ]
        )

    @classmethod
    async def sure_role(cls, role: str) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.success_role,
                        callback_data=f"sure_role|{role}",
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="sure_role|back"
                    )
                ],
            ]
        )

    @classmethod
    async def start_hello(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.ready_low, callback_data="start_hello"
                    )
                ]
            ]
        )

    @classmethod
    async def ready_register(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.create, callback_data="ready_register"
                    )
                ]
            ]
        )

    @classmethod
    async def gender(
        cls, role: str, personal: bool = False
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=(
                        texts.Start.Btns.boy
                        if role == "child"
                        else texts.Start.Btns.man
                    ),
                    callback_data="gender|man",
                ),
                types.InlineKeyboardButton(
                    text=(
                        texts.Start.Btns.girl
                        if role == "child"
                        else texts.Start.Btns.woman
                    ),
                    callback_data="gender|woman",
                ),
            ]
        )
        if not personal:
            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="gender|back"
                    )
                ]
            )
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def age(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.change_age, callback_data="edit_age|age"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.change_role, callback_data="edit_age|role"
                    )
                ],
            ]
        )

    @classmethod
    async def data_validation(cls, role: str) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=(
                            texts.Start.Btns.final
                            if role == "child"
                            else texts.Btns.success
                        ),
                        callback_data="data_validation|go",
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Start.Btns.edit_data,
                        callback_data="data_validation|edit",
                    )
                ],
            ]
        )

    @classmethod
    async def before_game(cls) -> types.InlineKeyboardMarkup:
        inline_keyboard = []
        # inline_keyboard.append(
        #     [
        #         types.InlineKeyboardButton(
        #             text=texts.Game.Btns.create,
        #             callback_data="game|create"
        #         )
        #     ]
        # )
        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=texts.Game.Btns.clicker, callback_data="game|clicker"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Game.Btns.geo_hunt, callback_data="game|geo_hunt"
                    )
                ],
            ]
        )
        inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.exit, callback_data="main_menu|back"
                )
            ]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @classmethod
    async def catalog(cls, catalog: dict) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=text, callback_data=data)]
                for text, data in catalog.items()
            ]
        )

    @classmethod
    async def pagination(
        cls, key: str, now_pag: int, max_pag: int
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.null if now_pag <= 1 else texts.Btns.left,
                        callback_data=(
                            "null" if now_pag <= 1 else "{}|{}".format(key, now_pag - 1)
                        ),
                    ),
                    types.InlineKeyboardButton(
                        text="{}/{}".format(now_pag, max_pag), callback_data="null"
                    ),
                    types.InlineKeyboardButton(
                        text=(
                            texts.Btns.null if now_pag >= max_pag else texts.Btns.right
                        ),
                        callback_data=(
                            "null"
                            if now_pag >= max_pag
                            else "{}|{}".format(key, now_pag + 1)
                        ),
                    ),
                ]
            ]
        )

    @classmethod
    async def buttons(
        cls, button_datas: List[Dict], count_lines: int = 4
    ) -> types.InlineKeyboardMarkup:
        inline_keyboard = []
        inline_line = []
        for data in button_datas:
            inline_line.append(
                types.InlineKeyboardButton(
                    text=data["title"], callback_data=data["callback_data"]
                )
            )
            if len(inline_line) >= count_lines:
                inline_keyboard.append(inline_line.copy())
                inline_line.clear()
        else:
            if inline_line:
                inline_keyboard.append(inline_line.copy())
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @classmethod
    async def buy_product(
        cls, product_id: int, instructions: str
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.yes,
                        callback_data=f"buy_product|{product_id}|{instructions}"
                    ),
                    types.InlineKeyboardButton(
                        text=texts.Btns.no, callback_data="buy_product|back"
                    ),
                ]
            ]
        )

    @classmethod
    async def confirm_buy(
        cls
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.yes,
                        callback_data="confirm_buy|yes"
                    ),
                    types.InlineKeyboardButton(
                        text=texts.Btns.no,
                        callback_data="confirm_buy|no"
                    ),
                ]
            ]
        )

    @classmethod
    async def rollback_buy(
        cls, purchases_id: int
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.rollback,
                        callback_data=f"rollback_buy|{purchases_id}"
                    ),
                ]
            ]
        )

    @classmethod
    async def success_buy(
        cls, purchases_id: int
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.success,
                        callback_data=f"success_buy|success|{purchases_id}"
                    ),
                    types.InlineKeyboardButton(
                        text=texts.Btns.cancel,
                        callback_data=f"success_buy|cancel|{purchases_id}"
                    ),
                ]
            ]
        )

    @classmethod
    async def check_sub(cls, sub_quest_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.check, callback_data=f"check_sub|{sub_quest_id}"
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="all_quests"
                    )
                ],
            ]
        )

    # @classmethod
    # async def success_ruls(cls) -> types.InlineKeyboardMarkup:
    #     return types.InlineKeyboardMarkup(
    #             inline_keyboard=[
    #                 [
    #                     types.InlineKeyboardButton(
    #                         text=texts.Start.Btns.listened,
    #                         callback_data="success_ruls"
    #                     )
    #                 ]
    #             ]
    #         )
    @classmethod # NOTE DELETE
    async def back_to_profile(cls) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="back_to_profile"
                    )
                ]
            ]
        )

    # @classmethod
    # async def refresh_info(cls) -> types.InlineKeyboardMarkup:
    #     return types.InlineKeyboardMarkup(
    #             inline_keyboard=[
    #                 [
    #                     types.InlineKeyboardButton(
    #                         text=texts.Btns.refresh,
    #                         callback_data="refresh_info"
    #                     )
    #                 ]
    #             ]
    #         )
    @classmethod
    async def idea_quest(cls, quest_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.go_activate,
                        callback_data=f"idea_quest|{quest_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="all_quests"
                    )
                ],
            ]
        )

    @classmethod
    async def daily_quest(cls, quest_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.go_activate,
                        callback_data=f"daily_quest|{quest_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.back, callback_data="all_quests"
                    )
                ],
            ]
        )

    @classmethod
    async def back(cls, callback_data: str) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text=texts.Btns.back,
                            callback_data=callback_data
                        )
                    ]
                ]
            )
    @classmethod
    async def verif_idea_admin(
        cls, quest_id: int, user_id: int
    ) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.approve,
                        callback_data=f"activate_idea|success|{quest_id}|{user_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.deny,
                        callback_data=f"activate_idea|delete|{quest_id}|{user_id}",
                    )
                ],
            ]
        )

    @classmethod
    async def new_rang(cls, new_quests: bool) -> types.InlineKeyboardMarkup:
        keyboard = []
        if new_quests:
            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.Season.Btns.view_quests, callback_data="all_quests"
                    )
                ]
            )
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Season.Btns.view_rangs, callback_data="view_rangs"
                )
            ]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    async def create_game(
        cls, required_result: Optional[bool]
    ) -> types.InlineKeyboardMarkup:
        inline_keyboard = []
        if required_result:
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.create,
                        callback_data="create_game",
                    )
                ]
            )

        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.clear,
                        callback_data="update_game|clear",
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.type_game,
                        callback_data="update_game|type_game",
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.title,
                        callback_data="update_game|title",
                    ),
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.description,
                        callback_data="update_game|description",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.reward_starcoins,
                        callback_data="update_game|reward_starcoins",
                    ),
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.reward_type,
                        callback_data="update_game|reward_type",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.min_rang,
                        callback_data="update_game|min_rang",
                    ),
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.max_rang,
                        callback_data="update_game|max_rang",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.min_players,
                        callback_data="update_game|min_players",
                    ),
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.max_players,
                        callback_data="update_game|max_players",
                    ),
                ],
            ]
        )
        inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.InteractiveGame.Btns.delete,
                    callback_data="update_game|delete",
                )
            ]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @classmethod
    async def verif_interactive_game(cls, game_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.approve,
                        callback_data=f"verif_interactive_game|success|{game_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Quests.Btns.deny,
                        callback_data=f"verif_interactive_game|delete|{game_id}",
                    )
                ],
            ]
        )

    @classmethod
    async def new_try_interactive_game(cls, game_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.start,
                        callback_data=f"verif_interactive_game|success|{game_id}",
                    ),
                ]
            ]
        )

    @classmethod
    async def login_game(cls, game_id: int) -> types.InlineKeyboardMarkup:
        return types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.login,
                        callback_data=f"login_interactive_game|{game_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.exit, callback_data="exit"
                    ),
                ],
            ]
        )

    @classmethod
    async def ready_game(
        cls, game_id: int, end_mailing: bool = False
    ) -> types.InlineKeyboardMarkup:
        inline_keyboard = []
        if end_mailing:
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.start,
                        callback_data=f"start_interactive_game|{game_id}",
                    ),
                ]
            )
        inline_keyboard.extend(
            [
                [
                    types.InlineKeyboardButton(
                        text=texts.Btns.refresh,
                        callback_data=f"refresh_interactive_game|{game_id}",
                    ),
                ],
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.delete,
                        callback_data=f"delete_interactive_game|{game_id}",
                    ),
                ],
            ]
        )
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    @classmethod
    async def game_info(cls, game_id: int, owner: bool) -> types.InlineKeyboardMarkup:
        inline_keyboard = []
        # inline_keyboard.append(
        #     [
        #         types.InlineKeyboardButton(
        #             text=texts.InteractiveGame.Btns.players,
        #             callback_data=""
        #         ),
        #     ]
        # )
        inline_keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=texts.Btns.refresh,
                    callback_data=f"refresh_info_game|{game_id}",
                ),
            ]
        )
        if owner:
            inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=texts.InteractiveGame.Btns.end_game,
                        callback_data=f"players_end_game|{game_id}|1",
                    ),
                ]
            )
        # else:
        #     inline_keyboard.append(
        #         [
        #             types.InlineKeyboardButton(
        #                 text=texts.InteractiveGame.Btns.try_end_game,
        #                 callback_data=f"try_end_game|{game_id}"
        #             ),
        #         ]
        #     )
        return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
