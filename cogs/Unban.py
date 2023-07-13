import discord
from discord import ui, app_commands
from discord.ext import commands
from discord.ext.commands import Context

class UnbanModal(ui.Modal, title='Податься на разбан'):
    ban_date = ui.TextInput(label='Дата бана', placeholder='Введите дату бана в формате ДД.ММ.ГГГГ')
    ban_reason = ui.TextInput(label='Причина бана', placeholder='Введите причину бана, указанную при бане')
    unban_reason = ui.TextInput(label='Почему мы должны снять бан?', placeholder='Пишите в этом пункте всё, что посчитаете нужным. Больше слов по делу - больше шанс на разбан', style=discord.TextStyle.paragraph)

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        ban_date = self.ban_date.value
        ban_reason = self.ban_reason.value
        unban_reason = self.unban_reason.value
        await interaction.response.send_message(f'Спасибо за ваш ответ!', ephemeral=True)
        # Создаем приватную ветку в категории с id 1114259348898713620
        category = self.bot.get_channel(1128516574593171566)
        if category is not None:
            thread = await category.create_thread(name=f"Тикет {interaction.user.display_name}", type=discord.ChannelType.private_thread)
            await thread.add_user(interaction.user)
            # Пингуем всех в ветке и отправляем результаты опроса
            embed = discord.Embed(title=f'Опрос о разбане пользователя {interaction.user}', colour=discord.Colour.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
            embed.add_field(name='Дата бана:', value=ban_date)
            embed.add_field(name='Причина бана:', value=ban_reason)
            embed.add_field(name='Причина разбана:', value=unban_reason)
            await thread.send(f'<@&1128517778320666784>', embed=embed)

            descript = f"Разбанивать ли участника?"
            embed = discord.Embed(title="Голосование", description=descript, color=discord.Colour.green())
            embed.set_footer(text="Заявка пользователя будет отклонена на месяц, в случае отказа")

            vote_view = VoteView(self.bot)
            vote_view.message = await thread.send(embed=embed, view=vote_view)
            view = CloseTicketView(self.bot)
            embed = discord.Embed(title="Нажми кнопку ниже, чтобы завершить голосование и закрыть тикет.", colour=discord.Colour.red())
            await thread.send(embed=embed, view=view)

# Создаем класс для кнопки принятия голосования
class AcceptButton(ui.Button):
    def __init__(self):
        super().__init__(label="✅", style=discord.ButtonStyle.green, custom_id="vote_YES")

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user in view.votes_no:
            view.votes_no.remove(interaction.user)
        if interaction.user not in view.votes_yes:
            view.votes_yes.append(interaction.user)
        await view.update_embed(interaction)
        await interaction.response.send_message(f"Вы проголосовали за разбан.", ephemeral=True)

# Создаем класс для кнопки отклонения голосования
class RejectButton(ui.Button):
    def __init__(self):
        super().__init__(label="❌", style=discord.ButtonStyle.red, custom_id="vote_NO")

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if interaction.user in view.votes_yes:
            view.votes_yes.remove(interaction.user)
        if interaction.user not in view.votes_no:
            view.votes_no.append(interaction.user)
        await view.update_embed(interaction)
        await interaction.response.send_message(f"Вы проголосовали против разбана.", ephemeral=True)

# Создаем класс для вида с кнопками голосования
class VoteView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = None
        self.votes_yes = self.bot.ctx.unban_votes_yes
        self.votes_no = self.bot.ctx.unban_votes_no
        self.add_item(AcceptButton())
        self.add_item(RejectButton())

    async def update_embed(self, interaction: discord.Interaction):
        thread = interaction.channel
        members = await thread.fetch_members()
        # Фильтруем список участников по роли с id 1128517778320666784
        voters = [member for member in members if thread.guild.get_member(member.id)._roles.has(1128517778320666784)]
        yes_count = len(self.votes_yes)
        no_count = len(self.votes_no)
        total_role = len(voters)
        total_count = yes_count + no_count
        yes_percent = round(yes_count / total_count * 100, 1)
        no_percent = round(no_count / total_count * 100, 1)

        descript = f"Разбанивать ли участника?"
        embed = discord.Embed(title="Голосование", description=descript, color=discord.Colour.green())
        embed.set_footer(text="Заявка пользователя будет отклонена на месяц, в случае отказа")
        embed.add_field(name="Результаты:", value=f"✅ - {yes_count} голосов ({yes_percent}%)\n❌ - {no_count} голосов ({no_percent}%)")
        await interaction.message.edit(embed=embed)
        self.bot.ctx.unban_vote_view_interaction = interaction
        if total_count == total_role:
            self.stop()


# Создаем класс для кнопки закрытия тикета
class CloseTicketButton(ui.Button):
    def __init__(self, bot: commands.Bot):
        super().__init__(label="Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        vote_view = VoteView(self.bot)
        thread = interaction.channel
        members = await thread.fetch_members()
        # Удаляем из ветки всех участников, которые не имеют роль с id 1128517778320666784
        for member in members:
            guild_member = thread.guild.get_member(member.id)
            if not guild_member._roles.has(1128517778320666784):
                await thread.remove_user(member)

        await interaction.response.send_message(f'Тикет успешно закрыт.', ephemeral=True)
        await thread.send(f'Тикет был закрыт.')
        vote_view.clear_items()
        await self.bot.ctx.unban_vote_view_interaction.message.edit(view=vote_view)
        await interaction.message.edit(view=vote_view)
        await thread.edit(name=f"{thread.name} (закрыто)")


# Создаем класс для вида с кнопкой закрытия тикета
class CloseTicketView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton(bot))

# Создаем класс для кнопки открытия тикета
class OpenTicketButton(ui.Button):
    def __init__(self, bot: commands.Bot):
        super().__init__(label="Открыть тикет", style=discord.ButtonStyle.primary, custom_id="open_ticket_button")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        view = UnbanModal(self.bot)
        await interaction.response.send_modal(view)

# Создаем класс для вида с кнопкой открытия тикета
class OpenTicketView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.add_item(OpenTicketButton(bot))

class Unban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vote_view = VoteView(self.bot)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Unban cog ready")
        self.bot.add_view(OpenTicketView(self.bot))
        self.bot.add_view(VoteView(self.bot))

    @app_commands.command(name='разбан', description='Показать ембед с кнопкой для открытия тикета на аппеляцию')
    async def unban(self, interaction: discord.Interaction):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1,20")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        view = OpenTicketView(self.bot)

        embed = discord.Embed(title="Нажми на кнопку, чтобы открыть тикет на аппеляцию", colour=discord.Colour.from_rgb(0, 214, 255))
        # Отправляем ембед и вид в канал с id 1114234886077825124
        channel = self.bot.get_channel(1114234886077825124)
        if channel is not None:
            await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            component_interaction = interaction.data
            if component_interaction['custom_id'] == "close_ticket_button":
                await CloseTicketButton.callback(self, interaction)

            if component_interaction['custom_id'] == "vote_YES":
                await AcceptButton.callback(self.vote_view.children[0], interaction)
            if component_interaction['custom_id'] == "vote_NO":
                await RejectButton.callback(self.vote_view.children[1], interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(Unban(bot), guilds=bot.guilds)