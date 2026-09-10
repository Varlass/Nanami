import traceback
from discord import Guild, Intents
from discord.ext.commands import Bot, Context, when_mentioned_or, CommandNotFound, CheckFailure, BotMissingPermissions
from pathlib import Path
from importlib import import_module
from dotenv import load_dotenv
from os import getenv
load_dotenv()

from utils.check import check_list
from data.app.manager import db_manage, DefaultData


class MyBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id in list(check_list["Guilds"].values()):
                continue
            await guild.leave()


    async def on_guild_join(self, guild: Guild):
        if guild.id in list(check_list["Guilds"].values()):
            return
        await guild.leave()


    async def on_command_error(self, ctx: Context, error):
        error = getattr(error, "original", error)
        if isinstance(error, (CommandNotFound, CheckFailure)):
            return

        if isinstance(error, BotMissingPermissions):
            return await ctx.reply("У меня недостаточно прав для выполнения команды.", mention_author = False, delete_after = 10)

        await ctx.send(f"Неизвестная ошибка.\n<@{check_list["Members"]["_varlass_"]}>")
        traceback.print_exception(type(error), error, error.__traceback__)


    async def setup_hook(self):
        root = Path(__file__).resolve().parent

        for file in (root / "cogs").rglob("*.py"):
            if file.name.startswith("_"):
                continue

            module_name = ".".join(file.relative_to(root).with_suffix("").parts)

            try:
                module = import_module(module_name)
                
                if hasattr(module, "setup"):
                    await module.setup(self)

            except Exception:
                print(traceback.format_exc())


TOKEN = getenv("TOKEN")

prefix = when_mentioned_or("n!", "N!")

intents = Intents().default()
intents.members = True
intents.messages = True
intents.message_content = True

bot = MyBot(command_prefix = prefix, intents = intents, help_command = None, case_insensitive = True)


if __name__ == "__main__":
    try:
        DefaultData().init_files()
        bot.run(TOKEN)

    finally:
        db_manage.close_all()