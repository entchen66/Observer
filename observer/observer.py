import discord
from redbot.core import commands

BaseCog = getattr(commands, "Cog", object)


class Observer(BaseCog):
    """A collection of stuff to help moderative work."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.guild.id == 357574333645717505 and isinstance(after, discord.Member):
            if before.roles != after.roles:
                channel = before.guild.get_channel(577395014988988436)
                await channel.send('Test')
