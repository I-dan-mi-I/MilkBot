import gspread_asyncio
from google.oauth2.service_account import Credentials

from datetime import datetime
from typing import Union, NoReturn
import numpy as np


def get_creds():
    creds = Credentials.from_service_account_file(r"./tokens/credentials_astral.json")
    scoped = creds.with_scopes(
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    return scoped


class AsyncTables:
    def __init__(self):
        self.base = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.session = None

    async def autorize(self):
        self.session = await self.base.authorize()

    # astral

    async def set_players_name(self, spread_sheet_id: str, players: list) -> None:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")

        data = [
            {
                "range": f"A2:A{2+len(players)}",
                "values": [[player.name] for player in players],
            }
        ]

        await sheet.batch_update(data)

    async def set_players_teams(self, spread_sheet_id: str, players: int) -> None:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")

        data = [
            {
                "range": f"C2:C{1+players}",
                "values": [["2" if p != players - 1 else "1"] for p in range(players)],
            }
        ]

        await sheet.batch_update(data)

    async def get_players_name(self, spread_sheet_id: str) -> list:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")
        values = await sheet.get_values("A2:A6")
        return list(np.array(values).ravel())

    async def get_players_spreadsheets_links(self, spread_sheet_id: str) -> list:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")
        values = await sheet.get_values("D2:D6")
        return list(np.array(values).ravel())

    async def set_players_move(self, spread_sheet_id: str, players: list) -> NoReturn:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Основная")

        data = []

        for count, value in enumerate(players):
            data.append(
                {
                    "range": f"C{count+2}:D{count+2}",
                    "values": [[value.move, value.move_direction]],
                }
            )

        await sheet.batch_update(data)

    async def get_player_spells(self, spread_sheet_id: str, player: str) -> list:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet(player)
        try:
            value = await sheet.get_values("Q90")
            spells = value[0][0].lower()
            if spells is None or spells == "":
                raise Exception
        except:
            return await self.get_player_spells(spread_sheet_id, player)
        return spells.split(", ")

    async def get_game_message(
        self, spread_sheet_id: str, time: datetime
    ) -> Union[list, bool]:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Основная")
        try:
            value = await sheet.get_values("I6")
            message = value[0][0]
            if message is None or message == "":
                raise Exception
        except Exception as e:
            print(e)
            if (datetime.now() - time).total_seconds() <= 15:
                return await self.get_game_message(spread_sheet_id, time)
            else:
                return False
        try:
            message_list = ["", []]
            g = message.split("\n")
            l = g[0].split(" ")
            for i in l:
                if i != "":
                    message_list[1].append(i)
            for i in range(4):
                g.pop(0)
            message_list[0] = ("\n").join(g)
        except Exception as e:
            print(e)
        return message_list

    async def set_arena(self, spread_sheet_id: str, arena: str) -> NoReturn:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")
        await sheet.update_acell("I3", arena)

    async def set_dm(self, spread_sheet_id: str, dm: str) -> None:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Настройки")
        await sheet.update_acell("K2", dm)

    async def get_player_effects(self, spread_sheet_id: str, player: str) -> str:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        main_sheet = await spread_sheet.worksheet("Основная")
        try:
            value = await main_sheet.get_values("H2")
            game_round = value[0][0]
            if game_round is None or game_round == "":
                raise Exception
        except:
            return await self.get_player_effects(spread_sheet_id, player)

        player_sheet = await spread_sheet.worksheet(player)
        try:
            value = await player_sheet.get_values("O3")
            first_number_eff = value[0][0]
            if first_number_eff is None or first_number_eff == "":
                raise Exception
        except:
            return await self.get_player_effects(spread_sheet_id, player)

        try:
            value = await player_sheet.get_values(
                f"U{2 + (int(game_round) - int(first_number_eff) + 1)}"
            )
            eff = value[0][0]
            return eff if eff is not None else ""
        except:
            return ""

    async def get_player_mp(self, spread_sheet_id: str, player: str) -> int:
        players: list = await self.get_players_name(spread_sheet_id)
        num = players.index(player)

        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Основная")

        try:
            values = await sheet.get_values("G2:G6")
            list_of_mp = list(np.array(values).ravel())
            if not list_of_mp:
                return await self.get_player_mp(spread_sheet_id, player)
        except:
            return await self.get_player_mp(spread_sheet_id, player)

        return list_of_mp[num]

    async def get_game_spells(self, spread_sheet_id: str) -> dict:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Описание")

        spells_info = await sheet.get_values("A2:G400")
        game_spells = {}

        for spell_info in spells_info:
            game_spells[spell_info[0].lower()] = {
                "mp": (int(spell_info[6]) if int(spell_info[6]) != 0 else -100),
                "type": spell_info[5],
            }

        return game_spells

    async def get_astral_script_id(self, spread_sheet_id: str) -> str:
        spread_sheet = await self.session.open_by_key(spread_sheet_id)
        sheet = await spread_sheet.worksheet("Инфо")

        return (await sheet.get_values("B1"))[0][0]

    # def create_astral_table(self, guild_id: int) -> None:
    #     spread_sheet = self.table_session.create(
    #         f"astral-{guild_id}", template=self.bot.database.get_tables()["astral"]
    #     )
    #
    #     spread_sheet.share("", role="writer", type="anyone")
    #     sheet = spread_sheet.worksheet_by_title("Инфо")
    #     sheet.update_value("A2", f"{guild_id}")
    #
    #     guild = self.bot.database.get_guild_info(guild_id)
    #     guild.astral_table = spread_sheet.id
    #     self.bot.database.session.commit()
    #
    # def create_temp_astral_table(
    #         self, uuid: str, template: Optional[str] = None
    # ):
    #     spread_sheet = self.table_session.create(
    #         f"temp_astral-{uuid}",
    #         template=template
    #         if template is not None
    #         else self.bot.database.get_tables()["astral"],
    #     )
    #
    #     spread_sheet.share("", role="writer", type="anyone")
    #     sheet = spread_sheet.worksheet_by_title("Инфо")
    #     sheet.update_value("B1", "=ScriptID()")
    #     sheet.update_value("B2", uuid)
    #
    #     return spread_sheet
    #
    # def get_astral_script_id(self, sheet_url: str) -> str:
    #     spread_sheet = self.table_session.open_by_url(sheet_url)
    #     sheet = spread_sheet.worksheet_by_title("Инфо")
    #
    #     return sheet.get_value("B1")