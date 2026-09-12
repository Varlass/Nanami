import asyncio, tempfile, pathlib, random, json
from discord import TextChannel, Interaction, File, Message, Member, User, TextStyle
from discord.ui import Modal, View, TextInput

from utils.render_tools import render_factory as render
from utils.data_tools import container_to_object
from utils.library import colors
from utils.utils import ntime


translate = {"RU": {"Title": "Вопрос №{}",
                    "Button_Title": "Ответить",
                    "Button_End_Answer": "Ваш ответ был услышан"},
             "EN": {"Title": "Question №{}",
                    "Button_Title": "Answer",
                    "Button_End_Answer": "Your answer was heard"}}

class QuizContext:
    def __init__(self, quiz_type: str  = "Quiz"):
        self.log_channel: TextChannel|None = None

        self.quiz_number: int = 0
        self.messages: dict[Message, View] = {}
        self.points: dict[Member, int] = {}
        self.log: dict = {"Quiz_Type": quiz_type}

    def number(self):
        self.quiz_number += 1
        return self.quiz_number

    def price(self, user: Member, user_answer: list[str], correct_answer: list[str], points: int = 1) -> bool:
        if user not in self.points.keys():
            self.points[user] = 0

        if user_answer == correct_answer:
            self.points[user] += int(points)
            return True

        return False

    def result(self) -> tuple[list[str], list[str]]:
        chat = []
        console = []

        for place, (user, points) in enumerate(sorted(self.points.items(), key = lambda user: user[1], reverse = True), 1):
            chat.append(f"\n{place}. {user.mention}: {points};")
            console.append(f"\n{place}. {user.name}: {points};")
            
        return chat, console

    async def close_answer(self):
        for message, view in self.messages.items():
            for button in view.children:
                button.disabled = True

            await message.edit(view = view)

        for lang in self.log:
            self.log[lang][str(self.quiz_number)]["ended_at"] = int(ntime().timestamp())

        self.messages.clear()

    async def close_quiz(self):
        await self.close_answer()
        chat, console = self.result()

        with tempfile.NamedTemporaryFile(mode = "w", encoding = "utf-8", suffix = ".json", delete = False) as file:
            json.dump(self.log, file, ensure_ascii = False, indent = 4)
        log_path = pathlib.Path(file.name)
        log_file = File(log_path, filename = "quiz_log.json")

        if len("".join(chat)) <= 1950:
            await self.log_channel.send("# Викторина завершена!" + "".join(chat), file = log_file)

        else:
            with tempfile.NamedTemporaryFile(mode = "w", encoding = "utf-8", suffix = ".txt", delete = False) as file:
                file.write("".join(console))
            text_path = pathlib.Path(file.name)
            text_file = File(text_path, filename = "quiz_result.txt")

            try:
                await self.log_channel.send("# Викторина завершена!", files = [text_file, log_file])

            finally:
                text_path.unlink(True)

        log_path.unlink(True)

        print(f"\033[34m[{ntime().strftime("%H:%M:%S")}]\nВикторина завершена!" + "".join(console) + "\033[0m")


async def autoquiz_manager(quiz: list[dict], quiz_channels: dict[TextChannel], log_channel: TextChannel, flag: asyncio.Event):
    context = QuizContext("Autoquiz")
    context.log_channel = log_channel

    for question in quiz:
        number = str(context.number())

        for lang, channel in quiz_channels.items():
            if channel == None:
                continue

            question_dict = {"Number": number,
                             "Type": question["Type"],
                             "Question": question["QUESTIONS"][lang],
                             "Answers": [answer.strip() for answer in question["ANSWERS"][lang] if answer.strip()],
                             "Points": question["Points"]}

            context.log[lang][number] = await quiz_manager(question_dict, translate[lang], channel, context)

        await asyncio.sleep(60)
        await context.close_answer()

        if flag.is_set():
            break

        _, console = context.result()
        await log_channel.send("## Промежуточные результаты:" + "".join(console))

    await context.close_quiz()


async def quiz_manager(question: dict[str, str], text: dict[str, str], channel: TextChannel, context: QuizContext):
    correct_answer = [question["Answers"][0].lower()] if question["Type"] != "SEQUENTIAL" else [answer.lower() for answer in question["Answers"].copy()]

    data = container_to_object({"correct_answer": None,
                                "context": context,
                                "members": None,
                                "points": question["Points"],
                                "end_text": text["Button_End_Answer"],
                                "log_block": None},
                                [member_check, end_button])

    data.log_block = {"type": question["Type"],
                      "question": question["Question"],
                      "correct_answer": correct_answer,
                      "answers": question["Answers"],
                      "points": question["Points"],
                      "started_at": int(ntime().timestamp()),
                      "ended_at": None,
                      "users_data": []}
    data.correct_answer = correct_answer
    data.members = {}

    random.shuffle(question["Answers"])

    render_view = render.View(data = data,
                       timeout = 3600,
                       buttons = [render.Button(label = answer if question["Type"] != "FREE" else text["Button_Title"],
                                                custom_id = answer.lower(),
                                                callback = TYPE_MAP[question["Type"]]) for answer in question["Answers"]])

    render_message = render.Message(embeds = [render.Embed(title = text["Title"].format(question["Number"]),
                                                           description = question["Question"],
                                                           color = colors.BLUE)],
                                    view = render_view)

    dict_message = render.render(render_message)

    context.messages[await channel.send(**dict_message)] = dict_message["view"]
    return data.log_block


async def free_button(self, interaction: Interaction):
    if self.data.member_check(interaction.user, answer = self.custom_id):
        return await interaction.response.defer()

    await interaction.response.send_modal(FreeModal(self.data))

async def choice_button(self, interaction: Interaction):
    if self.data.member_check(interaction.user, answer = self.custom_id):
        return await interaction.response.defer()

    await self.data.end_button(interaction, self.custom_id, 1, self.data.end_text)

async def sequential_button(self, interaction: Interaction):
    if self.data.member_check(interaction.user, answer = self.custom_id):
        return await interaction.response.defer()

    await self.data.end_button(interaction, self.custom_id, len(self.view.children), self.data.end_text)

class FreeModal(Modal):
    def __init__(self, data):
        super().__init__(title = "Ваш ответ")
        self.add_item(TextInput(label = "Ответить", style = TextStyle.paragraph))
        self.data = data

    async def on_submit(self, interaction: Interaction):
        await self.data.end_button(interaction, self.children[0].value.strip().lower(), 1, self.data.end_text)


def member_check(self, user: User, *, max_answers: int|None = None, answer: str|None = None) -> bool:
    if user.id not in self.members:
        self.members[user.id] = []
        return False

    answerer = self.members[user.id]
    if max_answers and len(answerer) == max_answers:
        return True

    if answer and answer in answerer:
        return True

    return False

async def end_button(self, interaction: Interaction, answer: str, max_answers: int, end_text: str):
    self.members[interaction.user.id].append(answer)

    if self.member_check(interaction.user, max_answers = max_answers):
        correct = self.context.price(interaction.user, self.members[interaction.user.id], self.correct_answer, self.points)
        self.log_block["users_data"].append({"user_id": interaction.user.id,
                                            "user_name": interaction.user.name,
                                            "answer": self.members[interaction.user.id],
                                            "answered_at": int(ntime().timestamp()),
                                            "correct": correct})

        await interaction.response.send_message(end_text, ephemeral = True)

    else:
        await interaction.response.defer()

TYPE_MAP = {"FREE": free_button,
            "CHOICE": choice_button,
            "SEQUENTIAL": sequential_button}