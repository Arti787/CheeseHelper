import discord
from discord import app_commands, ui
from discord.ext import commands
import json
import os
import pygsheets
from datetime import datetime, timedelta

# Авторизация
gc = pygsheets.authorize(service_file='docstransfer.json')



#[['первый ник или id', 'второй id или ник','устное предупреждение(уп) пред бан или прочее', 'номер (1.2, 1.3.1 и прочее)', 'доп матириалы'], [и так далее...], ...]

class ReportProcessor:
    def __init__(self):
        # You can add any attributes or methods you need for the class here
        pass

    def capitalize_first_letter(self, s: str) -> str:
        s = s.lower()
        s = s.capitalize()
        return s

    async def process_report(self, raw_report):
        # This is the same code as before, but now it is a method of the class
        report_list = []
        res_report_list = []
        last_report_j = -1
        mode_switch = 0

        for j, report in enumerate(raw_report):
            report_time, author_id, report_str, attachments, link, message, view_reaction = report
            if "2023-08-24 00:05:28" in report_time:
                print("мя")
            if report_str == '':
                report_list.append(["", ""])
                continue
            if report_str[0] == "1":
                mode_switch = 1
                report_list.append([report_time, author_id])
                start = report_str.find("1")
                end = -1
                for i in range(start + 1, len(report_str)):
                    if report_str[i] == "2" and not (report_str[i - 1].isdigit() or report_str[i + 1].isdigit()):
                        end = i
                        break
                if end != -1:
                    processed_str = report_str[start + 1:end].lstrip(" ).;").replace("\n", "")
                    report_list[j].append(processed_str)
                    start = end + 1
                    end = report_str.find("3", start)
                    if end != -1:
                        processed_str = report_str[start + 1:end].lstrip(" ).;").replace("\n", "")
                        report_list[j].append(self.capitalize_first_letter(processed_str))
                        start = end + 1
                        end = report_str.find("\n", start)
                        if end != -1:
                            processed_str = report_str[start + 1:end].lstrip(" ).;").replace("\n", "")
                            report_list[j].append(f"|{processed_str}")
                            start = end + 1
                            processed_str = report_str[start:].lstrip(" ).;").replace("\n", "")
                            report_list[j].append(processed_str)
                        else:
                            processed_str = report_str[start + 1:].lstrip(" ).;").replace("\n", "")
                            report_list[j].append(f"|{processed_str}")
                    else:
                        report_list[j].append("")
                        if attachments:
                            if len(report_list[j]) < 6:
                                report_list[j].append("")
                            if len(report_list[j]) > 5:
                                report_list[j][5] += " ;" + " ;".join(attachments)
                            else:
                                report_list[j].extend([""] * (6 - len(report_list[j])))
                                report_list[j][5] = " ;" + " ;".join(attachments)

                        else:
                            start = end + 1
                            end = report_str.find("\n", start)
                            if end != -1:
                                processed_str = report_str[start + 1:end].lstrip(" ).;").replace("\n", "")
                                report_list[j].append(processed_str)
                                start = end + 1
                                processed_str = report_str[start:].lstrip(" ).;").replace("\n", "")
                                report_list[j].append(processed_str)
                            else:
                                processed_str = report_str[start + 1:].lstrip(" ).;").replace("\n", "")
                                report_list[j].append(processed_str)
                                mode_switch = 2
                                last_report_j = j
                else:
                    report_list[j].extend(["", "", ""])
                if attachments:
                    if len(report_list[j]) < 6:
                        report_list[j].append("")
                    if len(report_list[j]) > 5:
                        report_list[j][5] += " ;" + " ;".join(attachments)
                        report_list[j][5] = report_list[j][5][report_list[j][5].find('h'):] if 'h' in report_list[j][5] else report_list[j][5]
                        report_list[j].append(link)

                    else:
                        report_list[j].extend([""] * (6 - len(report_list[j])))
                        report_list[j][5] = " ;" + " ;".join(attachments)
                        report_list[j][5] = report_list[j][5][report_list[j][5].find('h'):] if 'h' in report_list[j][
                            5] else report_list[j][5]
                        report_list[j].append(link)

                    print(report_list[j])
                    res_report_list.append(report_list[j])
                    if not view_reaction:
                        await message.add_reaction('✅')
                else:
                    if len(report_list[j]) < 6:
                        report_list[j].append("")
                        res_report_list.append(report_list[j])
                        if not view_reaction:
                            await message.add_reaction('✅')
                    else:
                        report_list[j].append(link)
                        res_report_list.append(report_list[j])
                        if not view_reaction:
                            await message.add_reaction('✅')
            else:
                report_list.append(["", ""])
                if not view_reaction:
                    await message.add_reaction('❌')

        return res_report_list


class DocsTransfer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = self.bot.ctx.docs_transfer_report_channel_id

    @commands.Cog.listener()
    async def on_ready(self):
        print("отчёты")

    def convert_to_utc_plus_3(self, datetime_str):
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        dt = dt + timedelta(hours=3)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == self.channel_id:
            channel = self.bot.get_channel(self.channel_id)
            guild = channel.guild

            messages = []
            async for message in channel.history(limit=None):
                messages.append(message)

            raw_report = []
            for message in messages:
                message_time = self.convert_to_utc_plus_3(message.created_at.strftime('%Y-%m-%d %H:%M:%S'))
                author_id = str(f"{message.author.name} ({message.author.id})")
                content = message.content
                attachments = [attachment.url for attachment in message.attachments]
                link = message.jump_url
                message = message
                view_reaction = any(reaction.emoji == '✅' or reaction.emoji == '❌' for reaction in message.reactions)
                raw_report.append([message_time, author_id, content, attachments, link, message, view_reaction])

            processor = ReportProcessor()

            processed_report = await processor.process_report(raw_report)

            # Открытие таблицы по ее идентификатору
            sh = gc.open_by_key(self.bot.ctx.docs_transfer_spreadsheet_key)
            # Добавление нового листа
            rep = sh[0]

            # Заполнение данных
            rep.update_values(f'A6:G{len(processed_report) + 5}', processed_report)
            # print(processed_report)

            banned_users = []
            async for entry in guild.bans():  # получаем список забаненных пользователей

                user = entry.user
                if entry.reason != None:
                    if "(ID: " in entry.reason:  # Джунипер
                        author_id, reason = self.juniper_parse(entry.reason)
                        author = await self.bot.fetch_user(int(author_id))
                        author_str = str(f"{author.name} ({author.id})")
                        banned_users.append(["", author_str, str(user.id), reason])
                        print("", author_str, str(entry.user.id), reason)
                    elif "проверяющий: " in entry.reason:  # ФЫР (бот спикера)
                        if entry.reason == 'проверяющий: Hector Medina#4637 Забанил пользователя':
                            print("мя")
                        author_id = self.fir_parse(entry.reason)
                        author = discord.utils.get(self.bot.users, name=author_id.split('#')[0],
                                                   discriminator=author_id.split('#')[1])
                        author_str = str(f"{author.name} ({author.id})")
                        banned_users.append(["", author_str, str(user.id), ""])
                        print("", author_str, str(user.id), "")
                    else:
                        author = await self.bot.fetch_user(user.id)
                        author_str = str(f"{author.name} ({author.id})")
                        banned_users.append(
                            ["", "", str(user.id), entry.reason])  # добавляем в список
                        print("", "", str(user.id), entry.reason)
                else:
                    author = await self.bot.fetch_user(user.id)
                    author_str = str(f"{author.name} ({author.id})")
                    banned_users.append(
                        ["", "", str(user.id), ""])  # добавляем в список
                    print("", "", str(user.id), "")

            for i in range(len(banned_users)):
                banned_users.append(["", "", "", ""])  # добавляем пустые строки для красоты
            print(banned_users)
            # Добавление нового листа
            ban = sh[1]

            # Заполнение данных
            ban.update_values(f'A6:D{len(banned_users) + 5}', banned_users)
            # print(banned_users)

    def juniper_parse(self, message: str):
        print(message)
        author_id = message.split(":")[1].split(")")[0].split(" ")[1].strip()
        try:
            reason = message.split(":")[2].strip()
        except:
            reason = ""
        return author_id, reason

    def fir_parse(self, message: str):
        parts = message.split(":")
        author_id = parts[1].split(" ")[1].strip()
        return author_id

    from typing import List, Tuple

    def sort_by_time(self, data):
        # Преобразуем строки с датами в объекты datetime
        from datetime import datetime
        for item in data:
            item[0] = datetime.strptime(item[0], '%Y-%m-%d %H:%M:%S')
        # Сортируем данные по времени в порядке убывания
        data.sort(key=lambda x: x[0], reverse=True)
        # Преобразуем объекты datetime обратно в строки
        for item in data:
            item[0] = item[0].strftime('%Y-%m-%d %H:%M:%S')
        return data

    @app_commands.command(name="отчёты", description="Синхронизировать отчёты в Google docs")
    async def DocsTransfer(self, interaction: discord.Interaction):
        check_1 = str(interaction.user.id) in self.bot.ctx.admins
        check_2 = self.bot.check_roles(interaction.user, "1,2")
        if not (check_1 or check_2):
            await interaction.response.send_message(f'У вас нет прав на использование данной команды', ephemeral=True)
            return

        # Начиная отсюда код:
        await interaction.response.send_message(f'отчёты синхронизируются. подождите...', ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DocsTransfer(bot), guilds=bot.guilds)