import discord, random, re
from discord.ext import commands

from utils.utils import ntime
from utils.check import check, check_list

channel_id = 1553071296110264420

class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.number = {}
        self.funcs = {self.activity,
                      self.reaction}

    @commands.command()
    @check({check_list["Channels"]["испытательный-полигон"]})
    async def price(self, ctx: commands.Context):
        channel: discord.TextChannel = await ctx.guild.fetch_channel(channel_id)

        members: set[discord.Member] = set()
        async for message in channel.history(limit = None):
            if message.author not in members:
                members.add(message.author)

        members: list[discord.Member] = list(members)
        random.shuffle(members)
        message1 = "## Hero/Battle pass:\n" + "\n".join(f"{number}. {member.mention}" for number, member in enumerate(members[:5], start = 1))
        message2 = "## Set:\n" + "\n".join(f"{number}. {member.mention}" for number, member in enumerate(members[-3:], start = 1))

        await ctx.send(message1 + "\n" + message2)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        for func in self.funcs:
            try:
                await func(message)
            except Exception as e:
                print(e)

    
    async def activity(self, message): # Отправка сообщения раз в n сообщений.
        chid = message.channel.id
        channels = [1285954945979256853, # │💬│общение-с-сервером
                    1271457430768717914] # │💬│main-chat

        text = ["{e:1193834090550534154}", # big_fih
                "🐲",
                "{e:1166864113306181642}", # kl_neco_arc
                "{e:1336006426673287298}", # Kimtya
                "{e:1192164618609639434}", # Im_thinking
                "{e:1192553794509230152}", # June_cute
                "<@1361759332462624868> 🐲",
                "{e:1516568431376208003}", # Calamitas
                "{e:1192206490518433945}", # Gosling
                "{e:1454536821089374394}", # cool_dragon_face
                "{e:1516520566289465547}", # chavo
                "{e:1325193954718781440}", # Kaguya
                "{e:1515004394540761098}", # pavlik
                "{e:1287036452172992546}"] # Chill

        if chid not in channels:
            return

        self.number[chid] = self.number.get(chid, 0) + 1

        if self.number[chid] >= 100:
            self.number[chid] = 0

            random_text = random.choice(text)
            try: # Небольшой костыль для краткости кода.
                random_text = re.sub(r"\{e:(\d{17,19})\}", lambda emoji: str(self.bot.get_emoji(int(emoji.group(1)))) if self.bot.get_emoji(int(emoji.group(1))) else False, random_text)
                await message.channel.send(random_text)
            except TypeError:
                print("Varlass, проверь список эмодзи.")


    async def reaction(self, message): # Реакция на триггер.
        rules = [(lambda m: self.bot.user.mention == m.content.split(), lambda m: m.reply("Чего хотел?")),
                 (lambda m: m.reference and m.reference.resolved.author == self.bot.user and "привет" in re.sub(r"[^\w\s]", "", m.content.lower()), lambda m : m.reply("Привеет!")),
                 (lambda m: m.reference and m.reference.resolved.author == self.bot.user and "как дела" in re.sub(r"[^\w\s]", "", m.content.lower()), lambda m : m.reply("Отлично"))]
        
        for check, action in rules:
            if check(message):
                await action(message)


async def setup(bot):
    await bot.add_cog(FunCog(bot))