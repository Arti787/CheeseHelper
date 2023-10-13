import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import json
import asyncio
import time

class on_roles_check(commands.Cog):

    @tasks.loop(hours=1)
    async def sdsf(self, bot):

            print("--[Roles Researcher Logs]: Pre Loading Values")
            try:
                self.mess = await self.channel.fetch_message(self.data["MessID"])
                func = self.mess.edit
            except:
                func = self.channel.send
            data = self.data
            for i in data:
                if i != "MessID":
                    data[i]["member"] = []
                    for j in data[i]["role"].members:
                        data[i]["member"].append(j.mention)
                    if data[i]["member"] == []:
                        data[i]["member"].append("Не назначен")
            try:
                guild = self.bot.get_guild(1096100154148397208)
                mods = ""
                for i in range(len(data["Mod"]["member"])):
                    mods += f'{data["Mod"]["member"][i]} \n'

                Sys = ""
                for i in range(len(data["Sys"]["member"])):
                    Sys += f'{data["Sys"]["member"][i]} \n'

                MlSys = ""
                for i in range(len(data["MlSys"]["member"])):
                    MlSys += f'{data["MlSys"]["member"][i]} \n'

                GameRup = ""
                for i in range(len(data["GameRup"]["member"])):
                    GameRup += f'{data["GameRup"]["member"][i]} \n'

                GameEve = ""
                for i in range(len(data["GameEve"]["member"])):
                    GameEve += f'{data["GameEve"]["member"][i]} \n'

                print("--[Roles Researcher Logs]: Compiling Message")

                message = (f'>>> # Персонал сервера: \n'
                           f'## Модерация \n'
                           f'\n'
                           f'{data["CatMod"]["role"].mention} \n'
                           f'\n'
                           f'{data["SeM"]["role"].mention} \n'
                           f'{data["SeM"]["member"][0]} \n'
                           f'\n'
                           f'{data["ZamSeM"]["role"].mention} \n'
                           f'{data["ZamSeM"]["member"][0]} \n'
                           f'\n'
                           f'{data["StM"]["role"].mention} \n'
                           f'{data["StM"]["member"][0]} \n'
                           f'\n'
                           f'{data["Sec"]["role"].mention} \n'
                           f'{data["Sec"]["member"][0]} \n'
                           f'\n'
                           f'{data["Mod"]["role"].mention} \n'
                           f'{mods}'
                           f'\n'
                           f'## Cисадмины \n'
                           f'\n'
                           f'{data["CatSys"]["role"].mention}\n'
                           f'\n'
                           f'{data["SeSys"]["role"].mention} \n'
                           f'{data["SeSys"]["member"][0]} \n'
                           f'\n'
                           f'{data["Sys"]["role"].mention} \n'
                           f'{Sys}'
                           f'\n'
                           f'{data["MlSys"]["role"].mention} \n'
                           f'{MlSys}'
                           f'\n'
                           f'## Креатив Отдел \n'
                           f'\n'
                           f'{data["CatCr"]["role"].mention} \n'
                           f'\n'
                           f'{data["SeCr"]["role"].mention} \n'
                           f'{data["SeCr"]["member"][0]} \n'
                           f'\n'
                           f'## Игро-Фыры \n'
                           f'\n'
                           f'{data["CatGame"]["role"].mention}\n'
                           f'\n'
                           f'{data["SeGame"]["role"].mention} \n'
                           f'{data["SeGame"]["member"][0]} \n'
                           f'\n'
                           f'{data["Primet"]["role"].mention} \n'
                           f'{data["Primet"]["member"][0]} \n'
                           f'\n'
                           f'{data["GameRup"]["role"].mention} \n'
                           f'{GameRup}'
                           f'\n'
                           f'{data["GameEve"]["role"].mention} \n'
                           f'{GameEve}'
                           f'\n'
                           f'## Шефы серверов клана \n\n'
                           f'{data["SeMine"]["role"].mention} \n'
                           f'{data["SeMine"]["member"][0]} \n'
                           f'\n'
                           f'{data["SeNSFW"]["role"].mention} \n'
                           f'{data["SeNSFW"]["member"][0]} \n'
                           f'\n'
                           f'{data["SeArt"]["role"].mention} \n'
                           f'{data["SeArt"]["member"][0]} \n'
                           f''
                           )
                print("--[Roles Researcher Logs]: Successfully Compiled! Sending...")
                await func(content=message)
                print("--[Roles Researcher Logs]: Successfully Sent!")
            except:
                channel = self.guild.get_channel(1149419053736272045)
                self.mess = await channel.send("Preloaded Message \nIt will disappear in next 1 hour")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {
            "MessID": 1159547594574401537,

            "CatMod": {
                "role": 1159358890736099328,
                "member": []
            },
            "CatSys": {
                "role": 1159359120864968744,
                "member": []
            },
            "CatCr": {
                "role": 1159359120864968744,
                "member": []
            },
            "CatGame": {
                "role": 1159359120864968744,
                "member": []
            },

            "SeM": {
                "role": 1159176342038921236,
                "member": []
            },
            "ZamSeM": {
                "role": 1159176455524200509,
                "member": []
            },
            "StM": {
                "role": 1159176527091609610,
                "member": []
            },
            "Sec": {
                "role": 1159176590731784323,
                "member": []
            },
            "Mod": {
                "role": 1159176672042553458,
                "member": []
            },
            "SeSys": {
                "role": 1159176702052814868,
                "member": []
            },
            "MlSys": {
                "role": 1159176789827014718,
                "member": []
            },
            "Sys": {
                "role": 1159176793308270724,
                "member": []
            },
            "SeCr": {
                "role": 1159176887654944823,
                "member": []
            },
            "SeGame": {
                "role": 1159176979619258488,
                "member": []
            },
            "Primet": {
                "role": 1159177304224841768,
                "member": []
            },
            "GameRup": {
                "role": 1159177408084197526,
                "member": []
            },
            "GameEve": {
                "role": 1159177408084197526,
                "member": []
            },
            "SeMine": {
                "role": 1159177454750027817,
                "member": []
            },
            "SeNSFW": {
                "role": 1159177520063729704,
                "member": []
            },
            "SeArt": {
                "role": 1159177606877425746,
                "member": []
            }
        }
        self.mess = None
        print("Syncing roles")
        self.guild = self.bot.get_guild(1096100154148397208)
        data = self.data
        for i in data:
            if i != "MessID":
                data[i]["role"] = self.guild.get_role(data[i]["role"])
                for j in data[i]["role"].members:
                    data[i]["member"].append(j.mention)
                if data[i]["member"] == []:
                    data[i]["member"].append("Не назначен")
        print(data)
        self.data = data
        self.channel = self.guild.get_channel(1149419053736272045)
        # print(self.mess.id)
        print("--[Roles Researcher Logs]: Roles and message are synced")
        self.sdsf.start(self.bot)

async def setup(bot: commands.Bot):
    await bot.add_cog(on_roles_check(bot), guilds=bot.guilds)