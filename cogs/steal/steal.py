import discord, re, aiohttp, io
from discord.ext import commands
from PIL import Image


class StealCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description = "получает эмодзи или стикер из сообщения, на которое ответили")
    async def steal(self, ctx: commands.Context):
        message = ctx.message.reference.resolved

        if not message:
            return await ctx.reply("Ответьте на сообщение, из которого хотите вытянуть эмодзи или стикер.", delete_after = 5)

        data = []

        matches = re.findall(r"<a?:\w+:\d+>", message.content)
        for raw_emoji in matches:
            emoji = discord.PartialEmoji.from_str(raw_emoji)
            data.append((emoji.name, emoji.url))

        for sticker in message.stickers:
            data.append((sticker.name, sticker.url))

        for attachment in message.attachments:
            data.append((attachment.filename, attachment.url))

        if not data:
            return await ctx.reply("В этом сообщении нет эмодзи или стикера.", delete_after = 5)

        images = await self.convert(data)

        try:
            for filename, image in images:
                await ctx.author.send(content = "Если вы обнаружили ошибку, сообщите об этом при помощи кнопки ниже.",
                                      file = discord.File(image,filename = filename))

        except discord.Forbidden:
            for filename, image in images:
                await ctx.reply(content = "❗**Пожалуйста, откройте личные сообщения дабы я могла отправлять вам эмодзи и стикеры, не засоряя чат.**❗",
                                file = discord.File(image, filename = filename),
                                delete_after = 10)


    async def convert(self, data: list):
        images = []

        for name, url in data:
            byte = await self.upload(url)
            frames = self.load_frames(byte)
            frames = self.normalize_side(frames)
            filename, image = self.encoding(frames, name)
            images.append((filename, image))

        return images


    async def upload(self, url: str) -> bytes:
        async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    return await resp.read()


    def load_frames(self, byte: bytes):
        image = Image.open(io.BytesIO(byte))

        frames = []
        for i in range(image.n_frames):
            image.seek(i)
            frame = image.convert("RGBA").copy()
            frames.append(frame)

        return frames


    def normalize_side(self, frames: list, max_size = 256) -> list:
        result = []

        for frame in frames:
            width, height = frame.size

            scale = min(max_size / width, max_size / height, 1.0)
            new_width, new_height = int(width * scale), int(height * scale)

            frame = frame.resize((new_width, new_height), Image.Resampling.BILINEAR)

            size = max(new_width, new_height)

            new_frame = Image.new("RGBA", (size, size))

            x = (size - new_width) // 2
            y = (size - new_height) // 2

            new_frame.alpha_composite(frame, (x, y))

            result.append(new_frame)

        return result


    def encoding(self, frames: list, name: str = "image"):
        output = io.BytesIO()

        if len(frames) == 1:
            frames[0].save(output, format = "PNG")
            filename = f"{name}.png"

        else:
            frames[0].save(output,
                           format = "GIF",
                           save_all = True,
                           append_images = frames[1:],
                           loop = 0,
                           duration = 100,
                           disposal = 2,
                           optimise = False)
            filename = f"{name}.gif"

        output.seek(0)
        return filename, output

async def setup(bot):
    await bot.add_cog(StealCog(bot))