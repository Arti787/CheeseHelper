# Импортируем необходимые библиотеки
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents(members=True, messages=True, message_content=True)
intents.guilds = True # Включаем право на просмотр серверов

# Создаем бота с префиксом !
bot = commands.Bot(command_prefix="!", intents=intents)

# Создаем категорию для приватных веток
category = discord.utils.get(bot.guilds[0].categories, name="Разбан")

# Создаем словарь для хранения анкет по разбану
applications = {}

# Создаем команду для создания кнопки по разбану
@bot.command()
async def create_button(ctx):
    # Создаем кнопку с надписью "Заполнить анкету по разбану"
    button = discord.ui.Button(label="Заполнить анкету по разбану", style=discord.ButtonStyle.green)
    # Добавляем обработчик нажатия на кнопку
    @button.callback
    async def on_button_click(interaction):
        # Открываем всплывающее окно с анкетой
        await open_application(interaction)
    # Отправляем сообщение с кнопкой в канал
    await ctx.send("Нажмите на кнопку, чтобы заполнить анкету по разбану", components=[button])

# Создаем функцию для открытия всплывающего окна с анкетой
async def open_application(interaction):
    # Получаем пользователя, который нажал на кнопку
    user = interaction.user
    # Проверяем, есть ли у него уже анкета по разбану
    if user.id in applications:
        # Если есть, то отправляем ему сообщение об этом
        await interaction.response.send_message("Вы уже заполнили анкету по разбану", ephemeral=True)
    else:
        # Если нет, то создаем новую анкету по разбану
        application = Application(user)
        # Добавляем ее в словарь анкет
        applications[user.id] = application
        # Отправляем пользователю сообщение с инструкцией по заполнению анкеты
        await interaction.response.send_message("Чтобы заполнить анкету по разбану, ответьте на следующие вопросы в личных сообщениях бота", ephemeral=True)
        # Отправляем пользователю первый вопрос из анкеты
        await application.ask_question()

# Создаем класс для представления анкеты по разбану
class Application:
    def __init__(self, user):
        # Сохраняем пользователя, который заполняет анкету
        self.user = user
        # Сохраняем список вопросов из анкеты
        self.questions = ["Какой у вас ник на сервере?", "Почему вы были забанены?", "Как вы объясняете свое поведение?"]
        # Сохраняем список ответов из анкеты
        self.answers = []
        # Сохраняем индекс текущего вопроса из анкеты
        self.index = 0

    # Создаем функцию для отправки вопроса пользователю
    async def ask_question(self):
        # Проверяем, есть ли еще вопросы в анкете
        if self.index < len(self.questions):
            # Если есть, то получаем текущий вопрос из списка вопросов
            question = self.questions[self.index]
            # Отправляем его пользователю в личные сообщения
            await self.user.send(question)
            # Увеличиваем индекс текущего вопроса на 1
            self.index += 1

    # Создаем функцию для получения ответа от пользователя
    async def get_answer(self, message):
        # Проверяем, является ли сообщение ответом на вопрос из анкеты
        if message.author == self.user and message.channel == self.user.dm_channel:
            # Если да, то добавляем ответ в список ответов
            self.answers.append(message.content)
            # Отправляем пользователю сообщение с подтверждением получения ответа
            await self.user.send("Ответ получен")
            # Отправляем пользователю следующий вопрос из анкеты
            await self.ask_question()
            # Проверяем, закончилась ли анкета
            if self.index == len(self.questions):
                # Если да, то отправляем пользователю сообщение с благодарностью за заполнение анкеты
                await self.user.send("Спасибо за заполнение анкеты по разбану")
                # Создаем приватную ветку для обсуждения анкеты
                await self.create_thread()
                # Отправляем анкету в канал отчетов
                await self.send_report()

    # Создаем функцию для создания приватной ветки для обсуждения анкеты
    async def create_thread(self):
        # Получаем канал, в котором была нажата кнопка по разбану
        channel = bot.get_channel(889846652893012002) # Замените на ID вашего канала
        # Создаем приватную ветку с названием в виде ника пользователя
        self.thread = await channel.start_thread(name=self.user.name, type=discord.ChannelType.private_thread)
        # Добавляем пользователя и комиссию в приватную ветку
        await self.thread.add_user(self.user)
        await self.thread.add_user(bot.get_user(360162170174177280)) # Замените на ID вашего члена комиссии
        # Отправляем анкету и причину бана в приватную ветку
        await self.thread.send(f"Анкета по разбану от {self.user.mention}")
        for question, answer in zip(self.questions, self.answers):
            await self.thread.send(f"{question}: {answer}")
        await self.thread.send(f"Причина бана: {self.get_ban_reason()}")

    # Создаем функцию для получения причины бана пользователя
    def get_ban_reason(self):
        # Здесь вы можете реализовать свою логику для определения причины бана
        # Например, вы можете проверить логи модерации или использовать API дискорда
        # В этом примере мы просто возвращаем "Нарушение правил"
        return "Нарушение правил"

    # Создаем функцию для отправки анкеты в канал отчетов
    async def send_report(self):
        # Получаем канал отчетов
        report_channel = bot.get_channel(1114259348898713620) # Замените на ID вашего канала отчетов
        # Отправляем анкету с личным делом, веткой и голосованием в канал отчетов
        report_message = await report_channel.send(f"Анкета по разбану от {self.user.mention}\nЛичное дело: {self.get_personal_file()}\nВетка: {self.thread.mention}\nГолосование:")
        # Добавляем реакции для голосования за разбан (👍) или против (👎)
        await report_message.add_reaction("👍")
        await report_message.add_reaction("👎")

    # Создаем функцию для получения личного дела пользователя
    def get_personal_file(self):
        # Здесь вы можете реализовать свою логику для получения личного дела пользователя
        # Например, вы можете проверить историю нарушений или использовать API дискорда
        # В этом примере мы просто возвращаем "Новичок"
        return "Новичок"

# Создаем обработчик события при получении сообщения от пользователя
@bot.event
async def on_message(message):
    # Проверяем, является ли сообщение командой бота
    if message.content.startswith("!"):
        # Если да, то обрабатываем команду бота
        await bot.process_commands(message)
    else:
        # Если нет, то проверяем, есть ли у пользователя анкета по разбану
        if message.author.id in applications:
            # Если есть, то получаем его анкету из словаря анкет
            application = applications[message.author.id]
            # Получаем ответ от пользователя на вопрос из анкеты
            await application.get_answer(message)

category = None # Объявляем глобальную переменную для категории

@bot.event
async def on_ready():
    global category # Используем глобальную переменную
    print(f"Logged in as {bot.user}") # Печатаем сообщение о готовности бота
    category = discord.utils.get(bot.guilds[0].categories, name="Разбан") # Получаем категорию по имени

# Запускаем бота с токеном
bot.run("MTExMzQ5ODI4NTU0MjQ3Nzg4NQ.G5BuU-.uiGjo-Gkiig0USSZvXSmGoRApXuVPc5UV1aWbA") # Замените на ваш токен бота
