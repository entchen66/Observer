from .observer import Observer


async def setup(bot):
    observer= Observer(bot)
    bot.add_cog(observer)
