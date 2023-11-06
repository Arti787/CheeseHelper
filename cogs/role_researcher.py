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
            data = self.data
            try:
                    self.mess = await self.channel.fetch_message(self.data["MessID"])
                    for i in data:
                        if i != "MessID":
                            data[i]["member"] = []
                            for j in data[i]["role"].members:
                                data[i]["member"].append(j.mention)
                            if data[i]["member"] == []:
                                data[i]["member"].append("Не назначен")
                    guild = self.bot.get_guild(691788414101618819)
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
                               f''
                               )
                    print("--[Roles Researcher Logs]: Successfully Compiled! Sending...")
                    await self.mess.edit(content=message)
                    print("--[Roles Researcher Logs]: Successfully Sent!")
            except Exception as e:
                    print(e)
                    channel = self.guild.get_channel(927615877833183252)
                    self.mess = await channel.send("Preloaded Message \nIt will disappear in next 1 hour бож это работает")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = {
            "MessID": None,

            "CatMod": {
                "role": 861257547012112405,
                "member": []
            },
            "CatSys": {
                "role": 1146125101851488326,
                "member": []
            },
            "CatCr": {
                "role": 1146131594080423976,
                "member": []
            },
            "CatGame": {
                "role": 1130151264123097168,
                "member": []
            },

            "SeM": {
                "role": 1093963334128238624,
                "member": []
            },
            "ZamSeM": {
                "role": 1158074479549894829,
                "member": []
            },
            "StM": {
                "role": 1032275192308826153,
                "member": []
            },
            "Sec": {
                "role": 1126958764994613258,
                "member": []
            },
            "Mod": {
                "role": 1004721986016129095,
                "member": []
            },
            "SeSys": {
                "role": 1144738416009945098,
                "member": []
            },
            "MlSys": {
                "role": 1143892003319464077,
                "member": []
            },
            "Sys": {
                "role": 870608947093057555,
                "member": []
            },
            "SeCr": {
                "role": 1146017381068591185,
                "member": []
            },
            "SeGame": {
                "role": 1146016243237797929,
                "member": []
            },
            "Primet": {
                "role": 1130156038465794198,
                "member": []
            },
            "GameRup": {
                "role": 1130160734584717432,
                "member": []
            },
            "GameEve": {
                "role": 1130150846890528938,
                "member": []
            }
        }
        self.mess = self.data["MessID"]
        print("Syncing roles")
        self.guild = self.bot.get_guild(691788414101618819)
        data = self.data
        try:
            for i in data:
                if i != "MessID":
                    data[i]["role"] = self.guild.get_role(data[i]["role"])
                    for j in data[i]["role"].members:
                        data[i]["member"].append(j.mention)
                    if data[i]["member"] == []:
                        data[i]["member"].append("Не назначен")
        except:
            pass
        print(data)
        self.data = data
        self.channel = self.guild.get_channel(927615877833183252)
        # print(self.mess.id)
        print("--[Roles Researcher Logs]: Roles and message are synced")
        self.sdsf.start(self.bot)

async def setup(bot: commands.Bot):
    await bot.add_cog(on_roles_check(bot), guilds=bot.guilds)