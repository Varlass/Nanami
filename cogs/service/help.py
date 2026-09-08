import discord
from discord.ext import commands

from utils.library import colors

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description = "выводит все существующие команды и их описания", help = "test")
    async def help(self, ctx: commands.Context, command: str = None):
        description = ""

        if command:
            
            cmd = self.bot.get_command(command)
            if cmd and await cmd.can_run(ctx):
                description = f"- {cmd.name.title()} – {cmd.help or cmd.description or "Подробное описание отсутствует"}"
            else:
                description = f"Команда `{command}` не найдена"

        else:
            if self.bot.commands:
                text = "## Текстовые команды:\n"
                for text_command in self.bot.commands:
                    try:
                        if await text_command.can_run(ctx):
                            text += f"\n- **{text_command.name.title()}** – {text_command.description or "описание отсутствует"}."
                    except commands.CheckFailure:
                        continue
                description += text
            
            slash = ""
            slash_commands = list(self.bot.tree.walk_commands())
            if slash_commands:
                slash = "\n## Слэш команды:\n"
                for slash_command in slash_commands:
                    description_text = slash_command.description
                    if slash_command._guild_ids:
                        scope = "серверная"
                    else:
                        scope = "глобальная"
                    if not description_text or description_text.strip(".…") == "":
                        description_text = "описание отсутствует" 
                    slash += f"\n- **{slash_command.name.title()}** – {description_text} ({scope})."
                description += slash

        embed = discord.Embed(title = "Help", description = description[:3000], color = colors.RED)
        await ctx.send(embed = embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))