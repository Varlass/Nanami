import discord, asyncio
from discord import ChannelType
from discord.ext import commands

from utils.check import check_list, check


class ArchiveCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(description = "копирование контента из одного канала в другой")
    @check({check_list["Roles"]["Смотритель"]})
    async def copy(self, ctx: commands.Context, *args: str):
        source = ctx.channel
        target = None

        for arg in args:
            if "=" not in arg:
                continue
            key, value = arg.split("=", 1)
            
            try:
                if key == "source":
                    source = await self.bot.fetch_channel(int(value))

                elif key == "target":
                    target = await self.bot.fetch_channel(int(value))
            except (ValueError, TypeError, discord.NotFound, discord.Forbidden) as error:
                print(error)


        if not target:
            create = {ChannelType.text: ctx.guild.create_text_channel,
                      ChannelType.forum: ctx.guild.create_forum}   
            target = await create[source.type](source.name)


        webhook = await target.create_webhook(name = "Webhook")
        if isinstance(source, discord.TextChannel):
            async for message in source.history(limit = None, oldest_first = True):
                content = "[Не найденно]"
                chunks = [content]
                files = []
                
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.size < 10 * 1024 * 1024:
                            files.append(await attachment.to_file())
                            content = None
                        else:
                            await ctx.send(f"{message.jump_url} имеет слишком тяжёлый файл.")
                
                if len(message.content) > 2000:
                    current = ""
                    chunks.remove(content)
                    for line in message.content.split("\n"):
                        if len(current) + len(line) + 1 > 2000:
                            chunks.append(current)
                            current = line
                        else:
                            current += "\n" + line
                    if current:
                        chunks.append(current)
                
                for content in chunks:
                    if message.embeds:
                        await webhook.send(content = message.content if message.content and len(message.content) <= 2000 else content, embeds = message.embeds, username = message.author.name, avatar_url = message.author.display_avatar.url)
                    else:
                        await webhook.send(content = message.content if message.content and len(message.content) <= 2000 else content, files = files, username = message.author.name, avatar_url = message.author.display_avatar.url)
                    await asyncio.sleep(1.2)
        
        elif isinstance(source, discord.ForumChannel):
            threads = []
            threads.extend(source.threads)
            async for thread in source.archived_threads():
                threads.append(thread)
            
            for thread in threads:
                content = None
                messages = [message async for message in thread.history(limit = None, oldest_first = True)]
                
                if messages[0].embeds:
                    await asyncio.sleep(1)
                    new_thread = await target.create_thread(name = thread.name, content = messages[0].content or content, embeds = messages[0].embeds if messages[0].embeds != None else None, files = [await files.to_file() for files in messages[0].attachments] if messages[0].attachments != None else None)
                else:
                    new_thread = await target.create_thread(name = thread.name, content = messages[0].content or content, files = [await files.to_file() for files in messages[0].attachments] if messages[0].attachments != None else None)
                
                for message in messages[1:]:
                    content = "[Не найденно]"
                    chunks = [content]
                    files = []
                    
                    if message.attachments:
                        for attachment in message.attachments:
                            if attachment.size < 10 * 1024 * 1024:
                                files.append(await attachment.to_file())
                                content = None
                            else:
                                await ctx.send(f"{message.jump_url} имеет слишком тяжёлый файл.")
                    
                    if len(message.content) > 2000:
                        current = ""
                        chunks.remove(content)
                        for line in message.content.split("\n"):
                            if len(current) + len(line) + 1 > 2000:
                                chunks.append(current)
                                current = line
                            else:
                                current += "\n" + line
                        if current:
                            chunks.append(current)
                    
                    for content in chunks:
                        if message.embeds:
                            await webhook.send(content = message.content if message.content and len(message.content) <= 2000 else content, embeds = message.embeds, username = message.author.name, avatar_url = message.author.display_avatar.url)
                        else:
                            await webhook.send(content = message.content if message.content and len(message.content) <= 2000 else content, files = files, username = message.author.name, avatar_url = message.author.display_avatar.url)

                        await asyncio.sleep(1.2)

        else:
            await ctx.reply("Некорректный тип копируемого канала.", delete_after = 5)

        await webhook.delete()
        await ctx.reply(f"Готово!\n{target.mention}")


async def setup(bot):
    await bot.add_cog(ArchiveCog(bot))