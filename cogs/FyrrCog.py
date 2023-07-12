import discord
from discord import app_commands
from discord.ext import commands

# скрипт для демонстрации постоянных кнопок даже после перезапуска бота. Источник решения проблемы:
# https://stackoverflow.com/questions/75522323/the-button-resets-after-restarting-the-bot-in-discord-py

class FyrrButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Фырр", style=discord.ButtonStyle.green, custom_id="fyrr_button") # Добавил custom_id для кнопки

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Фыырр", ephemeral=True)

class FyrrView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FyrrButton())

class FyrrCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.fyrr_views = {} # A dictionary to store the fyrr views by channel id

    @commands.Cog.listener()
    async def on_ready(self):
        print("Fyrr cog ready")
        self.bot.add_view(FyrrView()) # Добавил эту строку, чтобы зарегистрировать вид для постоянства

    @commands.Cog.listener()
    async def on_interaction_create(self, interaction: discord.Interaction):
        # Check if the interaction is a button click
        if interaction.type == discord.InteractionType.component:
            # Check if the button custom_id matches the fyrr button
            if interaction.custom_id == "fyrr_button":
                # Call the callback function of the fyrr button
                await FyrrButton().callback(interaction)

    @commands.command(name="фыр")
    async def fyrr(self, ctx: commands.Context):
        # Check if there is already a fyrr view in the same channel
        if ctx.channel.id in self.fyrr_views:
            await ctx.send("Такая кнопка уже есть в этом канале")
            return
        # Create a new fyrr view and send it to the channel
        view = FyrrView()
        await ctx.send("Нажми на кнопку, чтобы сказать фырр", view=view)
        # Store the fyrr view in the dictionary by channel id
        self.fyrr_views[ctx.channel.id] = view

# Create an async setup function for the cog
async def setup(bot: commands.Bot):
    await bot.add_cog(FyrrCog(bot))
