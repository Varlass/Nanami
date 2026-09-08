import discord, os, yaml
from discord.ext import commands

from utils.unifer import Unifer


white_list_yaml = os.path.join(os.path.dirname(__file__), "white_list.yaml") # Список id из white_list.yaml.
with open(white_list_yaml, encoding = "utf-8") as wlist:
    check_list = yaml.safe_load(wlist)

white_list = ({check_list["Members"][value] for value in ("_varlass_", "kaguyapet")}| # Белый список id.
              {check_list["Roles"][value] for value in ("SF3_Leader", "SFA_Leader")})


def check(checks: set[int] = set(), *, bypass: bool = True): # Декоратор проверки id.
    if not isinstance(checks, set):
        raise TypeError("Цель проверки должна быть множеством.")
    
    effective_checks = checks|white_list if bypass else checks

    async def predicate(source: commands.Context|discord.Interaction) -> bool:
        context = Unifer(source)

        ids = {context.user_id,
               *context.roles_id,
               context.channel_id,
               context.guild_id}
        
        ids.discard(None)

        if ids & effective_checks:
            return True

        raise commands.CheckFailure()

    return commands.check(predicate)