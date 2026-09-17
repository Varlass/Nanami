import asyncio, random
from discord.ext import commands
from discord import Interaction, File, ButtonStyle
from discord.ext.commands import Cog, Bot, Context

from data.manager import DIR, json_manage
from utils.data_tools import text_to_collection
from utils.check import check, check_list
from utils import render_tools as render
from utils.utils import ntime
from utils.library import colors

from cogs.quiz.quizzeswork import autoquiz_manager


dir = DIR/"quiz_data"
langs = ["RU", "EN"]

class AutoquizCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(description = "запуск автоматической викторины")
    @check({check_list["Roles"]["Giveaways_Organiser"]})
    async def autoquiz(self, ctx: Context):
        json_dict = json_manage.read("list", dir = dir)

        if not json_dict["use"]:
            return await ctx.send("Файлы автовикторины отсутствуют.")

        quiz_file = json_dict["quizzes"][json_dict["use"]]["name"]

        with open(dir/quiz_file, "r", encoding = 'utf-8') as file:
            quiz_text = file.read()

        quiz_dict = text_to_collection(quiz_text, [])
        random.shuffle(quiz_dict)
        channels = {lang: None for lang in langs}

        message = render.Message(data = {"channels": channels},
                                 embeds = [render.Embed(title = "Выберите каналы для викторины:",
                                                        description = lambda data: (f"Файл автовикторины: `{quiz_file}`\n"
                                                                                    f"- RU: {data["channels"]['RU'] or 'не указан'}\n"
                                                                                    f"- EN: {data["channels"]['EN'] or 'не указан'}"),
                                                        color = colors.CREAM)],

                                 view = render.View(timeout = 6000,
                                                    data = {"channels": channels,
                                                            "quiz": quiz_dict,
                                                            "flag": asyncio.Event()},
                                                    selects = [render.Select(callback = lang_select,
                                                                             select_type = render.SelectType.text_channel,
                                                                             custom_id = lang,
                                                                             placeholder = f"{lang} channel") for lang in langs],
                                                    buttons = [render.Button(callback = start_button,
                                                                             label = "Start",
                                                                             style = ButtonStyle.blurple,
                                                                             row = 3),
                                                               render.Button(callback = stop_button,
                                                                              label = "Stop",
                                                                              custom_id = "stop_button",
                                                                              style = ButtonStyle.red,
                                                                              row = 3,
                                                                              disabled = True)]))

        message.view.data["message"] = message
        message_content = render.render(message)

        await ctx.send(**message_content)



    @commands.command(description = "добавление файлов для autoquiz")
    @check({check_list["Roles"]["Giveaways_Organiser"]})
    async def quizadd(self, ctx: Context, *, comment: str = ""):
        attachments = ctx.message.attachments

        if not attachments:
            await ctx.reply(file = File(dir/"quiz_table.txt"), mention_author = False)

        else:
            json_dict = json_manage.read("list", dir = dir)
            index = max(map(int, json_dict["quizzes"]), default = 0)
            new_dict = {}

            for attachment in attachments:
                try:
                    data = await attachment.read()
                    data.decode("utf-8")

                except UnicodeDecodeError:
                    await ctx.send(f"Недопустимый файл: {attachment.filename}.")
                    continue

                index += 1

                if attachment.filename == "quiz_table.txt":
                    attachment.filename = f"quiz_number_{index}.txt"

                await attachment.save(dir/attachment.filename)
                new_dict[str(index)] = {"name": attachment.filename,
                                        "comment": comment,
                                        "added_at": int(ntime().timestamp()),
                                        "last_used_at": None,
                                        "usage_count": 0}

            json_dict["use"] = str(index)
            json_dict["quizzes"].update(new_dict)
            json_manage.write("list", json_dict, dir = dir)

            if new_dict:
                await ctx.send(f"Файлы `{",".join([file["name"] for file in new_dict.values()])}` успешно сохранены.")

            

    @commands.command(description = "навигация по файлам autoquiz (не готово)")
    @check({check_list["Roles"]["Giveaways_Organiser"]})
    async def quizsearch(self, ctx: Context):
        ...


async def start_button(self, interaction: Interaction):
    log_channel = interaction.channel
    quiz_channels = self.data["channels"]
    quiz = self.data["quiz"]

    if not any(quiz_channels.values()):
        return await interaction.response.send_message("Не выбран ни один канал.", ephemeral = True)

    for children in self.view.children:
        if children.custom_id == "stop_button":
            children.disabled = False

        else:
            children.disabled = True

    await interaction.response.edit_message(view = self.view)

    await log_channel.send("# Викторина началась!")
    await autoquiz_manager(quiz, quiz_channels, log_channel, self.data["flag"])

    for children in self.view.children:
        if children.custom_id == "stop_button":
            children.disabled = True
            break

async def stop_button(self, interaction: Interaction):
    self.data["flag"].set()

    button = next(item for item in self.view.children if item.custom_id == "stop_button")
    if button:
        button.disabled = True
        await interaction.response.edit_message(view = self.view)

    else:
        await interaction.response.defer()

async def lang_select(self, interaction: Interaction):
    channel = interaction.guild.get_channel(self.values[0].id)

    if self.data["channels"][self.custom_id] == channel:
        self.data["channels"][self.custom_id] = None

    else:
        self.data["channels"][self.custom_id] = channel

    await interaction.response.edit_message(**render.render(self.data["message"]))

async def setup(bot: Bot):
    await bot.add_cog(AutoquizCog(bot))