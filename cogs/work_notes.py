import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
from datetime import datetime
from typing import List

class Colour:
    def __init__(self):
        self.INFO_CHANNEL_ID = 1168272341529268315
        self.WORK_LOG_ID = 1168272558278332426
        self.CUSTOMISATE_LOG_ID = 1168272899656912937

        self.INFO_COLOR = 16437820
        self.USER_INFO_COLOR = 3340880
        self.GROUP_INFO_COLOR = 3970800

        self.FINISH_WORK_COLOR = 12464880

        self.USER_FAILED_WORK_COLOR = 16757761
        self.GROUP_FAILED_WORK_COLOR = 16757850

        self.DELITE_COLOR = 16396850

clr = Colour()



# intents = discord.Intents.all()

# bot = commands.Bot(command_prefix='!', intents=intents)

# class Info:
#     def __init__(self):
#         self.INFO_CHANNEL_ID = 1068213748835287070
#         self.LOG_CHANNEL_ID = 1068213748835287070

# clr = Info()


##################################
# SUB FUNCTIONS
##################################

# Функция, которая будет выполняться по расписанию
@tasks.loop(hours=3)
async def scheduled_task(bot: commands.Bot):
    # Получите текущую дату и время
    current_date = datetime.now()

    WORK_CONTROL = WorkControl(bot)
    # пинг об окончании времени
    for user_id in WORK_CONTROL.datafile['users'].keys():
        skip_group_work = True
        skip_user_work = True

        embed = discord.Embed(title="Напоминание", color=clr.INFO_COLOR)
        user = await bot.fetch_user(user_id)

        user_works_text = ''
        group_works_text = ''
        group_log = {}
        group_end_work = {}
        informed = WORK_CONTROL.datafile["users"][user_id]["last_informed"] == current_date.day
        # перебираем все работы
        for work_name in WORK_CONTROL.datafile['users'][user_id]['works'].keys():
            WORK_CONTROL = WorkControl(bot)
            u_description, u_extra_notes, u_deadline, u_finished_work, manager_id = await WORK_CONTROL.load_work(
                work_name, user_id=user_id
            )    
            
            y, m, d = u_deadline
            target_date = datetime(y, m, d)
            time_until_target = (target_date - current_date).days + 1
                  
            # проверка закончена ли работа
            if u_finished_work:
                if 0 > time_until_target < -3:
                    WORK_CONTROL.datafile['users'][user_id]['works'].pop(work_name)
                    await WORK_CONTROL.save_data()
                continue

            if 0 < time_until_target <= 3 or 0 < time_until_target and time_until_target % 10 == 0:
                user_works_text += f"- На твоей работе `{work_name}` <t:{int(target_date.timestamp())}:R> дедлайн. \n"
                skip_user_work = False
            elif time_until_target == 0 and not informed:
                manager_id = WORK_CONTROL.datafile['users'][user_id]['works'][work_name]['manager_id']
                m_user = await bot.fetch_user(manager_id)
                embed = discord.Embed(
                    title='', color=clr.USER_FAILED_WORK_COLOR,
                    description=f"К сожалению <@{user_id}> не смог завершить работу `{work_name}`."
                )
                await end_work_log(bot, work_name=work_name, user_id=f"{user_id}")
                await m_user.send(embed=embed)
            elif 0 > time_until_target < -1:
                if not u_finished_work:
                    await end_work_log(bot, work_name=work_name, user_id=user_id)
                WORK_CONTROL.datafile['users'][user_id]['works'].pop(work_name)
                await WORK_CONTROL.save_data()

        if not skip_user_work:
            embed.add_field(
                name=f"Уважаемый пользователь: `{user.name}`",
                value=user_works_text,
                inline=False
            )

        # проверка работ группы пользователя
        if WORK_CONTROL.datafile["users"][user_id]["group"]:
            group_name = WORK_CONTROL.datafile["users"][user_id]["group"]

            # перебираем все работы
            for work_name in WORK_CONTROL.datafile['groups'][group_name]['works'].keys():
                WORK_CONTROL = WorkControl(bot)
                g_description, g_extra_notes, g_deadline, g_finished_work, manager_id = await WORK_CONTROL.load_work(
                    work_name, group_name=group_name
                )
                
                y, m, d = g_deadline
                target_date = datetime(y, m, d)
                time_until_target = (target_date - current_date).days + 1
                
                # проверка закончена ли работа
                if g_finished_work:
                    if 0 > time_until_target < -3:
                        WORK_CONTROL.datafile['groups'][group_name]['works'].pop(work_name)
                        await WORK_CONTROL.save_data()
                    continue
                if 0 < time_until_target <= 3 or 0 < time_until_target and time_until_target % 10 == 0:
                    group_works_text += f"- У твоей группе работа `{work_name}` <t:{int(target_date.timestamp())}:R> дедлайн. \n"
                    skip_group_work = False
                elif time_until_target == 0 and not informed:
                    if not group_name in group_end_work:
                        group_end_work[group_name] = set()
                    group_end_work[group_name].add(work_name)

                    if not group_name in group_log:
                        group_log[group_name] = set()
                    group_log[group_name].add(work_name)
                elif 0 > time_until_target < -1:
                    # if not u_finished_work:
                    #     await end_work_log(work_name=work_name, group_name=group_name)
                    WORK_CONTROL.datafile['groups'][group_name]['works'].pop(work_name)
                    await WORK_CONTROL.save_data()
        if not skip_group_work:
            embed.add_field(
                name=f"Уважаемые участники группы: `{group_name}`",
                value=group_works_text,
                inline=False
            )

        # проверка проверялся ли он сегодня
        if informed:
            continue
        else:
            # записываем когда последний раз проверяли участника
            WORK_CONTROL.datafile["users"][user_id]["last_informed"] = current_date.day
            await WORK_CONTROL.save_data()
        # если 2 проверки были пропущены переходим к следующему пользователю
        if skip_user_work and skip_group_work:
            continue

        embed.add_field(name='Забыли свои обязаности?', 
                        value='Напомнить свои задачи сможете прописав команду: `/info`',
                        inline=False)

        try:  # проверка открыт ли у пользователя лс
            await user.send(embed=embed)
        except Exception as e:
            channel = bot.get_channel(clr.INFO_CHANNEL_ID)
            await channel.send(content=f"# <@{user_id}> пожалуйста откройте лс для оповещений", embed=embed)
    if group_end_work:
        for group_name in group_end_work.keys():
            for work_name in group_end_work[group_name]:
                await send_manager_info(bot, work_name=work_name, group_name=group_name)
    if group_log:
        for group_name in group_log.keys():
            for work_name in group_log[group_name]:
                await end_work_log(bot, work_name=work_name, group_name=group_name)
    print("Checked notes")

async def send_manager_info(bot:commands.Bot, work_name, user_id=None, group_name=None):
    WORK_CONTROL = WorkControl(bot)
    description, extra_notes, deadline, finished_work, manager_id = await WORK_CONTROL.load_work(
        work_name=work_name,
        user_id=user_id,
        group_name=group_name,
    )

    m_user = await bot.fetch_user(manager_id)
    embed = discord.Embed(title='', color=clr.GROUP_FAILED_WORK_COLOR, description='')
    if user_id:
        embed.description += f"Пользователь <@{user_id}> не уложился в дедлайн и __не__ выполнил работу `{work_name}` \n"
    elif group_name:
        embed.description += f"Группа `{group_name}` не уложилась в дедлайн и __не__ выполнила работу `{work_name}` \n"
        g_users = WORK_CONTROL.datafile['groups'][group_name]['users']
        if g_users: 
            embed.description += f"Пользователи группы: {', '.join([f'<@{user_id}>' for user_id in g_users])} \n"
        else:
            embed.description += f"Пользователи группы: `нет` \n"

    await m_user.send(embed=embed)

async def add_work_log(bot:commands.Bot, work_name, user_id=None, group_name=None):
    WORK_CONTROL = WorkControl(bot)
    description, extra_notes, deadline, finished_work, manager_id = await WORK_CONTROL.load_work(
        work_name=work_name,
        user_id=user_id,
        group_name=group_name,
    )
    embed = discord.Embed(title="", description='')
    embed.color = clr.INFO_COLOR
    
    if user_id: 
        embed.title = "Выдана работа пользователю"
        user = await bot.fetch_user(user_id)
        embed.set_author(name=user.name, icon_url=user.avatar)
    else: embed.title = "Выдана работа группе"
    
    if user_id: embed.description += f'Пользователь: <@{user_id}> \n'
    elif group_name: 
        embed.description += f'Группа: `{group_name}` \n'
        g_users = WORK_CONTROL.datafile['groups'][group_name]['users']
        if g_users: 
            embed.description += f"Пользователи: {', '.join([f'<@{user_id}>' for user_id in g_users])} \n"
        else: 
            embed.description += "Пользователи: `пусто` \n"
    
    embed.description += f"Название работы: `{work_name}` \n"
    embed.description += f"Описание: \n{description} \n"
    
    if extra_notes: embed.description += f"Примичания: {extra_notes} \n"
    else: embed.description += f"Примичания: `нет` \n"

    embed.description += f"Deadline: <t:{int(datetime(*deadline).timestamp())}:R> | <t:{int(datetime(*deadline).timestamp())}:D> \n"
    embed.description += f"Менеджер: <@{manager_id}> \n"
    
    log_channel = await bot.fetch_channel(clr.WORK_LOG_ID)
    await log_channel.send(embed=embed)

async def end_work_log(bot:commands.Bot, work_name, user_id=None, group_name=None):
    WORK_CONTROL = WorkControl(bot)
    description, extra_notes, deadline, finished_work, manager_id = await WORK_CONTROL.load_work(
        work_name=work_name,
        user_id=user_id,
        group_name=group_name,
    )
    embed = discord.Embed(title="", description='')
    
    if finished_work: 
        embed.title = "Работа была завершена"
        embed.color = clr.GROUP_INFO_COLOR # потом надо поменять цвет!
        if user_id:
            user = await bot.fetch_user(user_id)
            embed.set_author(name=user.name, icon_url=user.avatar)
    else: 
        embed.title = "Работа была __НЕ__ завершена"
        embed.color = clr.DELITE_COLOR # потом надо поменять цвет!
    
    if user_id: embed.description += f'Пользователь: <@{user_id}> \n'
    elif group_name: 
        embed.description += f'Группа: `{group_name}` \n'
        g_users = WORK_CONTROL.datafile['groups'][group_name]['users']
        if g_users: 
            embed.description += f"Пользователи: {', '.join([f'<@{user_id}>' for user_id in g_users])} \n"
        else: 
            embed.description += "Пользователи: `пусто` \n"
    
    embed.description += f"Название работы: `{work_name}` \n"
    embed.description += f"Описание: \n{description} \n"
    
    if extra_notes: embed.description += f"Примичания: {extra_notes} \n"
    else: embed.description += f"Примичания: `нет` \n"

    embed.description += f"Deadline: <t:{int(datetime(*deadline).timestamp())}:R> | <t:{int(datetime(*deadline).timestamp())}:D> \n"
    embed.description += f"Менеджер: <@{manager_id}> \n"
    
    log_channel = await bot.fetch_channel(clr.WORK_LOG_ID)
    await log_channel.send(embed=embed)

async def customisate_log(bot:commands.Bot, admin_id, group_name=None, users:List[int]=None, *, delitting=False, adding=False):
    WORK_CONTROL = WorkControl(bot)
    embed = discord.Embed(title="", description='')

    embed.description += f"Кто это сделал: <@{admin_id}> \n"

    if delitting:
        embed.color = clr.DELITE_COLOR
        if group_name and users:
            embed.title = f'Удалили пользователеля из `{group_name}`'
            embed.description += f"Удалённый пользователь: {', '.join([f'<@{user_id}>' for user_id in users])} \n"
        elif group_name:
            embed.title = f'Удалена группа `{group_name}`'
    elif adding:
        embed.color = clr.USER_INFO_COLOR # потом надо поменять цвет!
        if group_name and users:
            embed.title = f'Добавлены пользователи для `{group_name}`'
            embed.description += f"Добавленые дользователи: {', '.join([f'<@{user_id}>' for user_id in users])} \n"
        elif group_name:
            embed.title = f'Добавлена группа `{group_name}`'

    log_channel = await bot.fetch_channel(clr.CUSTOMISATE_LOG_ID)
    await log_channel.send(embed=embed)


##################################
# MAIN CLASS
##################################

class WorkControl:
    def __init__(self, bot:commands.Bot=None):
        self.bot = bot
        
        with open("data\work_notes.json", "r", encoding='utf-8') as file:
            self.datafile = json.load(file)
        
    async def add_user(self, user_id:str, *, user_group:str = None):
        if user_group:
            user_group_text = user_group
        else:
            user_group_text = ""

        self.datafile['users'][user_id] = {
            "group": user_group_text,
            "last_informed": 0,
            "works": {},
        }

    async def add_group(self, group_name:str, *, group_users:List[int] = None):
        if group_users:
            group_users_text = group_users
        else:
            group_users_text = []

        self.datafile['groups'][group_name] = {
            "users": group_users_text,
            "works": {},
        }

    async def set_user_work(self, user_id:str, work_name:str, date_list:List[int], work_description:str, extra_notes:str, who_added_id:int) -> discord.Embed:
        select_date = datetime(*date_list)
        
        if not user_id in self.datafile['users'].keys():
            await self.add_user(user_id)

        self.datafile['users'][f"{user_id}"]['works'][work_name] = {
            "description": work_description,
            "extra_notes": extra_notes,
            "deadline": date_list,
            "finished_work": False,
            'manager_id': who_added_id,
        }

        await self.save_data()        

        await add_work_log(self.bot, work_name=work_name, user_id=user_id)

        embed = await self.load_embed(work_name=work_name, user_id=user_id)
        return embed

    async def set_group_work(self, group:str, work_name:str, date_list:List[int], work_description:str, extra_notes:str, who_added_id:int) -> discord.Embed:
        select_date = datetime(*date_list)

        self.datafile['groups'][group]['works'][work_name] = {
            "description": work_description,
            "extra_notes": extra_notes,
            "deadline": date_list,
            "finished_work": False,
            'manager_id': who_added_id,
        }
        # записываем в бд
        await self.save_data()
        
        await add_work_log(self.bot, work_name=work_name, group_name=group)

        embed = await self.load_embed(work_name, group_name=group)
        return embed

    async def load_embed(self, work_name:str, user_id:str=None, group_name:str=None):
        if user_id: # user
            work_list = list(self.datafile['users'][user_id]['works'].keys()) 
            if work_list: 
                work_name = work_name
            else:
                u_group = self.datafile['users'][user_id]['group']
                
                if u_group: group_text = f"{u_group}"
                else: group_text = "`пусто`"

                embed = discord.Embed(color=clr.USER_INFO_COLOR,
                    title='Информация о пользователе', 
                    description=f'Группа: `{group_text}` \n'
                                f'На данный момент у <@{user_id}> нет никакой личной работы.'
                )
                member = await self.bot.fetch_user(user_id)
                embed.set_author(name=member.name, icon_url=member.avatar)
                return embed
        else: # group          
            work_list = list(self.datafile['groups'][group_name]['works'].keys()) 
            if work_list: 
                work_name = work_name
            else:
                g_users = self.datafile['groups'][group_name]['users']
                if g_users: users_text = f"{', '.join([f'<@{user_id}>' for user_id in g_users])}"
                else: users_text = "`пусто`"
                
                return discord.Embed(color=clr.GROUP_INFO_COLOR,
                    title='Информация о группе', 
                    description=f'Участники: {users_text}'
                                f'На данный момент нет у {group_name}> никакой работы.'
                )
        
        description, extra_notes, deadline, finished_work, manager_id = await self.load_work(
            work_name=work_name,
            user_id=user_id,
            group_name=group_name,
        )

        # user, group
        if description: description_text = f"\n{description}"
        else: description_text = "`пусто`"

        # user, group
        if extra_notes: extra_notes_text = f"{extra_notes}"
        else: extra_notes_text = "`пусто`"

        if user_id:
            u_group = self.datafile['users'][user_id]['group']
            
            if u_group: group_text = f"{u_group}"
            else: group_text = "`пусто`"

            embed = discord.Embed(color=clr.USER_INFO_COLOR,
                title='Информация о работе пользователя', 
                description=f"**Группа:** `{group_text}` \n"
                            f"**Название работы:** `{work_name}` \n"
                            f"**Описание:** {description_text} \n"
                            f"**Примичания:** {extra_notes_text} \n"
                            f"**Deadline:** <t:{int(datetime(*deadline).timestamp())}:R> \n"
                            f'**Менеджер:** <@{manager_id}> \n'
                            f"**Завершил работу:** `{finished_work}` \n"
            )
            member = await self.bot.fetch_user(user_id)
            embed.set_author(name=member.name, icon_url=member.avatar)
        elif group_name:
            g_users = self.datafile['groups'][group_name]['users']
            
            if g_users: users_text = f"{', '.join([f'<@{user_id}>' for user_id in g_users])}"
            else: users_text = "`пусто`"

            embed = discord.Embed(color=clr.GROUP_INFO_COLOR,
                title=f"Инфа про `{group_name}`", 
                description=f"**Название работы:** `{work_name}` \n"
                            f"**Описание:** \n{description} \n"
                            f"**Примичания:** {extra_notes_text} \n"
                            f"**Deadline:** <t:{int(datetime(*deadline).timestamp())}:R> \n"
                            f"**Участники:** {users_text} \n" 
                            f"**Менеджер:** <@{manager_id}> \n" 
                            f"**Завершил работу:** `{finished_work}`",
            )
        return embed

    async def load_work(self, work_name:str, *, user_id:str = None, group_name:str = None):
        if user_id:
            if not self.datafile['users'][user_id]['works']:
                return None, None, [2020, 1, 1], False
            description = self.datafile['users'][user_id]["works"][work_name]['description']
            extra_notes = self.datafile['users'][user_id]["works"][work_name]['extra_notes']
            deadline = self.datafile['users'][user_id]["works"][work_name]['deadline']
            finished_work = self.datafile['users'][user_id]["works"][work_name]['finished_work']
            manager_id = self.datafile['users'][user_id]["works"][work_name]['manager_id']
        elif group_name:
            if not self.datafile['groups'][group_name]['works']:
                return None, None, [2020, 1, 1], False
            description = self.datafile['groups'][group_name]["works"][work_name]['description']
            extra_notes = self.datafile['groups'][group_name]["works"][work_name]['extra_notes']
            deadline = self.datafile['groups'][group_name]["works"][work_name]['deadline']
            finished_work = self.datafile['groups'][group_name]["works"][work_name]['finished_work']
            manager_id = self.datafile['groups'][group_name]["works"][work_name]['manager_id']

        return description, extra_notes, deadline, finished_work, manager_id

    async def save_data(self):
        # изменяем бд
        with open("data\work_notes.json", "w", encoding='utf-8') as file:
            json.dump(self.datafile, file, ensure_ascii=False, indent=4)


##################################
# MODALS
##################################

class AddUserWorkModal(discord.ui.Modal, title="Выдача работы"):
    work_name = discord.ui.TextInput(label="Укажите название работе:", style=discord.TextStyle.short, 
                                    required=True, max_length=30)
    deadline = discord.ui.TextInput(label="Укажите когда должна быть сделана работа:", style=discord.TextStyle.short,
                                    placeholder='2023-3-21', required=True, max_length=10, min_length=8)
    work_description = discord.ui.TextInput(label="Что он должен сделать:", style=discord.TextStyle.long, required=True,
                                            max_length=900)
    extra_notes = discord.ui.TextInput(label="Примичания:", style=discord.TextStyle.short, required=False,
                                       max_length=100)

    def __init__(self, bot: commands.Bot, user_id:int):
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
        

        WORK_CONTROL = WorkControl(bot=self.bot)

        embed = await WORK_CONTROL.set_user_work(
            str(self.user_id),                 # id (str)
            str(self.work_name.value.lower()), # work_name (str)
            [y, m, d],                         # date (int)
            self.work_description.value,       # work_description (str)
            self.extra_notes.value,            # extra_notes (str)
            interaction.user.id,               # manager_id (int)
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        ####### Отправка уведомления про изминение работы #######
        
        user = await self.bot.fetch_user(self.user_id)

        embed.title = "Обновление твоей работы:"
        embed.color = clr.USER_INFO_COLOR

        try:
            await user.send(embed=embed)
        except Exception as e:
            print(e)
            channel = self.bot.get_channel(clr.INFO_CHANNEL_ID)
            await channel.send(content=f"# <@{self.user_id}> пожалуйста откройте лс для оповещений", embed=embed)


class AddGroupWorkModal(discord.ui.Modal, title="Выдача работы"):
    work_name = discord.ui.TextInput(label="Укажите название работе:", style=discord.TextStyle.short, 
                                    required=True, max_length=30)
    deadline = discord.ui.TextInput(label="Укажите когда должна быть сделана работа:", style=discord.TextStyle.short,
                                    placeholder="2023-9-21", required=True, max_length=10, min_length=8)
    work_description = discord.ui.TextInput(label="Что должны сделать:", style=discord.TextStyle.long, required=True,
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
        WORK_CONTROL = WorkControl(bot=self.bot)

        embed = await WORK_CONTROL.set_group_work(
            self.group,                        # group (str)
            str(self.work_name.value.lower()), # work_name (str)
            [y, m, d],                         # date (List[int])
            self.work_description.value,       # work_description (str)
            self.extra_notes.value,            # extra_notes (str)
            interaction.user.id,               # manager_id (int)
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


        ####### Отправка уведомления про изминение работы #######

        embed.title = "Обновление работы группы:"
        embed.color = clr.GROUP_INFO_COLOR
        group_users = WORK_CONTROL.datafile['groups'][self.group]['users']

        for user_id in group_users:
            user = await self.bot.fetch_user(user_id)

            try:
                await user.send(embed=embed)
            except Exception as e:
                print(e)
                channel = self.bot.get_channel(clr.INFO_CHANNEL_ID)
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
        WORK_CONTROL = WorkControl(self.bot)

        await customisate_log(self.bot, admin_id=interaction.user.id, group_name=self.group_name, delitting=True)

        for g_member_id in WORK_CONTROL.datafile['groups'][self.group_name]['users']:
            WORK_CONTROL.datafile["users"][f"{g_member_id}"]['group'] = ''

        WORK_CONTROL.datafile['groups'].pop(self.group_name)

        await WORK_CONTROL.save_data()
        embed = discord.Embed(
            title='', color=clr.DELITE_COLOR,
            description=f'Вы успешно удалили `{self.group_name}`'
        )
        await interaction.response.edit_message(view=None, embed=embed)

    @discord.ui.button(label='Нет', style=discord.ButtonStyle.green)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Вы отменили удаление.', view=None, embed=None)

class ShureDelGroupUserView(discord.ui.View):
    def __init__(self, *, bot: commands.Bot = None, group_name: str = None, member_id: int = None):
        super().__init__()
        self.bot = bot
        self.group_name = group_name
        self.member_id = member_id

    @discord.ui.button(label='Да', style=discord.ButtonStyle.red)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        WORK_CONTROL = WorkControl(self.bot)

        await customisate_log(self.bot, admin_id=interaction.user.id, group_name=self.group_name, users=[self.member_id], delitting=True)


        WORK_CONTROL.datafile['groups'][self.group_name]['users'].remove(self.member_id)
        WORK_CONTROL.datafile["users"][f"{self.member_id}"]['group'] = ''

        await WORK_CONTROL.save_data()

        embed = discord.Embed(
            title='', color=clr.DELITE_COLOR,
            description=f'Вы успешно удалили <@{self.member_id}> из группы: `{self.group_name}`'
        )
        await interaction.response.edit_message(view=None, embed=embed)

    @discord.ui.button(label='Нет', style=discord.ButtonStyle.green)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Вы отменили удаление.', view=None, embed=None)

class ScrollView(discord.ui.View):
    def __init__(self, work_list, max_page, group_name:str = None, user_id:str = None, user_name:str = None, bot:commands.Bot=None):
        super().__init__()
        self.work_list = work_list
        self.now_page = 1
        self.max_page = max_page
        self.group_name = group_name
        self.user_id = user_id
        self.user_name = user_name
        self.bot = bot

    async def show_items(self, interaction: discord.Interaction):
        WORK_CONTROL = WorkControl(self.bot)

        if self.group_name:
            embed = await WORK_CONTROL.load_embed(self.work_list[self.now_page-1], group_name=self.group_name)
            embed.set_footer(text=f"Страница: {self.now_page}/{self.max_page}")
        elif self.user_id:
            embed = await WORK_CONTROL.load_embed(self.work_list[self.now_page-1], user_id=self.user_id)
            embed.set_footer(text=f"Страница: {self.now_page}/{self.max_page}")
            
        self.clear_items()
        self.add_item(self.button1)
        self.add_item(self.button2)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='<<', style=discord.ButtonStyle.green)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        if self.now_page != 1:
            self.now_page -= 1
        await self.show_items(interaction)

    @discord.ui.button(label='>>', style=discord.ButtonStyle.green)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        if self.now_page != self.max_page:
            self.now_page += 1
        await self.show_items(interaction)


##################################
# AUTOCOMPLETE
##################################

# загрузка авто выбора групп
async def select_group_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    WORK_CONTROL = WorkControl()

    return [
        app_commands.Choice(name=group, value=group)
        for group in WORK_CONTROL.datafile['groups'].keys() if current.lower() in group.lower()
    ]

# загрузка авто выбора пользователей
async def select_user_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    WORK_CONTROL = WorkControl()

    user_ids = WORK_CONTROL.datafile['users']
    
    # Получить информацию о пользователях из сервера Discord
    user_choices = []
    for user_id in user_ids:
        user = interaction.guild.get_member(int(user_id))
        if user and current.lower() in user.display_name.lower():
            user_choices.append(app_commands.Choice(name=user.display_name, value=user_id))
    return user_choices

# загрузка авто выбора работы пользователя
async def select_u_work_name_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    WORK_CONTROL = WorkControl()

    u_work_name_list = WORK_CONTROL.datafile['users'][f"{interaction.user.id}"]['works'].keys()
    
    # Получить информацию о пользователях из сервера Discord
    choices = []
    for u_work_name in u_work_name_list:
        if u_work_name and current.lower() in u_work_name.lower():
            choices.append(app_commands.Choice(name=u_work_name, value=u_work_name))
    return choices

# загрузка авто выбора работы группы
async def select_g_work_name_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    WORK_CONTROL = WorkControl()

    group = WORK_CONTROL.datafile['users'][f"{interaction.user.id}"]['group']
    if not group:
        return
    else:
        g_work_name_list = WORK_CONTROL.datafile['groups'][group]['works'].keys()
    
    # Получить информацию о пользователях из сервера Discord
    choices = []
    for g_work_name in g_work_name_list:
        if g_work_name and current.lower() in g_work_name.lower():
            choices.append(app_commands.Choice(name=g_work_name, value=g_work_name))
    return choices



class work_notes(commands.Cog):
    def __init__(self, bot, *, guilds=None):
        self.bot = bot
        self.guilds = guilds

    ##################################
    # EVENTS
    ##################################

    # запускает постоянную проверку, добавление бд, обновление "/" команд
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"work_notes")

        # Проверяем, существует ли файл
        if not os.path.exists("data\work_notes.json"):
            # Если файла нет, создаем его с начальной структурой
            with open("data\work_notes.json", "w", encoding='utf-8') as file:
                json.dump({"users": {}, "groups": {}}, file)

        # Теперь мы знаем, что файл существует, открываем его для чтения
        with open("data\work_notes.json", "r", encoding='utf-8') as file:
            datafile = json.load(file)

        # Проверяем, есть ли в файле нужная нам информация
        if 'users' not in datafile:
            datafile['users'] = {}
        if 'groups' not in datafile:
            datafile['groups'] = {}

        with open("data\work_notes.json", "w", encoding='utf-8') as file:
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
    @app_commands.command(name='add_group_work', description="Добавляет указанной группе работу")
    @app_commands.autocomplete(group=select_group_autocomplete)  # Ensure this matches your parameter
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
                        member2: discord.Member = None, member3: discord.Member = None, 
                        member4: discord.Member = None, member5: discord.Member = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return

        WORK_CONTROL = WorkControl(self.bot)

        # проверяем: не указали ли существующею группу
        for group in WORK_CONTROL.datafile['groups'].keys():
            if group_name.lower() == group.lower():
                return await interaction.response.send_message(f"Ошибка: `{group_name}` уже существует!",
                                                                ephemeral=True)

        await customisate_log(self.bot, admin_id=interaction.user.id, group_name=group_name, adding=True)

        group_users = set()
        for member in [member1, member2, member3, member4, member5]:
            if member:
                group_users.add(member.id)
                # если нет пользователя в бд = добавить
                if not str(member.id) in WORK_CONTROL.datafile['users']:
                    await WORK_CONTROL.add_user(str(member.id), user_group=group_name)
                # если была у пользователя раньше группа = изменить её
                elif WORK_CONTROL.datafile['users'][f"{member.id}"]['group']:
                    old_u_group = WORK_CONTROL.datafile['users'][f"{member.id}"]['group']
                    WORK_CONTROL.datafile['groups'][old_u_group]['users'].remove(member.id)
                    WORK_CONTROL.datafile['users'][f"{member.id}"]['group'] = group_name
                else:
                    WORK_CONTROL.datafile['users'][f"{member.id}"]['group'] = group_name


        await WORK_CONTROL.add_group(group_name, group_users=list(group_users))
        await WORK_CONTROL.save_data()

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
        
        WORK_CONTROL = WorkControl(self.bot)

        member_id_list = set(WORK_CONTROL.datafile['groups'][group_name]["users"])
        member_mention = set()
        for member in [member1, member2, member3, member4, member5]:
            if member:
                member_id_list.add(member.id)
                member_mention.add(member.mention)
                # если нет пользователя в бд = добавить
                if not str(member.id) in WORK_CONTROL.datafile['users']:
                    await WORK_CONTROL.add_user(str(member.id), user_group=group_name)
                # если была у пользователя раньше группа = изменить её 
                elif WORK_CONTROL.datafile['users'][f"{member.id}"]['group']:
                    old_u_group = WORK_CONTROL.datafile['users'][f"{member.id}"]['group']
                    WORK_CONTROL.datafile['groups'][old_u_group]['users'].remove(member.id)
                    WORK_CONTROL.datafile['users'][f"{member.id}"]['group'] = group_name
                else:
                    WORK_CONTROL.datafile['users'][f"{member.id}"]['group'] = group_name

        await customisate_log(self.bot, admin_id=interaction.user.id, group_name=group_name, users=member_id_list, adding=True)

        WORK_CONTROL.datafile['groups'][group_name]["users"] = list(member_id_list)

        await WORK_CONTROL.save_data()

        await interaction.response.send_message(
            f"Для группы: `{group_name}`; \nДобавлены новые участники: {', '.join(member_mention)}", ephemeral=True)

    # удаление группы
    @app_commands.command(name='del_group', description="Удаляет группу")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def del_group(self, interaction: discord.Interaction, group_name: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        try:
            view = ShureDelGroupView(bot=self.bot, group_name=group_name)
            await interaction.response.send_message(f"Вы уверены что хотите удалить `{group_name}`?", view=view,
                                                    ephemeral=True)
        except Exception as e:
            print(e)

    # удаление в группе участников
    @app_commands.command(name='del_group_user', description="Удаляет указаной группе участника")
    @app_commands.autocomplete(member_id=select_user_autocomplete)
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    async def del_group_user(self, interaction: discord.Interaction, group_name: str, member_id: str):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        
        WORK_CONTROL = WorkControl(self.bot)

        if not int(member_id) in WORK_CONTROL.datafile['groups'][f"{group_name}"]["users"]:
            return await interaction.response.send_message(f"Ошибка: Пользователя <@{member_id}> нет в `{group_name}`",
                                                            ephemeral=True)

        view = ShureDelGroupUserView(bot=self.bot, group_name=group_name, member_id=int(member_id))
        await interaction.response.send_message(f"Вы уверены что хотите удалить <@{member_id}> из `{group_name}`?",
                                                view=view, ephemeral=True)

    # завершение работы
    @app_commands.command(name='finish_work', description="Завершение работы")
    @app_commands.autocomplete(user_work=select_u_work_name_autocomplete)
    @app_commands.autocomplete(group_work=select_g_work_name_autocomplete)
    async def  finish_work(self, interaction: discord.Interaction, user_work:str = None, group_work:str = None):
        WORK_CONTROL = WorkControl(self.bot)

        if user_work: # проверка вызова
            description, u_extra_notes, u_deadline, u_finished_work, manager_id = await WORK_CONTROL.load_work(
                user_work, user_id=f"{interaction.user.id}"
            )
            if u_finished_work:
                return await interaction.response.send_message(f'Работа `{user_work}` уже и так __завершена__.', ephemeral=True)

            WORK_CONTROL.datafile['users'][f"{interaction.user.id}"]['works'][user_work]['finished_work'] = True
            await WORK_CONTROL.save_data()

            manager = await self.bot.fetch_user(manager_id)
            embed = discord.Embed(title='Завершение работы', color=clr.FINISH_WORK_COLOR,
                                description=f"Пользователь <@{interaction.user.id}> завершил работу `{user_work}`!")
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)

            await end_work_log(self.bot, work_name=user_work, user_id=f"{interaction.user.id}")

            await manager.send(embed=embed)
        elif group_work: # проверка вызова
            group_name = WORK_CONTROL.datafile['users'][f"{interaction.user.id}"]['group']
            g_description, g_extra_notes, g_deadline, g_finished_work, manager_id = await WORK_CONTROL.load_work(
                group_work, group_name=group_name
            )
            if g_finished_work:
                return await interaction.response.send_message(f'Работа `{group_work}` уже и так __завершена__.', ephemeral=True)

            WORK_CONTROL.datafile['groups'][group_name]['works'][group_work]['finished_work'] = True
            await WORK_CONTROL.save_data()

            manager = await self.bot.fetch_user(manager_id)
            embed = discord.Embed(
                title='Завершение работы', color=clr.FINISH_WORK_COLOR,
                description=f"Пользователи группы `{group_name}` завершили работу `{group_work}`!"
            )

            await end_work_log(self.bot, work_name=group_work, group_name=group_name)

            await manager.send(embed=embed)
        else: # если ничего не вызвал
            return await interaction.response.send_message(f'Вы __не__ выбрали какую работу жаждите завершить.', ephemeral=True)
        embed = discord.Embed(
            title='Завершение работы', color=clr.FINISH_WORK_COLOR,
            description=f"Вы успешно завершили работу. \n"
                        f'- Менеджер <@{manager_id}> был оповещён про ваше завершение.'
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # информация про работы
    @app_commands.command(name='info', description="Показывает инфу работ пользователей и групп")
    @app_commands.autocomplete(group_name=select_group_autocomplete)
    @app_commands.autocomplete(member=select_user_autocomplete)
    async def info(self, interaction: discord.Interaction, group_name: str = None, member: str = None):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "3")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return
        
        WORK_CONTROL = WorkControl(self.bot)

        used_optional = False
        if group_name:
            check_1 = str(interaction.user.id) in self.bot.ctx.admins
            check_2 = self.bot.check_roles(interaction.user, "1")
            if not (check_1 or check_2):
                await interaction.response.send_message(f'У вас нет прав на просмотр информации о задачах групп',
                                                        ephemeral=True)
                return

            work_list = list(WORK_CONTROL.datafile['groups'][group_name]['works'].keys())
            if work_list:
                work_name = work_list[0]
            else:
                work_name = None
            
            embed = await WORK_CONTROL.load_embed(work_name, group_name=group_name)

            if len(work_list) > 1:
                embed.set_footer(text=f"1/{len(work_list)}")
                view = ScrollView(work_list=work_list, max_page=len(work_list), group_name=group_name, bot=self.bot) 
            else:
                view = None
            
            used_optional = True
            try:
                await interaction.user.send(embed=embed, view=view)
            except:
                await interaction.response.send_message(content='Откройте лс для получения информации', 
                                                            view=view,
                                                            ephemeral=True)


        if member:
            check_1 = str(interaction.user.id) in self.bot.ctx.admins
            check_2 = self.bot.check_roles(interaction.user, "1")
            if not (check_1 or check_2):
                await interaction.response.send_message(f'У вас нет прав на просмотр информации о задачах пользователей',
                                                        ephemeral=True)
                return
            
            member = await self.bot.fetch_user(member)
            if not str(member.id) in WORK_CONTROL.datafile["users"].keys():
                return await interaction.response.send_message(f"Пользователя <@{member.id}> нет в бд.", ephemeral=True)

            work_list = list(WORK_CONTROL.datafile['users'][str(member.id)]['works'].keys())
            if work_list:
                work_name = work_list[0]
            else:
                work_name = None
            
            embed = await WORK_CONTROL.load_embed(work_name, user_id=str(member.id))

            if len(work_list) > 1:
                embed.set_footer(text=f"1/{len(work_list)}")
                view = ScrollView(work_list=work_list, max_page=len(work_list), user_id=f"{member.id}", user_name=member.name, bot=self.bot) 
            else:
                view = None

            used_optional = True
            try:
                await interaction.user.send(embed=embed, view=view)
            except Exception as e:
                print(e)
                await interaction.response.send_message(content=f'Откройте лс для получения информации',
                                                            view=view,
                                                            ephemeral=True)


        if not used_optional:
            user_id = str(interaction.user.id)
            if not str(user_id) in WORK_CONTROL.datafile['users'].keys():
                return await interaction.response.send_message('Ошибка: О вас нет никакой информации', ephemeral=True)

            
            # инфа группы
            if WORK_CONTROL.datafile['users'][user_id]['group']:
                group_name = WORK_CONTROL.datafile['users'][user_id]['group']
                work_list = list(WORK_CONTROL.datafile['groups'][group_name]['works'].keys()) 
                if work_list:
                    work_name = work_list[0]
                else:
                    work_name = None

                embed = await WORK_CONTROL.load_embed(work_name, group_name=group_name)

                if len(work_list) > 1:
                    embed.set_footer(text=f"Страница: 1/{len(work_list)}")
                    view = ScrollView(work_list=work_list, max_page=len(work_list), group_name=group_name, bot=self.bot) 
                else:
                    view = None

                try:
                    await interaction.user.send(embed=embed, view=view)
                except:
                    await interaction.response.send_message(content='Откройте лс для получения информации', 
                                                                view=view,
                                                                ephemeral=True)

            # инфа пользователя
            if WORK_CONTROL.datafile['users'][user_id]['works'].keys():
                member = await self.bot.fetch_user(user_id)
                work_list = list(WORK_CONTROL.datafile['users'][str(member.id)]['works'].keys())
                if work_list:
                    work_name = work_list[0]
                else:
                    work_name = None

                embed = await WORK_CONTROL.load_embed(work_name, user_id=str(member.id))

                if len(work_list) > 1:
                    embed.set_footer(text=f"Страница: 1/{len(work_list)}")
                    view = ScrollView(work_list=work_list, max_page=len(work_list), user_id=f"{member.id}", user_name=member.name, bot=self.bot) 
                else:
                    view = None

                try:
                    await interaction.user.send(embed=embed, view=view)
                except Exception as e:
                    print(e)
                    await interaction.response.send_message(content=f'Откройте лс для получения информации',
                                                                view=view,
                                                                ephemeral=True)
        await interaction.response.send_message(content='Проверьте лс', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(work_notes(bot), guilds=bot.guilds)