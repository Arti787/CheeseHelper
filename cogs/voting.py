import discord
from discord import app_commands
from discord.ext import commands
import json


class VoteButton(discord.ui.Button):
    def __init__(self, option, bot):
        super().__init__(label=option,
                         style=discord.ButtonStyle.green if option == '✅' else discord.ButtonStyle.red if option == '❌' else discord.ButtonStyle.grey,
                         custom_id=f'vote_{option}')
        self.option = option
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        view = self.view
        if self.custom_id == 'vote_end':
            if user.id != view.author.id:
                await interaction.response.send_message(f'Вы не являетесь автором голосования.',
                                                        ephemeral=True)
                return

            view.active = False
            embed = view.get_embed(discord.Colour.red(), view.active)
            try:
                await interaction.response.send_message('Голосование закончилось.')
            except:
                await interaction.response.send_message('Голосование закончилось.', ephemeral=True)

            view.clear_items()
            await interaction.message.edit(embed=embed, view=view)
            manager = VoteManager(self.bot)  # создаем экземпляр VoteManager
            manager.views[view.message_id] = view  # обновляем голосование в атрибуте views через локальную переменную manager
            manager.save_votes()  # сохраняем голосование в файл через локальную переменную manager
            return

        if user.id in view.votes[self.option]:
            view.votes[self.option].remove(user.id)
            await interaction.response.send_message(f'Вы отменили свой голос за {self.option}.',
                                                    ephemeral=True)
        else:
            for other_option in view.options:
                view.votes[other_option].discard(user.id)
            view.votes[self.option].add(user.id)
            await interaction.response.send_message(f'Вы проголосовали за {self.option}.',
                                                    ephemeral=True)

        manager = VoteManager(self.bot)
        manager.views[view.message_id] = view
        manager.save_votes()
        embed = view.get_embed(discord.Colour.green(), view.active)
        await interaction.message.edit(embed=embed, view=view)



class VoteView(discord.ui.View):
    def __init__(self, title, bot):
        super().__init__(timeout=None)
        self.title = title
        self.bot = bot
        self.description = None
        self.options = ['✅', '❌', '⛔']
        self.votes = {option: set() for option in self.options}
        self.active = True
        self.message_id = None
        self.author = None
        for option in self.options:
            button = VoteButton(option, bot)
            self.add_item(button)
        end_button = VoteButton('Закончить голосование', bot)
        end_button.custom_id = 'vote_end'
        end_button.style = discord.ButtonStyle.blurple
        self.add_item(end_button)

    def get_results(self):
        total = sum(len(votes) for votes in self.votes.values())
        if total == 0:
            return 'Никто не проголосовал.'
        if self.active:
            return f'Всего проголосовало: {total}'
        results = [f'{option} - {len(votes)} голосов ({round(len(votes) / total * 100, 2)}%)' for option, votes in
                   self.votes.items()]
        return '\n'.join(results)

    def get_embed(self, colour, active):
        with open("votes.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        row = None

        for item in data:
            if item["message_id"] == self.message_id:
                row = item
                break

        if row:  # если словарь есть в списке
            title = row["title"]
            description = row["description"]
            author_id = row["author_id"]
            user = self.bot.get_user(author_id)
            author_name = user.name
            author_avatar = user.avatar.url
            results = row["votes"]
            total = sum(len(votes) for votes in row["votes"].values())
            if total == 0:
                results = 'Никто не проголосовал.'
            elif active:
                results = f'Всего проголосовало: {total}'
            else:
                results = [f'{option} - {len(votes)} голосов ({round(len(votes) / total * 100, 2)}%)' for option, votes
                           in
                           row["votes"].items()]
                results = '\n'.join(results)

            print(results)

        else:  # если словаря нет в списке
            title = self.title
            description = self.description
            author_id = self.author.id
            author_name = self.author.display_name
            author_avatar = self.author.avatar.url
            results = self.get_results()

        embed = discord.Embed(title=title, description=description,
                              colour=colour)  # создаем embed с полученными данными
        embed.set_author(name=author_name, icon_url=author_avatar)  # устанавливаем имя и аватар автора в embed
        embed.add_field(name='Результаты:', value=results)  # добавляем поле с результатами в embed
        return embed  # возвращаем embed


class VoteManager:
    def __init__(self, bot):
        self.views = bot.ctx.VoteValues  # создаем атрибут views
        self.bot = bot

    def save_votes(self):
        data = [self.view_to_dict(view) for view in self.views.values()]
        with open("votes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load_votes(self):
        try:
            with open("votes.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return

        for item in data:
            view = self.dict_to_view(item)
            self.views[view.message_id] = view

    @staticmethod
    def view_to_dict(view):
        return {
            "title": view.title,
            "description": view.description,
            "options": view.options,
            "votes": {option: list(votes) for option, votes in view.votes.items()},
            "active": view.active,
            "message_id": view.message_id,
            "author_id": view.author.id,
        }

    def dict_to_view(self, data):
        view = VoteView(data["title"], self.bot)
        view.description = data["description"]
        view.options = data["options"]
        view.votes = {option: set(votes) for option, votes in data["votes"].items()}
        view.active = data["active"]
        view.message_id = data["message_id"]
        view.author = discord.Object(id=data["author_id"])
        return view


class voting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("voiting")

        manager = VoteManager(self.bot)  # создаем экземпляр VoteManager

        manager.load_votes()  # загружаем голосования из файла через локальную переменную manager

        for message_id in manager.views:  # добавляем голосования в бота для каждого message_id через локальную переменную manager
            view = manager.views[message_id]
            self.bot.add_view(view)

    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands")

    @app_commands.command(name="голосование", description="Начать голосование по заданной теме")
    @app_commands.describe(title="Сюда вводится тема голосования (заголовок)",description="Сюда вводится описание голосования (основная суть)")
    async def voit(self, interaction: discord.Interaction, title: str, description: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1,2,3,5,69,20")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return

        view = VoteView(title, self.bot)
        view.author = interaction.user
        view.description = description
        view.title = title
        embed = view.get_embed(discord.Colour.green(), True)
        message = await interaction.response.send_message(embed=embed, view=view)
        view.message_id = view.id  # исправляем ошибку с присвоением id сообщения
        manager = VoteManager(self.bot)  # создаем экземпляр VoteManager
        manager.views[
            view.message_id] = view  # добавляем голосование в атрибут views через локальную переменную manager
        manager.save_votes()  # сохраняем голосование в файл через локальную переменную manager


async def setup(bot: commands.Bot):
    guilds_count = len(bot.guilds)
    if guilds_count > 0:
        await bot.add_cog(voting(bot), guilds=bot.guilds)
    else:
        await bot.add_cog(voting(bot), guilds=[discord.Object(id=889846652893011998)])