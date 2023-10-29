import discord
from discord.ext import commands
from load_config import load_config
from context import Global
import asyncio
import os


print(discord.__version__)

# создаем класс бота-модератора, наследуясь от commands.Bot
class CheeseHelper(commands.Bot):
    def __init__(self, config_file):
        super().__init__(command_prefix=".", intents=discord.Intents.all())
        self.ctx = Global()
        self.ctx.config_file = config_file
        self.ctx.config_pass, self.ctx.admins, self.ctx.servers, self.ctx.discord_token, self.ctx.openai_keys, self.ctx.moder_roles, self.ctx.unban_guild_ids, self.ctx.appeal_channel_id, self.ctx.welcome_thread_channel_id, self.ctx.docs_transfer_report_channel_id, self.ctx.docs_transfer_spreadsheet_key = load_config(self.ctx.config_file)
        self.ctx.guilds = self.guilds

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print(f"Guilds: {bot.guilds}")
        await self.reload_cogs()

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")

    async def reload_cogs(self):
        cogs = list(bot.cogs.keys())
        for cog in cogs:
            cog_name = cog
            await self.unload_extension(f"cogs.{cog_name}")
            await self.load_extension(f"cogs.{cog_name}")

    # функция проверяющая приоритетность ролей пользователя (user, "1,3,5")
    def check_roles(self, user, priorities):
        priority_set = set(int(p) for p in priorities.split(","))
        for role in user.roles:
            role_id = str(role.id)
            if role_id in self.ctx.moder_roles:
                priority = self.ctx.moder_roles[role_id]
                if priority in priority_set:
                    return True
        return False


    async def on_message(self, message):
        #print(message)
        if message.author == self.user:
            return
        if str(message.author.id) in self.ctx.admins:
            await self.process_commands(message)
        try:
            if message.channel.id in self.ctx.servers[message.guild.id]["read"]:
                print(f"{message.author}: {message.content}")
                if message.content == "GGAB":
                    report_channel = self.get_channel(self.ctx.servers[message.guild.id]["send"])
                    await report_channel.send("Hello World")
                    for admin_id, status in self.ctx.admins.items():
                        if status:
                            admin = await self.fetch_user(admin_id)
                            await admin.send("Hello World")
        except:
            None

if __name__ == '__main__':
    bot = CheeseHelper("config.7z")
    bot.run(bot.ctx.discord_token)
    bot.ctx.guilds = bot.guilds
    print("ФЫР")