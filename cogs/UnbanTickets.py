import discord
from discord import ui, app_commands
from discord.ext import commands

class UnbanModal(ui.Modal, title='Разбанить пользователя'):
    ban_date = ui.TextInput(label='Дата бана', placeholder='Введите дату бана в формате ДД.ММ.ГГГГ')
    ban_reason = ui.TextInput(label='Причина бана', placeholder='Введите причину бана, указанную при бане')
    unban_reason = ui.TextInput(label='Причина разбана', placeholder='Введите причину разбана. Больше слов - больше шанс.', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        ban_date = self.ban_date.value
        ban_reason = self.ban_reason.value
        unban_reason = self.unban_reason.value
        await interaction.response.send_message(f'Спасибо за ваш ответ!', ephemeral=True)
        # Отправляем результаты опроса в канал с id 1114259348898713620
        channel = self.bot.get_channel(1114234886077825124)
        if channel is not None:
            embed = discord.Embed(title=f'Опрос о разбане пользователя {interaction.user}', colour=discord.Colour.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
            embed.add_field(name='Дата бана:', value=ban_date)
            embed.add_field(name='Причина бана:', value=ban_reason)
            embed.add_field(name='Причина разбана:', value=unban_reason)
            await channel.send(embed=embed)

class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='разбан', description='Показать модуль с небольшим опросом для разбана пользователя')
    async def unban(self, interaction: discord.Interaction):
        view = UnbanModal()
        view.bot = self.bot
        await interaction.response.send_modal(view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Unban(bot), guilds=bot.guilds)