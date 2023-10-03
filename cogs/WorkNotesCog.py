import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from datetime import datetime
from typing import List

class Info:
    def __init__(self):
        self.INFO_CHANNEL_ID = 1068213748835287070

config = Info()


##################################
# SUB COMMANDS
##################################

# Функция, которая будет выполняться по расписанию
@tasks.loop(hours=3)
async def scheduled_task(bot: commands.Bot):
    # Получите текущую дату и время
    current_date = datetime.now()

    with open("data/work_notes.json", "r", encoding='utf-8') as file:
        datafile = json.load(file)

    # пинг об окончании времени
    for user_id in datafile['users'].keys():
        if datafile["users"][user_id]["finished_work"] or datafile["users"][user_id][
            "last_informed"] == current_date.day:
            continue

        skip_group_work = False
        skip_user_work = False

        embed = discord.Embed(title="Напоминание", color=16752676)
        user = await bot.fetch_user(user_id)

        # проверка работы группы пользователя
        if datafile["users"][user_id]["user_group"]:
            group_name = datafile["users"][user_id]["user_group"]
            y, m, d = map(int, datafile['groups'][f'{group_name}']['group_deadline'])
            target_date = datetime(y, m, d)
            time_until_target = target_date - current_date
            if 0 < time_until_target.days <= 3:
                embed.add_field(
                    name=f"Уважаемые участники группы: `{group_name}`",
                    value=f"\nУ вашей группы <t:{int(target_date.timestamp())}:R> закончится время выполнение для работы!",
                    inline=False
                )
            else:
                skip_group_work = True
        else:
            skip_group_work = True

        # проверка работы пользователя
        y, m, d = map(int, datafile['users'][f'{user_id}']['user_deadline'])
        target_date = datetime(y, m, d)
        time_until_target = target_date - current_date
        if 0 < time_until_target.days <= 3:
            embed.add_field(
                name=f"Уважаемый пользователь: `{user.name}`",
                value=f"У тебя <t:{int(target_date.timestamp())}:R> закончится время выполнение для твоей личной работы!",
                inline=False
            )
        else:
            skip_user_work = True

        # если 2 проверки были пропущены переходим к следующему пользователю
        if skip_user_work and skip_group_work:
            continue

        embed.add_field(name='Забыли свои обязаности?', value='Напомнить свои задачи сможете прописав команду: `/info`',
                        inline=False)

        try:  # проверка открыт ли у пользователя лс
            await user.send(embed=embed)
        except Exception as e:
            print(e)
            channel = bot.get_channel(config.INFO_CHANNEL_ID)
            await channel.send(content=f"# <@{user_id}> пожалуйста откройте лс для оповещений", embed=embed)

        # записываем когда последний раз оповещали участника
        datafile["users"][user_id]["last_informed"] = current_date.day
        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

##################################
# MODALS
##################################


class AddUserWorkModal(discord.ui.Modal, title="Выдача работы"):
    deadline = discord.ui.TextInput(label="Укажите когда должна быть сделана работа:", style=discord.TextStyle.short,
                                    placeholder='2023-3-21', required=True, max_length=10, min_length=8)
    work_describtion = discord.ui.TextInput(label="Что он должен сделать:", style=discord.TextStyle.long, required=True,
                                            max_length=900)
    extra_notes = discord.ui.TextInput(label="Примичания:", style=discord.TextStyle.short, required=False,
                                       max_length=100)

    def __init__(self, bot: commands.Bot, user_id):
        super().__init__()
        self.bot = bot
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            y, m, d = self.deadline.value.split('-')
            y, m, d = int(y), int(m), int(d)
            select_date = datetime(y, m, d)
        except Exception as e:
            print(e)
            return await interaction.response.send_message(content=f"Ошибка: Вы не верно указали дату.", ephemeral=True)

        # записываем бд
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        # проверяем есть ли участник в группе
        if not f"{self.user_id}" in datafile['users'].keys():
            group = ""
        else:
            group = datafile['users'][f"{self.user_id}"]["user_group"]

        datafile['users'][f"{self.user_id}"] = {
            "user_group": group,
            "user_describtion": f"{self.work_describtion.value}",
            "user_extra_notes": f"{self.extra_notes.value}",
            "user_deadline": [y, m, d],
            "last_informed": 0,
            "finished_work": False
        }

        # изменяем бд
        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        if self.extra_notes.value:
            extra_notes_text = f"{self.extra_notes.value}"
        else:
            extra_notes_text = f"`пусто`"

        embed = discord.Embed(title='Информация о работе пользователя', color=57650,
                              description=f'**Описание:** \n{self.work_describtion.value} \n'
                                          f'**Примичания:** {extra_notes_text} \n'
                                          f'**Deadline:** <t:{int(select_date.timestamp())}:d> | <t:{int(select_date.timestamp())}:R>'
                              )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        user = await self.bot.fetch_user(self.user_id)
        embed = discord.Embed(
            title="Обновление твоей работы:", color=33735,
            description=f"**Описание:** \n{self.work_describtion.value} \n"
                        f"**Примичания:**{extra_notes_text} \n"
                        f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R> \n"
        )

        try:
            await user.send(embed=embed)
        except Exception as e:
            print(e)
            channel = self.bot.get_channel(config.INFO_CHANNEL_ID)
            await channel.send(content=f"# <@{self.user_id}> пожалуйста откройте лс для оповещений", embed=embed)


class AddGroupWorkModal(discord.ui.Modal, title="Выдача работы"):
    deadline = discord.ui.TextInput(label="Укажите когда должна быть сделана работа:", style=discord.TextStyle.short,
                                    placeholder="2023-9-21", required=True, max_length=10, min_length=8)
    work_describtion = discord.ui.TextInput(label="Что должны сделать:", style=discord.TextStyle.long, required=True,
                                            max_length=900)
    extra_notes = discord.ui.TextInput(label="Примичания:", style=discord.TextStyle.short, required=False,
                                       max_length=100)

    def __init__(self, bot: commands.Bot, group):
        super().__init__()
        self.bot = bot
        self.group = group

    async def on_submit(self, interaction: discord.Interaction):
        # Проверка правилльно ли указано время
        try:
            y, m, d = self.deadline.value.split('-')
            y, m, d = int(y), int(m), int(d)
            select_date = datetime(y, m, d)
        except Exception as e:
            print(e)
            return await interaction.response.send_message(content=f"Ошибка: Вы не верно указали время.",
                                                           ephemeral=True)

        # записываем бд
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        if not datafile['groups'][f'{self.group}']['group_users']:
            group_users = []
        else:
            group_users = datafile['groups'][f'{self.group}']['group_users']

        datafile['groups'][f"{self.group}"] = {
            "group_describtion": f"{self.work_describtion.value}",
            "group_extra_notes": f"{self.extra_notes.value}",
            "group_deadline": [y, m, d],
            "group_users": group_users
        }

        # изменяем бд
        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        if self.extra_notes.value:
            extra_notes_text = f"{self.extra_notes.value}"
        else:
            extra_notes_text = f"`пусто`"

        if group_users:
            users_text = f"{', '.join([f'<@{user_id}>' for user_id in group_users])}"
        else:
            users_text = f"`пусто`"

        embed = discord.Embed(title='', color=12345)
        embed.add_field(name=f"Инфа про `{self.group}`", inline=False,
                        value=f"**Описание:** \n{self.work_describtion.value} \n"
                              f"**Примичания:**{extra_notes_text} \n"
                              f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R> \n"
                              f"**Участники:** {users_text}"
                        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        for user_id in group_users:
            user = await self.bot.fetch_user(user_id)
            embed = discord.Embed(
                title="Обновление работы группы:", color=65330,
                description=f"**Описание:** \n{self.work_describtion.value} \n"
                            f"**Примичания:**{extra_notes_text} \n"
                            f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R> \n"
            )

            try:
                await user.send(embed=embed)
            except Exception as e:
                print(e)
                channel = self.bot.get_channel(config.INFO_CHANNEL_ID)
                await channel.send(content=f"# <@{user_id}> пожалуйста откройте лс для оповещений", embed=embed)


##################################
# VIEWS
##################################

class ShureDelGroupView(discord.ui.View):
    def __init__(self, *, bot: commands.Bot = None, group_name: str = None, member_id: int = None):
        super().__init__()
        self.bot = bot
        self.group_name = group_name
        self.member_id = member_id

    @discord.ui.button(label='Да', style=discord.ButtonStyle.red)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        for g_member_id in datafile['groups'][self.group_name]['group_users']:
            datafile["users"][f"{g_member_id}"]['user_group'] = ''

        datafile['groups'].pop(self.group_name)

        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)
        await interaction.response.edit_message(content=f'Вы успешно удалили {self.group_name}', view=None, embed=None)

    @discord.ui.button(label='Нет', style=discord.ButtonStyle.green)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Вы отменили удаление', view=None, embed=None)


class ShureDelUserView(discord.ui.View):
    def __init__(self, *, bot: commands.Bot = None, group_name: str = None, member_id: int = None):
        super().__init__()
        self.bot = bot
        self.group_name = group_name
        self.member_id = member_id

    @discord.ui.button(label='Да', style=discord.ButtonStyle.red)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        datafile['groups'][self.group_name]['group_users'].remove(self.member_id)
        datafile["users"][f"{self.member_id}"]['user_group'] = ''

        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        await interaction.response.edit_message(
            content=f'Вы успешно удалили <@{self.member_id}> из группы: `{self.group_name}`', view=None, embed=None)

    @discord.ui.button(label='Нет', style=discord.ButtonStyle.green)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Вы отменили удаление ', view=None, embed=None)


class InfoView(discord.ui.View):
    def __init__(self, *, bot: commands.Bot = None, group_name: str = None, member_id: int = None):
        super().__init__()
        self.bot = bot
        self.group_name = group_name
        self.member_id = member_id

    @discord.ui.button(label='Да', style=discord.ButtonStyle.red, custom_id='button_info')
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content=f'Да', view=None, embed=None)


# загрузка авто выбора групп
async def select_group_autocomplete(interaction: discord.Interaction, current: str, ) -> List[app_commands.Choice[str]]:
    with open("data/work_notes.json", "r", encoding='utf-8') as file:
        datafile = json.load(file)

    return [
        app_commands.Choice(name=group, value=group)
        for group in datafile['groups'].keys() if current.lower() in group.lower()
    ]


class WorkNotesCog(commands.Cog):
    def __init__(self, bot, *, guilds=None):
        self.bot = bot
        self.guilds = guilds

    ##################################
    # EVENTS
    ##################################

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"WorkNotesCog")

        # Проверяем, существует ли файл
        if not os.path.exists("data/work_notes.json"):
            # Если файла нет, создаем его с начальной структурой
            with open("data/work_notes.json", "w", encoding='utf-8') as file:
                json.dump({"users": {}, "groups": {}}, file)

        # Теперь мы знаем, что файл существует, открываем его для чтения
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        # Проверяем, есть ли в файле нужная нам информация
        if 'users' not in datafile:
            datafile['users'] = {}
        if 'groups' not in datafile:
            datafile['groups'] = {}

        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        await self.bot.tree.sync()
        scheduled_task.start(self.bot)

    ##################################
    # COMMANDS
    ##################################

    # добавление пользователю работы
    @app_commands.command(name='add_user_work', description="Дбовляет указаному пользователю работу")
    async def add_user_work(self, interaction: discord.Interaction, member: discord.Member):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        modal = AddUserWorkModal(self.bot, member.id)
        await interaction.response.send_modal(modal)

    # добавление группе работы
    @app_commands.command(name='add_group_work', description="Дбовляет указаной группе работу")
    @app_commands.autocomplete(group=select_group_autocomplete)
    async def add_group_work(self, interaction: discord.Interaction, group: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        modal = AddGroupWorkModal(self.bot, group)
        await interaction.response.send_modal(modal)

    # создание группы
    @app_commands.command(name='add_group', description="Добавляет группу вместе с пользователями(не обязательно)")
    @app_commands.describe(group_name='Название группы')
    async def add_group(self, interaction: discord.Interaction, group_name: str, member1: discord.Member = None,
                        member2: discord.Member = None, member3: discord.Member = None, member4: discord.Member = None,
                        member5: discord.Member = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return

        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        # проверяем есть не указали ли существующею группу
        for group in datafile['groups'].keys():
            if group_name.lower() == group.lower():
                return await interaction.response.send_message(f"Ошибка: `{group_name}` уже существует!",
                                                               ephemeral=True)

        member_id_list = set()
        for member in [member1, member2, member3, member4, member5]:
            if member:
                member_id_list.add(member.id)
                if not str(member.id) in datafile['users']:
                    datafile['users'][f"{member.id}"] = {
                        "user_group": group_name,
                        "user_describtion": "",
                        "user_extra_notes": "",
                        "user_deadline": [2020, 1, 1],
                        "last_informed": 0,
                        "finished_work": False
                    }
                elif datafile['users'][f"{member.id}"]['user_group']:
                    old_u_group = datafile['users'][f"{member.id}"]['user_group']
                    datafile['groups'][old_u_group]['group_users'].remove(member.id)
                    datafile['users'][f"{member.id}"]['user_group'] = group_name
                else:
                    datafile['users'][f"{member.id}"]['user_group'] = group_name

        datafile['groups'][group_name] = {
            "group_describtion": "",
            "group_extra_notes": "",
            "group_deadline": [2020, 1, 1],
            "group_users": list(member_id_list)
        }

        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        modal = AddGroupWorkModal(self.bot, group_name)

        await interaction.response.send_modal(modal)

    # добавление в группу участников
    @app_commands.command(name='add_group_users', description="Дбовляет указаной группе участников")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def add_group_users(self, interaction: discord.Interaction, group_name: str, member1: discord.Member,
                              member2: discord.Member = None, member3: discord.Member = None,
                              member4: discord.Member = None, member5: discord.Member = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        member_id_list = set(datafile['groups'][group_name]["group_users"])
        member_mention = set()
        for member in [member1, member2, member3, member4, member5]:
            if member:
                member_id_list.add(member.id)
                member_mention.add(member.mention)
                if not str(member.id) in datafile['users']:
                    datafile['users'][f"{member.id}"] = {
                        "user_group": group_name,
                        "user_describtion": "",
                        "user_extra_notes": "",
                        "user_deadline": [2020, 1, 1],
                        "last_informed": 0,
                        "finished_work": False
                    }
                elif datafile['users'][f"{member.id}"]['user_group']:
                    old_u_group = datafile['users'][f"{member.id}"]['user_group']
                    datafile['groups'][old_u_group]['group_users'].remove(member.id)
                    datafile['users'][f"{member.id}"]['user_group'] = group_name
                else:
                    datafile['users'][f"{member.id}"]['user_group'] = group_name

        datafile['groups'][group_name]["group_users"] = list(member_id_list)

        with open("data/work_notes.json", "w", encoding='utf-8') as file:
            json.dump(datafile, file, ensure_ascii=False, indent=4)

        await interaction.response.send_message(
            f"Для группы: `{group_name}`; \nДобавлены новые участники: {', '.join(member_mention)}", ephemeral=True)

    # добавление в группу участников
    @app_commands.command(name='del_group', description="Удаляет группу")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def del_group(self, interaction: discord.Interaction, group_name: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        try:
            view = ShureDelGroupView(group_name=group_name)
            await interaction.response.send_message(f"Вы уверены что хотите удалить `{group_name}`?", view=view,
                                                    ephemeral=True)
        except Exception as e:
            print(e)

    @app_commands.command(name='del_group_user', description="Удаляет указаной группе участника")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def del_group_user(self, interaction: discord.Interaction, group_name: str, member1: discord.Member):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        # записываем бд
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        if not member1.id in datafile['groups'][f"{group_name}"]["group_users"]:
            return await interaction.response.send_message(f"Ошибка: Пользователя <@{member1.id}> нет в `{group_name}`",
                                                           ephemeral=True)

        view = ShureDelUserView(group_name=group_name, member_id=member1.id)
        await interaction.response.send_message(f"Вы уверены что хотите удалить <@{member1.id}> из `{group_name}`?",
                                                view=view, ephemeral=True)

    @app_commands.command(name='info', description="Показывает инфу работ пользователей и групп")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def info(self, interaction: discord.Interaction, group_name: str = None, member: discord.Member = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "3")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        with open("data/work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        used_optional = False
        if group_name:
            check_1 = str(interaction.user.id) in self.bot.ctx.admins
            check_2 = self.bot.check_roles(interaction.user, "1")
            if not (check_1 or check_2):
                await interaction.response.send_message(f'У вас нет прав на просмотр информации о задачах групп',
                                                        ephemeral=True)
                return
            embed = discord.Embed(title='', color=65330)
            g_describtion = datafile['groups'][group_name]['group_describtion']
            g_extra_notes = datafile['groups'][group_name]['group_extra_notes']
            y, m, d = datafile['groups'][group_name]['group_deadline']
            g_users = datafile['groups'][group_name]['group_users']

            if g_extra_notes:
                extra_notes_text = f"{g_extra_notes}"
            else:
                extra_notes_text = f"`пусто`"

            if g_users:
                users_text = f"{', '.join([f'<@{user_id}>' for user_id in g_users])}"
            else:
                users_text = f"`пусто`"

            embed.add_field(name=f"Инфа про `{group_name}`", inline=False,
                            value=f"**Описание:** \n{g_describtion} \n"
                                  f"**Примичания:** {extra_notes_text} \n"
                                  f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R> \n"
                                  f"**Участники:** {users_text}"
                            )
            try:
                await interaction.user.send(embed=embed)
            except:
                return await interaction.response.send_message(content='Откройте лс для получения информации',
                                                               ephemeral=True)

            used_optional = True

        if member:
            check_1 = str(interaction.user.id) in self.bot.ctx.admins
            check_2 = self.bot.check_roles(interaction.user, "1")
            if not (check_1 or check_2):
                await interaction.response.send_message(f'У вас нет прав на просмотр информации о задачах пользователей',
                                                        ephemeral=True)
                return
            if not str(member.id) in datafile["users"].keys():
                return await interaction.response.send_message(f"Пользователя <@{member.id}> нет в бд.", ephemeral=True)

            embed = discord.Embed(title='', color=33735)
            embed.set_author(name=member.name, icon_url=member.avatar)

            u_group = datafile['users'][f"{member.id}"]['user_group']
            u_describtion = datafile['users'][f"{member.id}"]['user_describtion']
            u_extra_notes = datafile['users'][f"{member.id}"]['user_extra_notes']
            y, m, d = datafile['users'][f"{member.id}"]['user_deadline']
            last_informed = datafile['users'][f"{member.id}"]['last_informed']
            finished_work = datafile['users'][f"{member.id}"]['finished_work']

            if u_group:
                u_group_text = f"{u_group}"
            else:
                u_group_text = f"`пусто`"

            if u_describtion:
                u_describtion_text = f"\n{u_describtion}"
            else:
                u_describtion_text = f"`пусто`"

            if u_extra_notes:
                extra_notes_text = f"{u_extra_notes}"
            else:
                extra_notes_text = f"`пусто`"

            embed.add_field(name=f"Инфа про `{member.name}`", inline=False,
                            value=f"**Группа:** `{u_group_text}` \n"
                                  f"**Описание:** {u_describtion_text} \n"
                                  f"**Примичания:** {extra_notes_text} \n"
                                  f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R> \n"
                                  f"**last_informed:** `{last_informed}` \n"
                            #   f"**Завершил работу:** `{finished_work}`"
                            )

            try:
                await interaction.user.send(embed=embed)
            except Exception as e:
                print(e)
                return await interaction.response.send_message(content=f'Откройте лс для получения информации',
                                                               ephemeral=True)

            used_optional = True

        if not used_optional:
            user_id = str(interaction.user.id)
            if not str(user_id) in datafile['users'].keys():
                return await interaction.response.send_message('Ошибка: О вас нет никакой информации', ephemeral=True)

            if datafile['users'][user_id]['user_group']:
                embed = discord.Embed(title="", color=65330)

                user_group = datafile['users'][user_id]['user_group']
                g_describtion = datafile['groups'][user_group]['group_describtion']
                g_extra_notes = datafile['groups'][user_group]['group_extra_notes']
                y, m, d = datafile['groups'][user_group]['group_deadline']

                if g_extra_notes:
                    extra_notes_text = f"{g_extra_notes}"
                else:
                    extra_notes_text = f"`пусто`"

                embed.add_field(name=f'Инфа о группе: `{user_group}`:', inline=False,
                                value=f"**Описание:** \n{g_describtion} \n"
                                      f"**Примичания:** {extra_notes_text} \n"
                                      f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R>"
                                )
                try:
                    await interaction.user.send(embed=embed)
                except:
                    return await interaction.response.send_message(content='Откройте лс для получения информации',
                                                                   ephemeral=True)

            if datafile['users'][user_id]['user_describtion']:
                embed = discord.Embed(title="", color=48895)
                embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)

                u_describtion = datafile['users'][user_id]['user_describtion']
                u_extra_notes = datafile['users'][user_id]['user_extra_notes']
                y, m, d = datafile['users'][user_id]['user_deadline']

                if u_extra_notes:
                    extra_notes_text = f"{u_extra_notes}"
                else:
                    extra_notes_text = f"`пусто`"

                embed.add_field(name=f'Инфа о пользователе: `{interaction.user.name}`:', inline=False,
                                value=f"**Описание:** \n{u_describtion} \n"
                                      f"**Примичания:** {extra_notes_text} \n"
                                      f"**Deadline:** <t:{int(datetime(y, m, d).timestamp())}:R>"
                                )
                try:
                    await interaction.user.send(embed=embed)
                except:
                    return await interaction.response.send_message(content='Откройте лс для получения информации',
                                                                   ephemeral=True)

        await interaction.response.send_message(content='Проверьте лс', ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(WorkNotesCog(bot), guilds=bot.guilds)