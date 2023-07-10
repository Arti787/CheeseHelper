import discord
from discord import app_commands
from discord.ext import commands

class VoteButton(discord.ui.Button):
    def __init__(self, option):
        super().__init__(label=option,
                         style=discord.ButtonStyle.green if option == '✅' else discord.ButtonStyle.red if option == '❌' else discord.ButtonStyle.grey,
                         custom_id=f'vote_{option}')
        self.option = option

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        view = self.view
        if self.custom_id == 'vote_end':
            if user != view.author:
                await interaction.response.send_message(f'Вы не являетесь автором голосования.',
                                                        ephemeral=True)
                return

            view.active = False
            embed = view.get_embed(discord.Colour.red())
            try:
                await interaction.response.send_message('Голосование закончилось.')
            except:
                await interaction.response.send_message('Голосование закончилось.', ephemeral=True)

            view.clear_items()
            await interaction.message.edit(embed=embed, view=view)
            return

        if user in view.votes[self.option]:
            view.votes[self.option].remove(user)
            await interaction.response.send_message(f'Вы отменили свой голос за {self.option}.',
                                      ephemeral=True)
        else:
            for other_option in view.options:
                view.votes[other_option].discard(user)
            view.votes[self.option].add(user)
            await interaction.response.send_message(f'Вы проголосовали за {self.option}.',
                                      ephemeral=True)
        embed = view.get_embed(discord.Colour.green())
        await interaction.message.edit(embed=embed, view=view)

class VoteView(discord.ui.View):
    def __init__(self, title):
        super().__init__(timeout=None)
        self.title = title
        self.description = None
        self.options = ['✅', '❌', '⛔']
        self.votes = {option: set() for option in self.options}
        self.active = True
        self.message_id = None
        self.author = None
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

    def get_embed(self, colour):
        embed = discord.Embed(title=self.title, description=self.description, colour=colour)
        embed.set_author(name=self.author.display_name, icon_url=self.author.avatar.url)
        embed.add_field(name='Результаты:', value=self.get_results())
        return embed

class voting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def on_ready(self):
        print("voiting")

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

        view = VoteView(title)
        view.author = interaction.user
        view.description = description
        view.title = title
        embed = view.get_embed(discord.Colour.green())
        message = await interaction.response.send_message(embed=embed, view=view)
        view.message_id = message.id
        self.bot.add_view(view, message_id=message.id)

async def setup(bot: commands.Bot):
    await bot.add_cog(voting(bot), guilds=bot.guilds)
