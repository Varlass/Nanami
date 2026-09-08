import datetime, asyncio
from datetime import datetime, timezone
from discord.ext import commands


def ntime() -> datetime: # Текущее время.
    return datetime.now(timezone.utc)


async def loading(activity: asyncio.Event = None, ctx: commands.Context = None, *, console: bool = True): # Пассивное отписывание в чат и терминал раз в n секунд (полезно для долгих функций).
    loading = "Loading"
    stime = datetime.now(timezone.utc)
    message = None
    
    if ctx:
        message = await ctx.send(loading)
    
    while not activity.is_set():
        
        if console:
            print(f"\r[{stime.strftime("%H:%M:%S")}–{ntime().strftime("%H:%M:%S")}] {loading}   ", end = "", flush = True)
        
        loading += "."
        
        await asyncio.sleep(1)
        
        if len(loading) >= 11:
            loading  = "Loading"
        
        if message:
            await message.edit(content = loading)

    if message:
        await message.delete()
    print(end = "\n")