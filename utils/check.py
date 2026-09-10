from discord import Interaction
from discord.ext.commands import Context, CheckFailure, check as ch
from yaml import safe_load

from data.app.manager import DIR
from utils.unifer import Unifer


with open(DIR/"id_list.yaml", encoding = "utf-8") as file:  # Список id из white_list.yaml.
    check_list = safe_load(file)

try:
    white_list = {check_list[category][name] for category, names in check_list["White_List"].items() for name in names if name}

except KeyError:
    white_list = {}


def check(checks: set[int] = set(), *, bypass: bool = True): # Декоратор проверки id.
    if not isinstance(checks, set):
        raise TypeError("Цель проверки должна быть множеством.")
    
    effective_checks = checks|white_list if bypass else checks

    async def predicate(source: Context|Interaction) -> bool:
        context = Unifer(source)

        ids = {context.user_id,
               *context.roles_id,
               context.channel_id,
               context.guild_id}
        
        ids.discard(None)

        if ids & effective_checks:
            return True

        raise CheckFailure()

    return ch(predicate)