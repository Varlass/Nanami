from discord.ext.commands import Context
from discord import Interaction


class Unifer:
    __slots__ = ("source",
                 "user",
                 "message",
                 "channel",
                 "guild")

    def __init__(self, source: Context|Interaction):
        self.source = source

        self.user = getattr(source, "author", None) or getattr(source, "user", None)
        self.message = getattr(source, "message", None)
        self.channel = getattr(source, "channel", None)
        self.guild = getattr(source, "guild", None)


    @property
    def user_id(self) -> int|None:
        return getattr(self.user, "id", None)

    @property
    def roles_id(self) -> set[int]:
        if hasattr(self.user, "roles") and self.user.roles:
            return {role.id for role in self.user.roles}
        
        else:
            return set()

    @property
    def channel_id(self) -> int|None:
        return getattr(self.channel, "id", None)

    @property
    def guild_id(self) -> int|None:
        return getattr(self.guild, "id", None) if self.guild else getattr(self.source, "guild_id", None)