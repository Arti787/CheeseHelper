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
            embed = discord.Embed(title=view.title, description=view.description)
            embed.set_author(name=view.author.display_name, icon_url=view.author.avatar.url)
            embed.colour = discord.Colour.red()
            embed.add_field(name='Результаты:', value=view.get_results())
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
                if user in view.votes[other_option]:
                    view.votes[other_option].remove(user)
            view.votes[self.option].append(user)
            await interaction.response.send_message(f'Вы проголосовали за {self.option}.',
                                      ephemeral=True)
        embed = discord.Embed(title=view.title, description=view.description)
        embed.set_author(name=view.author.display_name, icon_url=view.author.avatar.url)
        embed.add_field(name='Результаты:', value=view.get_results())
        await interaction.message.edit(embed=embed, view=view)

        if view.active:
            embed.colour = discord.Colour.green()
        else:
            embed.colour = discord.Colour.red()
        await interaction.message.edit(embed=embed, view=view)


class VoteView(discord.ui.View):
    def __init__(self, title):
        super().__init__(timeout=None)
        self.title = title
        self.description = None
        self.options = ['✅', '❌', '⛔']
        self.votes = {option: [] for option in self.options}
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
            return 'Никто еще не проголосовал.'
        if self.active:
            return f'Всего проголосовало: {total}'
        results = []
        for option, votes in self.votes.items():
            count = len(votes)
            percent = round(count / total * 100, 2)
            results.append(f'{option} - {count} голосов ({percent}%)')
        return '\n'.join(results)

class voting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("ИНИИт")

    @commands.Cog.listener()
    async def on_ready(self):
        print("voiting")

    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands")

    @app_commands.command(name="голосование", description="Начать голосование по заданной теме")
    @app_commands.describe(title="Сюда вводится тема голосования (заголовок)", description="Сюда вводится описание голосования (основная суть)")
    async def voit(self, interaction: discord.Interaction, title: str, description: str):
        if (str(interaction.user.id) not in self.bot.multi_variable.admins) and (not self.bot.check_roles(interaction.user, "1,5")):
                await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
                return

        view = VoteView(title)
        view.author = interaction.user
        view.description = description
        view.title = title
        embed = discord.Embed(title=view.title, description=view.description)
        embed.set_author(name=view.author.display_name, icon_url=view.author.avatar.url)
        embed.colour = discord.Colour.green()
        message = await interaction.response.send_message(embed=embed, view=view)
        view.message_id = message.id
        self.bot.add_view(view, message_id=message.id)


async def setup(bot: commands.Bot):
    print("СЕТАП")
    guilds_count = len(bot.guilds)
    if guilds_count > 0:
        await bot.add_cog(voting(bot), guilds=bot.guilds)
    else:
        await bot.add_cog(voting(bot), guilds=[discord.Object(id=889846652893011998)])
