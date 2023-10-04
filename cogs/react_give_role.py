import discord
from discord import app_commands, ui
from discord.ext import commands
import json



class react_give_role(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("react_give_role")

    @app_commands.command(name="выдача", description="Установить сообщению роль на реакции")
    async def react(self, interaction: discord.Interaction, message_id: str, role_id: str, emoji_name: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        message_id = int(message_id)
        role_id = int(role_id)
        with open("data/react_give_role.json", "r") as f:
            data = json.load(f)
            f.close()

        try:
            message = data[str(message_id)]
            try:
                data[str(message_id)][emoji_name.split(":")[1]] = int(role_id)
            except:
                data[str(message_id)][emoji_name] = int(role_id)

        except:
            try:
                message = {
                    emoji_name.split(":")[1]: int(role_id)
                }
            except:
                message = {
                    emoji_name: int(role_id)
                }
            data[str(message_id)] = message

        with open("data/react_give_role.json", "w") as f:
            json.dump(data, f)
            f.close()
        channel = self.bot.get_channel(interaction.channel.id)
        message = await channel.fetch_message(int(message_id))
        await message.add_reaction(emoji_name)
        await interaction.response.send_message("Успешно добавлены роли на сообщение", ephemeral=True)


    @app_commands.command(name="очистить_сообщение", description="убрать все привязанные роли к сообщению")
    async def clear(self, interaction: discord.Interaction, message_id: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        message_id =  int(message_id)
        with open("data/react_give_role.json", "r") as f:
            data = json.load(f)
            f.close()

        try:
            data.pop(str(message_id))
            await interaction.response.send_message("Успешно удалены привязки", ephemeral=True)

        except:
            await interaction.response.send_message("Unknown message", ephemeral=True)

        with open("data/react_give_role.json", "w") as f:
            json.dump(data, f)
            f.close()


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):
        with open("data/react_give_role.json", "r") as f:
            data = json.load(f)
            f.close()

        for i in data:

            if payload.message_id == int(i):

                for j in data[i]:

                    if payload.emoji.name == j:

                        role = self.bot.get_guild(payload.guild_id).get_role(int(data[i][j]))
                        channel = self.bot.get_channel(payload.channel_id)
                        message = await channel.fetch_message(payload.message_id)
                        user = message.guild.get_member(payload.user_id)
                        if not user.bot:
                            await user.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload:discord.RawReactionActionEvent):

        with open("data/react_give_role.json", "r") as f:
            data = json.load(f)
            f.close()
        try:
            test_is_known = data[str(payload.message_id)]

            for j in data[str(payload.message_id)]:

                if payload.emoji.name == j:

                    role = self.bot.get_guild(payload.guild_id).get_role(int(data[str(payload.message_id)][j]))
                    channel = self.bot.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    user = message.guild.get_member(payload.user_id)
                    if not user.bot:
                        await user.remove_roles(role)
        except:
            print("unknown message")

async def setup(bot: commands.Bot):
    await bot.add_cog(react_give_role(bot), guilds=bot.guilds)
