from discord.ext import commands
from groq import Groq, RateLimitError
from dotenv import load_dotenv
from os import getenv
load_dotenv()

from utils.check import check, check_list
from data.manager import DIR
from utils.utils import ntime


CLIENT = Groq(api_key = getenv("API_KEY"), max_retries = 0)
SYSTEM_PROMPT = """
Отвечай кратко, но добавляй краткое пояснение или контекст, если он помогает понять ответ.
Используй поиск для проверки фактов, особенно если информация может быть неточной или устаревшей.
Не используй внутренние спецсимволы и ссылки.
"""

class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.num = 0

    @commands.command(description = "поиск в интернете через ии")
    @check({check_list["Channels"]["испытательный-полигон"]})
    async def search(self, ctx: commands.Context, *, text: str = None):
        if text == None:
            return

        message = await ctx.reply("`Думаю...`", mention_author = False)

        try:
            start_time = ntime()

            answer = CLIENT.chat.completions.create(model = "openai/gpt-oss-20b",
                                                    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                                                                {"role": "user", "content": text}],
                                                    tools = [{"type": "browser_search"}],
                                                    reasoning_effort = "low",
                                                    tool_choice = "auto")
            content = answer.choices[0].message.content
            self.num += 1

            log = [f"----- TRY {self.num} -----",
                   f"START_TIME: {start_time.strftime("%d/%m/%Y | %H:%M:%S")}",
                   f"END_TIME: {ntime().strftime("%d/%m/%Y | %H:%M:%S")}",
                   f"DURATION: {(ntime() - start_time).total_seconds():.2f}s",
                   f"QUESTION: {text}",
                   f"ANSWER: {content}",
                   f"USAGE: {answer.usage}",
                   f"\nOTHER: model=openai/gpt-oss-20b, reasoning_effort=low, tool_choice=auto",
                   "\n\n\n"]

            with open(DIR/"search.log", "a", encoding = "utf-8") as file:
                file.write("\n".join(log))

        except RateLimitError as error:
            content = f"Достигнут лимит токенов.\nПопробуйте снова через: {error.response.headers.get("x-ratelimit-reset-tokens")}"

        await message.edit(content = content)

async def setup(bot: commands.Bot):
    await bot.add_cog(SearchCog(bot))