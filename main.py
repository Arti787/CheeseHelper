import discord
from discord.ext import commands
from load_config import load_config
from multi_variable import Global
import asyncio
import os


print(discord.__version__)

# создаем класс бота-модератора, наследуясь от commands.Bot
class CheeseHelper(commands.Bot):
    def __init__(self, config_file):
        super().__init__(command_prefix="/", intents=discord.Intents.all())
        self.multi_variable = Global()
        self.multi_variable.config_file = config_file
        self.multi_variable.admins, self.multi_variable.servers, self.multi_variable.discord_token, self.multi_variable.openai_keys, self.multi_variable.moder_roles = load_config(self.multi_variable.config_file)
        self.multi_variable.admins, self.multi_variable.servers, self.multi_variable.discord_token, self.multi_variable.openai_keys, self.multi_variable.moder_roles
        self.multi_variable.guilds = self.guilds

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print(f"Guilds: {bot.guilds}")
        await self.reload_cogs()  # call a function to reload all cogs with guilds

    async def reload_cogs(self):
        cogs = list(bot.cogs.keys()) # make a copy of the cog names
        for cog in cogs:  # iterate over the copy
            cog_name = cog
            await self.unload_extension(f"cogs.{cog_name}")
            await self.load_extension(f"cogs.{cog_name}")

    # функция проверяющая приоритетность ролей пользователя (user, "1,3,5")
    def check_roles(self, user, priorities):
        priority_set = set(int(p) for p in priorities.split(","))
        for role in user.roles:
            role_id = str(role.id)
            if role_id in self.multi_variable.moder_roles:
                priority = self.multi_variable.moder_roles[role_id]
                if priority in priority_set:
                    return True
        return False


    async def on_message(self, message):
        if message.author == self.user:
            return
        if str(message.author.id) in self.multi_variable.admins:
            await self.process_commands(message)
        if message.channel.id in self.multi_variable.servers[message.guild.id]["read"]:
            print(f"{message.author}: {message.content}")
            if message.content == "GGAB":
                report_channel = self.get_channel(self.multi_variable.servers[message.guild.id]["send"])
                await report_channel.send("Hello World")
                for admin_id, status in self.multi_variable.admins.items():
                    if status:
                        admin = await self.fetch_user(admin_id)
                        await admin.send("Hello World")

if __name__ == '__main__':
    bot = CheeseHelper("config.7z")
    bot.run(bot.multi_variable.discord_token)
    bot.multi_variable.guilds = bot.guilds
    print("ФЫ")