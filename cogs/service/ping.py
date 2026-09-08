from discord.ext import commands

from utils.utils import ntime


class PingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description = "проверка отклика бота")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"`{round(ctx.bot.latency * 1000)} мс`")
        print(f"[{ntime().strftime("%H:%M:%S")}] Pong")

async def setup(bot: commands.Bot):
    await bot.add_cog(PingCog(bot))