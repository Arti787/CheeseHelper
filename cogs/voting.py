import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class VoteManager:
    def __init__(self, bot, filename="votes.json"):
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
            "author_id": vote.author_id
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
                return vote
        return None


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

            view.active = False
            VM = VoteManager(view.bot)
            VM.save_vote(view)
            embed = await view.get_embed(discord.Colour.red())
            await interaction.response.send_message('Голосование закончилось.')

            view.clear_items()
            await interaction.message.edit(embed=embed, view=view)
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
        VM = VoteManager(view.bot)
        VM.save_vote(view)
        embed = await view.get_embed(discord.Colour.green())
        await interaction.message.edit(embed=embed, view=view)

class VoteView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.title = None
        self.description = None
        self.options = ['✅', '❌', '⛔']
        self.votes = {option: set() for option in self.options}
        self.active = True
        self.message_id = None
        self.author_id = None
        for option in self.options:
            button = VoteButton(option)
            self.add_item(button)
        end_button = VoteButton('Закончить голосование')
        end_button.custom_id = 'vote_end'
        end_button.style = discord.ButtonStyle.blurple
        self.add_item(end_button)

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
        embed.add_field(name='Результаты:', value=self.get_results())
        return embed


class voting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("voiting")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            component_interaction_data = interaction.data['custom_id']

            if component_interaction_data.find("vote_", 0)  != -1:
                VM = VoteManager(self.bot)
                view = VM.load_vote(interaction.message.id)
                if view != None:
                    for i in range(len(view.children)):
                        value = view.children[i]
                        if value.custom_id == component_interaction_data:
                            await VoteButton.callback(view.children[i], interaction)


    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands")

    @app_commands.command(name="голосование", description="Начать голосование по заданной теме")
    @app_commands.describe(title="Сюда вводится тема голосования (заголовок)", description="Сюда вводится описание голосования (основная суть)")
    async def voit(self, interaction: discord.Interaction, title: str, description: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1,2,3,5,69")
        if not(check_1 or check_2):
                await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
                return

        view = VoteView(self.bot)
        view.author_id = interaction.user.id
        view.description = description
        view.title = title
        embed = await view.get_embed(discord.Colour.green())
        message = await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(voting(bot), guilds=bot.guilds)