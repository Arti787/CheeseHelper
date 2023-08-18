import discord
from discord import ui, app_commands
from discord.ext import commands
from discord.ext.commands import Context
import json
import os

class VoteManager:
    def __init__(self, bot, filename="unban_votes.json"):
        self.filename = filename
        self.bot = bot

    def save_vote(self, vote):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        vote_dict = {
            "user_id": vote.user_id,
            "ban_date": vote.ban_date,
            "ban_reason": vote.ban_reason,
            "unban_reason": vote.unban_reason,
            "votes": {option: list(vote.votes[option]) for option in vote.options},
            "active": vote.active,
            "thread_id": vote.thread_id,
            "message_id": vote.message_id,
            "close_time": vote.close_time,
        }
        found = False
        for i in range(len(data)):
            if data[i]["thread_id"] == vote.thread_id:
                data[i] = vote_dict
                found = True
                break
        if not found:
            data.append(vote_dict)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load_vote(self, thread_id):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return None
        for vote_dict in data:
            if vote_dict["thread_id"] == thread_id:
                vote = VoteView(self.bot)
                vote.ban_date = vote_dict["ban_date"]
                vote.ban_reason = vote_dict["ban_reason"]
                vote.unban_reason = vote_dict["unban_reason"]

                vote.votes = {option: set(vote_dict["votes"][option]) for option in vote.options}
                vote.active = vote_dict["active"]
                vote.thread_id = vote_dict["thread_id"]
                vote.message_id = vote_dict["thread_id"]
                vote.user_id = vote_dict["user_id"]
                vote.close_time = vote_dict["close_time"]
                return vote
        return None
    def update_view(self, view):

        for option in view.options:
            button = VoteButton(option)
            view.add_item(button)

        settings_button = VoteButton('🔧')
        settings_button.custom_id = 'vote_🔧'
        settings_button.style = discord.ButtonStyle.blurple
        view.add_item(settings_button)

        end_button = VoteButton('Закончить голосование')
        end_button.custom_id = 'vote_end'
        end_button.style = discord.ButtonStyle.blurple
        view.add_item(end_button)
        return view


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

        with open("unban_votes.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if str(interaction.user.id) in str(data):
            await interaction.response.send_message(f'У вас уже есть действующий тикет на разбан', ephemeral=True)
            return

        await interaction.response.send_message(f'Спасибо за ваш ответ!', ephemeral=True)
        # Создаем приватную ветку в категории с id 1111696778862014524
        category = self.bot.get_channel(1111696778862014524)
        if category is not None:
            thread = await category.create_thread(name=f"Тикет {interaction.user.display_name}", type=discord.ChannelType.private_thread)
            # Попытаться получить объект участника по его идентификатору
            user = await self.bot.fetch_user(360162170174177280)
            # Добавить участника в поток
            await thread.add_user(user)

            # Пингуем всех в ветке и отправляем результаты опроса
            embed = discord.Embed(title=f'Опрос о разбане пользователя {interaction.user}', colour=discord.Colour.green())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url)
            embed.add_field(name='Дата бана:', value=ban_date)
            embed.add_field(name='Причина бана:', value=ban_reason)
            embed.add_field(name='Причина разбана:', value=unban_reason)
            await thread.send(f'<@&1125082611631534090>', embed=embed)

            vote_view = VoteView(self.bot)
            vote_view.user_id = interaction.user.id
            vote_view.ban_date = ban_date
            vote_view.ban_reason = ban_reason
            vote_view.unban_reason = unban_reason
            vote_view.thread_id = thread.id

            descript = f"Разбанивать ли участника {vote_view.user_id}?"
            embed = discord.Embed(title="Голосование", description=descript, color=discord.Colour.green())
            embed.set_footer(text="Заявка пользователя будет отклонена на месяц, в случае отказа")

            VM = VoteManager(self.bot)
            VM.save_vote(vote_view)
            vote_view.message = await thread.send(embed=embed, view=vote_view)
            view = CloseTicketView(self.bot)
            embed = discord.Embed(title="Нажми кнопку ниже, чтобы завершить голосование и закрыть тикет.", colour=discord.Colour.red())
            await thread.send(embed=embed, view=view)


# Создаем класс для кнопки принятия голосования
class AcceptButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="✅", style=discord.ButtonStyle.green, custom_id="unban_YES")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        VM = VoteManager(self.bot)
        view = VM.load_vote(interaction.channel.id)
        if interaction.user.id in view.votes["❌"]:
            view.votes["❌"].remove(interaction.user.id)
        if interaction.user.id not in view.votes["✅"]:
            view.votes["✅"].add(interaction.user.id) # Используем add вместо append
            await interaction.response.send_message(f"Вы проголосовали за разбан.", ephemeral=True)
        else:
            view.votes["✅"].remove(interaction.user.id)
            await interaction.response.send_message(f"Вы отменили голос за разбан.", ephemeral=True)

        view.thread_id = interaction.channel.id
        view.message_id = interaction.message.id
        VM.save_vote(view)
        await view.update_embed(interaction)


# Создаем класс для кнопки отклонения голосования
class RejectButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="❌", style=discord.ButtonStyle.red, custom_id="unban_NO")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        VM = VoteManager(self.bot)
        view = VM.load_vote(interaction.channel.id)
        if interaction.user.id in view.votes["✅"]:
            view.votes["✅"].remove(interaction.user.id)
        if interaction.user.id not in view.votes["❌"]:
            view.votes["❌"].add(interaction.user.id)  # Используем add вместо append
            await interaction.response.send_message(f"Вы проголосовали против разбана.", ephemeral=True)
        else:
            view.votes["❌"].remove(interaction.user.id)
            await interaction.response.send_message(f"Вы отменили голос против разбана.", ephemeral=True)
        view.thread_id = interaction.channel.id
        view.message_id = interaction.message.id
        VM.save_vote(view)
        await view.update_embed(interaction)

# Создаем класс для вида с кнопками голосования
class VoteView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.message = None
        self.options = ['✅', '❌']
        self.user_id = None
        self.ban_date = None
        self.ban_reason = None
        self.unban_reason = None
        self.votes = {option: set() for option in self.options}
        self.active = True
        self.thread_id = None
        self.message_id = None
        self.close_time = None

        self.add_item(AcceptButton(self.bot))
        self.add_item(RejectButton(self.bot))

    async def update_embed(self, interaction: discord.Interaction):
        thread = interaction.channel
        members = await thread.fetch_members()
        # Фильтруем список участников по роли с id 1125082611631534090
        yes_count = len(self.votes["✅"])
        no_count = len(self.votes["❌"])
        total_role = len(self.votes)
        total_count = yes_count + no_count
        yes_percent = 0
        no_percent = 0
        try:
            yes_percent = round(yes_count / total_count * 100, 1)
        except:
            None
        try:
            no_percent = round(no_count / total_count * 100, 1)
        except:
            None

        descript = f"Разбанивать ли участника {self.user_id}?"
        embed = discord.Embed(title="Голосование", description=descript, color=discord.Colour.green())
        embed.set_footer(text="Заявка пользователя будет отклонена на месяц, в случае отказа")
        embed.add_field(name="Результаты:", value=f"✅ - {yes_count} голосов ({yes_percent}%)\n❌ - {no_count} голосов ({no_percent}%)")
        await interaction.message.edit(embed=embed)
        if total_count == total_role:
            self.stop()


# Создаем класс для кнопки закрытия тикета
class CloseTicketButton(ui.Button):
    def __init__(self, bot: commands.Bot):
        super().__init__(label="Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        VM = VoteManager(self.bot)
        vote_view = VM.load_vote(interaction.channel.id)
        thread = interaction.channel
        members = await thread.fetch_members()
        # Удаляем из ветки всех участников, которые не имеют роль с id 1125082611631534090
        '''
        for member in members:
            guild_member = thread.guild.get_member(member.id)
            if not guild_member._roles.has(1125082611631534090):
                await thread.remove_user(member)
        '''

        guild_ids = [
            691788414101618819,  # Сай и его Фыр
            856978727972110356,  # Майнкрафт сервер
            865194554252591104,  # Хаб общий
            975557824287506443,  # Хорни сервер
            880581161133416480,  # Арт мастер
            795643820800213012,  # РП сервер
            932050265975193611,  # Сервер забаненых
            1114227136199405591, # Сервер Тестирование бота CheeseHelper
            1142152375440785410  # Сервер БАНОВ
        ]
        yes_count = len(vote_view.votes["✅"])
        no_count = len(vote_view.votes["❌"])
        total_role = len(vote_view.votes)
        total_count = yes_count + no_count
        yes_percent = 0
        no_percent = 0
        try:
            yes_percent = round(yes_count / total_count * 100, 1)
        except:
            None
        try:
            no_percent = round(no_count / total_count * 100, 1)
        except:
            None


        # await thread.send(f'Тикет был закрыт.')
        vote_view.clear_items()

        # message = await interaction.channel.fetch_message(vote_view.message_id)
        #
        # await message.edit(view=vote_view)
        await interaction.message.edit(view=vote_view)
        await thread.edit(name=f"(закрыто) {thread.name}")

        if yes_percent > 50:
            await self.UnbanBaban(interaction, guild_ids, vote_view.user_id)
        else:
            await thread.send(f'Разбан пользователя был отклонён')
            await interaction.response.send_message(f'Тикет успешно закрыт.', ephemeral=True)

    async def UnbanBaban(self,interaction, server_ids, user_id):
        user = await self.bot.fetch_user(user_id)
        # перебрать серверы из списка по id
        for server_id in server_ids:
            # получить объект сервера по id
            server = self.bot.get_guild(server_id)
            # проверить, существует ли такой сервер
            if server is None:
                continue  # перейти к следующему серверу
            # попытаться разбанить пользователя на сервере
            try:
                await server.unban(user)  # разбанить пользователя на сервере
                await interaction.channel.send(f'Пользователь {user.name}(id: {user.id}) успешно разблокирован на сервере {server.name}')  # отправить сообщение об успешном разбане
                break  # прервать цикл
            except discord.NotFound:
                continue  # перейти к следующему серверу
            except discord.Forbidden:
                await interaction.channel.send(f"У бота нет разрешения на разбан пользователя {user.mention} на сервере {server.name}")  # отправить сообщение об ошибке
                break  # прервать цикл



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

    @app_commands.command(name='разбан', description='Показать ембед с кнопкой для открытия тикета на аппеляцию')
    async def unban(self, interaction: discord.Interaction):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1,20")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        view = OpenTicketView(self.bot)

        embed = discord.Embed(title="Нажми на кнопку, чтобы открыть тикет на аппеляцию", colour=discord.Colour.from_rgb(0, 214, 255))
        # Отправляем ембед и вид в канал с id 1111696778862014524
        channel = self.bot.get_channel(1111696778862014524)
        if channel is not None:
            await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            component_interaction = interaction.data
            if component_interaction['custom_id'] == "open_ticket_button":
                await OpenTicketButton.callback(self, interaction)
            if component_interaction['custom_id'] == "close_ticket_button":
                await CloseTicketButton.callback(self, interaction)
                print("мяу")
            if component_interaction['custom_id'] == "unban_YES":

                VM = VoteManager(self.bot)
                vote_view = VM.load_vote(interaction.channel.id)
                if vote_view != None:
                    await AcceptButton.callback(self.vote_view.children[0], interaction)

            if component_interaction['custom_id'] == "unban_NO":
                VM = VoteManager(self.bot)
                vote_view = VM.load_vote(interaction.channel.id)
                if vote_view != None:
                    await RejectButton.callback(self.vote_view.children[1], interaction)

            '''
            {"user_id": null, "ban_date": null, "ban_reason": null, "unban_reason": null,
             "votes": {"✅": [360162170174177280], "❌": []}, "active": true, "thread_id": null, "close_time": null}
            '''

async def setup(bot: commands.Bot):
    await bot.add_cog(Unban(bot), guilds=bot.guilds)