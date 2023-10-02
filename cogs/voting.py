import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os

class AddOptionsModal(ui.Modal, title='Свои варианты'):
    Option_1 = ui.TextInput(label='Вариант 1', placeholder='Введите сюда эмодзи либо короткий текст', max_length = 30, required = True)
    Option_2 = ui.TextInput(label='Вариант 2', placeholder='Введите сюда эмодзи либо короткий текст', max_length = 30, required = True)
    Option_3 = ui.TextInput(label='Вариант 3', placeholder='Введите сюда эмодзи либо короткий текст', max_length = 30, required = False)
    Option_4 = ui.TextInput(label='Вариант 4', placeholder='Введите сюда эмодзи либо короткий текст', max_length = 30, required = False)
    Option_5 = ui.TextInput(label='Дополнительные варианты', placeholder='Введите сюда доп. варианты через запятую', max_length = 150, required = False)

    def __init__(self, view):
        super().__init__(timeout=None)
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        # Создаем список из значений опций
        options = [self.Option_1.value, self.Option_2.value, self.Option_3.value, self.Option_4.value]
        if self.Option_5.value: # если есть дополнительные варианты
            options.extend(self.Option_5.value.split(',')) # добавляем их к списку
        options = [option.strip() for option in options] # убираем пробелы в начале и конце каждого варианта
        options = [option for option in options if option != ""] # убираем пустые варианты
        options = list(dict.fromkeys(options)) # убираем повторяющиеся варианты

        self.view.options=[]
        self.view.options.extend(options)
        self.view.votes = {option: set() for option in self.view.options}
        self.view.clear_items()
        VM = VoteManager(self.view.bot)
        self.view = VM.update_view(self.view)

        print(self.view.options)
        VM = VoteManager(self.view.bot)
        VM.save_vote(self.view)
        embed = await self.view.get_embed(discord.Colour.green())
        await interaction.message.edit(embed=embed, view=self.view)
        await interaction.response.send_message(f'Вы успешно задали кастомные опции голосования',ephemeral=True)


class TitleDescriptionModal(ui.Modal, title='Ваше голосование'):
    Title = ui.TextInput(label='Заголовок', placeholder='Обозначте тему голосования', max_length = 100, required = True)
    Description = ui.TextInput(label='Описание', placeholder='Распишите ваше голосование подробнее :3', max_length = 2000, required = False)

    def __init__(self, view):
        super().__init__(timeout=None)
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        self.view.author_id = interaction.user.id
        self.view.title = self.Title.value
        if self.view.roles is not None:
            # Преобразуем список ролей в строку
            roles_str = ', '.join(f'<@&{role}>' for role in self.view.roles)
            if len(self.view.roles) > 1:
                self.view.description = f'К голосованию доступны лишь пользователи с ролями {roles_str}\n{self.Description.value}'
            else:
                self.view.description = f'К голосованию доступны лишь пользователи с ролью {roles_str}\n{self.Description.value}'
        else:
            self.view.description = self.Description.value
        embed = await self.view.get_embed(discord.Colour.green())
        await interaction.response.send_message(embed=embed, view=self.view)


class VoteManager:
    def __init__(self, bot, filename="data/votes.json"):
        self.filename = filename
        self.bot = bot

    def save_vote(self, vote):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        vote_dict = {
            "title": vote.title,
            "description": vote.description,
            "options": vote.options,
            "votes": {option: list(vote.votes[option]) for option in vote.options},
            "active": vote.active,
            "message_id": vote.message_id,
            "author_id": vote.author_id,
            "roles": vote.roles
        }
        found = False
        for i in range(len(data)):
            if data[i]["message_id"] == vote.message_id:
                data[i] = vote_dict
                found = True
                break
        if not found:
            data.append(vote_dict)
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load_vote(self, message_id):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return None
        for vote_dict in data:
            if vote_dict["message_id"] == message_id:
                vote = VoteView(self.bot)
                vote.title = vote_dict["title"]
                vote.description = vote_dict["description"]
                vote.options = vote_dict["options"]
                vote.votes = {option: set(vote_dict["votes"][option]) for option in vote.options}
                vote.active = vote_dict["active"]
                vote.message_id = vote_dict["message_id"]
                vote.author_id = vote_dict["author_id"]
                if 'roles' in vote_dict and isinstance(vote_dict['roles'], list):
                    vote.roles = vote_dict['roles']
                else:
                    vote.roles = None

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


class VoteButton(discord.ui.Button):
    def __init__(self, option):
        super().__init__(label=option,
                         style=discord.ButtonStyle.green if option == '✅' else discord.ButtonStyle.red if option == '❌' else discord.ButtonStyle.grey,
                         custom_id=f'vote_{option}')
        self.option = option

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        self.view.message_id = interaction.message.id
        view = self.view
        if self.custom_id == 'vote_end':
            if user.id != view.author_id:
                await interaction.response.send_message(f'Вы не являетесь автором голосования.',
                                                        ephemeral=True)
                return

            total_votes = sum(len(votes) for votes in view.votes.values())
            try:
                max_percent = max(len(votes) / total_votes for votes in view.votes.values())
            except:
                await interaction.response.send_message(f'Нельзя закончить голосование, пока никто не проголосовал',
                                                        ephemeral=True)
                return
            max_options = [option for option, votes in view.votes.items() if len(votes) / total_votes == max_percent]
            max_option = max_options[0]

            sorted_votes = sorted(view.votes.items(), key=lambda x: len(x[1]), reverse=True)

            sorted_options = [option for option, votes in sorted_votes]

            max_votes = len(view.votes[max_option])
            view.active = False
            VM = VoteManager(view.bot)
            VM.save_vote(view)
            view.clear_items()
            embed = await view.get_embed(discord.Colour.red())
            await interaction.message.edit(embed=embed, view=view)

            if len(max_options) == len(view.options):  # если все варианты набрали одинаковое кол-во голосов
                embed = discord.Embed(title=f'Голосование "**{view.title}**" закончилось.',
                                      description=f'Нет явного победителя, все варианты получили по **{max_votes}** голосов.',
                                      color=discord.Color.orange())
                await interaction.response.send_message(embed=embed)
                return
            elif len(max_options) > 1:  # если некоторые варианты набрали одинаковое кол-во голосов
                winners = ', '.join(f'"**{option}**"' for option in max_options)
                embed = discord.Embed(title=f'Голосование "**{view.title}**" закончилось.',
                                      description=f'Есть несколько победителей: {winners}\nГолосов за каждого из них: **{max_votes}** ({round(max_percent * 100, 1)}%)',
                                      color=discord.Color.green())
                await interaction.response.send_message(embed=embed)
                return
            else:  # если есть один победитель
                second_percent = sorted(len(votes) / total_votes for votes in view.votes.values())[
                    -2]  # процент голосов за второй вариант
                diff_percent = max_percent - second_percent  # разница в процентах между первым и вторым вариантом
                if diff_percent < 0.15:  # если разница меньше 15%
                    embed = discord.Embed(title=f'Голосование "**{view.title}**" закончилось.',
                                          description=f'Выигравший результат: "**{max_option}**"\nГолосов за него: **{max_votes}** ({round(max_percent * 100, 1)}%)\nОн оторвался от ближайшего варианта **{sorted_options[1]}** всего на {round(diff_percent * 100, 1)}%',
                                          color=discord.Color.blue())
                    await interaction.response.send_message(embed=embed)
                    return
                else:  # если разница больше или равна 10%
                    embed = discord.Embed(title=f'Голосование "**{view.title}**" закончилось.',
                                          description=f'Выигравший результат: "**{max_option}**"\nГолосов за него: **{max_votes}** ({round(max_percent * 100, 1)}%)',
                                          color=discord.Color.purple())
                    await interaction.response.send_message(embed=embed)
                    return

        if self.custom_id == 'vote_🔧':
            if user.id != view.author_id:
                await interaction.response.send_message(f'Вы не являетесь автором голосования.',
                                                        ephemeral=True)
                return
            await interaction.response.send_modal(AddOptionsModal(view))

        if view.roles != None:
            view_roles = [discord.utils.get(interaction.guild.roles, id=role_id) for role_id in view.roles]

            if view_roles is not None and not all(role in interaction.user.roles for role in view_roles):
                await interaction.response.send_message('У вас нет прав на это голосование.', ephemeral=True)
                return

        if user.id in view.votes[self.option]:
            view.votes[self.option].remove(user.id)
            await interaction.response.send_message(f'Вы отменили свой голос за "**{self.option}**".',
                                      ephemeral=True)
        else:
            for other_option in view.options:
                view.votes[other_option].discard(user.id)
            view.votes[self.option].add(user.id)
            await interaction.response.send_message(f'Вы проголосовали за "**{self.option}**".',
                                      ephemeral=True)
        VM = VoteManager(view.bot)
        VM.save_vote(view)
        embed = await view.get_embed(discord.Colour.green())
        await interaction.message.edit(embed=embed, view=view)

class VoteView(discord.ui.View):
    def __init__(self, bot, options = ['✅', '❌', '⛔']):
        super().__init__(timeout=None)
        self.bot = bot
        self.title = None
        self.description = None
        self.options = options
        self.custom_options = []
        self.active = True
        self.message_id = None
        self.author_id = None
        self.votes = {option: set() for option in self.options}
        self.roles = None
        VM = VoteManager(self.bot)
        self.clear_items()
        VM.update_view(self)

    def get_results(self):
        total = sum(len(votes) for votes in self.votes.values())
        if total == 0:
            return 'Никто не проголосовал.'
        if self.active:
            return f'Всего проголосовало: {total}'
        results = [f'{option} - {len(votes)} голосов ({round(len(votes) / total * 100, 2)}%)' for option, votes in self.votes.items()]
        return '\n'.join(results)

    async def get_embed(self, colour):
        user = await self.bot.fetch_user(self.author_id)
        embed = discord.Embed(title=self.title, description=self.description, colour=colour)
        embed.set_author(name=user.display_name, icon_url=user.avatar.url)
        if self.active == True:
            status = "Продолжается"
        else:
            status = "Закончилось"
        status = f"\n\nСтатус голосования:\n**{status}**"

        embed.add_field(name='Результаты:', value=self.get_results() + status)
        return embed


class voting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("voiting")

    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            component_interaction_data = interaction.data['custom_id']

            if component_interaction_data.find("vote_", 0) != -1:
                VM = VoteManager(self.bot)
                view = VM.load_vote(interaction.message.id)
                view.clear_items()
                view = VM.update_view(view)
                if view != None:
                    for i in range(len(view.children)):
                        value = view.children[i]
                        if value.custom_id == component_interaction_data:
                            await VoteButton.callback(view.children[i], interaction)

    @app_commands.command(name="голосование", description="Начать голосование по заданной теме")
    @app_commands.describe(role="Укажите через запятую все роли, которые имеют возможность голосовать")
    async def voit(self, interaction: discord.Interaction, role: str = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "6")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        view = VoteView(self.bot)
        if role is not None:
            role_ids = [role_id.strip() for role_id in role.split(',')]

            guild = interaction.guild
            role = []
            for role_id in role_ids:
                try:
                    role_id = int(role_id)
                    if discord.utils.get(guild.roles, id=role_id) is not None:
                        role.append(role_id)
                except ValueError:
                    continue

            role = list(set(role))

            if not role:
                role = None
        else:
            role = None

        view.roles = role

        await interaction.response.send_modal(TitleDescriptionModal(view))


async def setup(bot: commands.Bot):
    await bot.add_cog(voting(bot), guilds=bot.guilds)