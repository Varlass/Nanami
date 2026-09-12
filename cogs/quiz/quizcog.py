from discord.ext import commands
from discord.ui import Modal, TextInput
from discord import Interaction, TextChannel, ButtonStyle, TextStyle
from discord.ext.commands import Cog, Bot, Context

from utils.check import check, check_list
from utils.render_tools import render_factory as render
from utils.library import colors
from utils.data_tools import collection_to_object

from cogs.quiz.quizzeswork import QuizContext, quiz_manager, translate


QUESTION_TYPES = {"FREE": 1,
                  "CHOICE": 4,
                  "SEQUENTIAL": 4}

class QuizCog(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(description = "запуск ручной викторины")
    @check({check_list["Roles"]["Giveaways_Organiser"]})
    async def quiz(self, ctx: Context, channel: TextChannel = None):
        if not channel:
            channel = ctx.channel

        context = QuizContext("Handquiz")
        context.log_channel = ctx.channel

        message = render.Message(embeds = [render.Embed(title = "Панель управления викториной",
                                                        description =  f"""Текущий канал викторины: {channel.mention}
                                                                           \n- `Свободный` – позволяет создать вопрос со свободным вводом ответа.
                                                                           \n- `Выбор` – позволяет создать вопрос с несколькими вариантами ответа.
                                                                           \n- `Последовательность` – позволяет создать вопрос с цепочкой ответов.
                                                                           \n- `Завершить` – отключает возможность ответить на последний вопрос и подсчитывает баллы (можно использовать для перерыва между этапами, баллы сохраняются между этапами).""",
                                                        color = colors.CREAM)],

                                 view = render.View(data = collection_to_object({"context": context,
                                                                                 "channel": channel}),
                                                    timeout = None,
                                                    buttons = [render.Button(label = question_type.title(),
                                                                             style = ButtonStyle.green,
                                                                             custom_id = question_type,
                                                                             callback = question_create) for question_type in QUESTION_TYPES.keys()]
                                                              +
                                                              [render.Button(label = "Stop",
                                                                             style = ButtonStyle.red,
                                                                             callback = end_button)]))

        await ctx.send(**render.render(message))


async def question_create(self, interaction: Interaction):
    await self.data.context.close_answer()

    modal = QuizModal(self.custom_id, self.data)
    await interaction.response.send_modal(modal)

async def end_button(self, interaction: Interaction):
    await interaction.response.defer()
    await self.data.context.close_quiz()

class QuizModal(Modal):
    def __init__(self, question_type: str, data: dict):
        super().__init__(title = "Вопрос с несколькими вариантами ответа")
        self.add_item(TextInput(label = "Вопрос:", style = TextStyle.paragraph))
        self.add_item(TextInput(label = "Правильный ответ:", placeholder = "Старайтесь делать короткий ответ"))

        for _ in range(QUESTION_TYPES[question_type] - 1):
            self.add_item(TextInput(label = "Ответ:", placeholder = "Старайтесь делать короткий ответ", required = False))

        self.question_type = question_type
        self.data = data

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()
        number = self.data.context.number()

        question_dict = {"Number": number,
                         "Type": self.question_type,
                         "Question": self.children[0].value,
                         "Answers": [answer.value.strip().lower() for answer in self.children[1:]],
                         "Points": 1}

        self.data.context.log[number] = await quiz_manager(question_dict, translate["RU"], self.data["channel"], self.data["context"])

async def setup(bot: Bot):
    await bot.add_cog(QuizCog(bot))