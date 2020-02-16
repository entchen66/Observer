import discord
from redbot.core import commands, Config

BaseCog = getattr(commands, "Cog", object)


class Observer(BaseCog):
    """A collection of stuff to help moderative work."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 34926752)
        default_guild_settings = {
            'activated': []
        }
        self.settings.register_guild(**default_guild_settings)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = before.guild
        if guild.id == 357574333645717505 and isinstance(after, discord.Member):
            acticatedList = await self.settings.guild(guild).activated()
            if before.roles != after.roles and before.id not in acticatedList:
                channel = guild.get_channel(577395014988988436)
                role = guild.get_role(425357864417099776)
                if role not in before.roles and role in after.roles:
                    await channel.send(f'Glückwunsch Agent {before.mention}, du wurdest aktiviert.')
                    acticatedList.append(before.id)
                    await self.settings.guild(guild).activated.set(acticatedList)
