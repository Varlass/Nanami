from discord.ext import commands
from discord import Interaction, ButtonStyle, SelectOption, ChannelType
from discord.ext.commands import Cog, Bot, Context
from asyncio import sleep
from random import shuffle

from data.manager import FileManager
from utils.data_tools import text_to_collection
from utils.library.colors import *
from utils.render_tools import render_factory as render
from utils.check import check, check_list

from cogs.quiz.quizzeswork import autoquiz_manager


LANGS: list[str] = ["RU", "EN"]
descriptions = {"RU": ("Начать викторину",
                       "Приготовься!\nВикторина начнётся через 10 секунд."),
                "EN": ("Start Quiz",
                       "Get ready! Quiz starts in 10 seconds.")}

class OfflineQuizCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command()
    @check(check_list["Roles"]["Giveaways_Organiser"])
    async def quizspawn(self, ctx: Context):
        json_dict = FileManager("quiz_data/list.json").read()

        if not json_dict["use"]:
            return await ctx.send("Файлы автовикторины отсутствуют.")

        quiz_file = json_dict["quizzes"][json_dict["use"]]["name"]

        quiz_text = FileManager(f"quiz_data/{quiz_file}").read()

        quiz_dict = text_to_collection(quiz_text, list)
        shuffle(quiz_dict)
        lang = None

        message = render.Message(data = lang,
                                 embeds = [render.Embed(title = "Выберите язык викторины:",
                                                        description = lambda lang: (f"Файл автовикторины: `{quiz_file}`\n"
                                                                                    f"- {lang or "не указан"}"),
                                                        color = CREAM)],

                                 view = render.View(timeout = 6000,
                                                    data = {"quiz": quiz_dict,
                                                            "lang": lang},
                                                    selects = [render.Select(callback = lang_select,
                                                                             select_type = render.SelectType.option([SelectOption(label = lang, value = lang) for lang in LANGS]),
                                                                             placeholder = f"Выберите язык")],
                                                    buttons = [render.Button(callback = start_button,
                                                                             label = "Start",
                                                                             style = ButtonStyle.blurple,
                                                                             row = 3)]))

        message.view.data["message"] = message
        message_content = render.render(message)

        await ctx.send(**message_content)


async def lang_select(self, interaction: Interaction):
    lang = interaction.guild.get_channel(self.values[0])

    if self.data == lang:
        self.data = None

    else:
        self.data = lang

    await interaction.response.edit_message(**render.render(self.data["message"]))

async def start_button(self, interaction: Interaction):
    if not self.data["lang"]:
        return await interaction.response.send_message("Ещё не выбран язык.", ephemeral = True)

    message = render.Message(embeds = [render.Embed(title = self.data["lang"], description = descriptions[self.data["lang"][0]])],
                             view = render.View(data = self.data,
                                                buttons = render.Button(callback = start_quiz,
                                                                        style = ButtonStyle.green,
                                                                        label = "Start",)))

    message_content = render.render(message)

    await interaction.channel.send(**message_content)


async def start_quiz(self, interaction: Interaction):
    thread_name = f"{interaction.user.display_name}'s quiz"

    thread = await interaction.channel.create_thread(name = thread_name, type = ChannelType.private_thread, invitable = False)

    await thread.send(descriptions[self.data["lang"][1]])

    await sleep(10)

    await autoquiz_manager(self.data["quiz_data"], {thread_name: thread})


async def setup(bot: Bot):
    await bot.add_cog(OfflineQuizCog(bot))