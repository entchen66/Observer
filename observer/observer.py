import discord
from discord.ext.commands.converter import Greedy
from discord.ext.commands.cooldowns import BucketType
import asyncio
import random
import os
from io import BytesIO
import matplotlib.pyplot as plt
from redbot.core import commands
from someutils.skinNames import tranlationList
from redbot.core import checks, Config, commands
from redbot.core.utils.chat_formatting import pagify, escape
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.data_manager import bundled_data_path
import re
from datetime import datetime, timezone, timedelta
import pytz, numpy

import json

BaseCog = getattr(commands, "Cog", object)


class Observer(BaseCog):
    """A collection of stuff to help moderative work."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 5343796627)
        default_guild_settings = {
            'member_join': 0,
            'member_left': 0,
            'member_ban': 0,
            'last_reset': datetime.now(tz=timezone.utc).timestamp(),
            'channelListForLineFilter': [398972261094129665, 406952054649520148, 423590117941444618, 471683835814346763, 529500181415067658, 529500093959897098, 402477327902179328, 490969727343263745, 520342556815523855, 583373871143583748],
            'joinsLeftPerHour' : {},
            'nameFilterList' : ['use code', 'revert', '[epic]', '[eplc]'],
            'maxLineLenth': 7
        }
        default_member_settings = {
            'lastBRClanPost': 0,
            'lastRDWClanPost': 0,
            'beer': 0,
            'schildRewards': 0,
            'schildLefts': 5
        }
        default_channel_settings = {
            'sample': 0
        }
        self.settings.register_guild(**default_guild_settings)
        self.settings.register_member(**default_member_settings)
        self.settings.register_channel(**default_channel_settings)

    #Notfall Nachrichten log für die BR Clanverstärkung
#    @commands.Cog.listener()
#    async def on_raw_message_delete(self, payload):
#        if payload.channel_id == 458371700166230016:
#            channel = self.bot.get_guild(payload.guild_id).get_channel(577189299078823937)
#            if payload.cached_message is not None:
#                embed = discord.Embed(title=f'Es wurde eine Nachricht ({payload.message_id}) aus BR-Clanmeldung  gelöscht.', description=payload.cached_message.content, colour=discord.Colour(0x00FF00))
#                embed.add_field(name='Author:', value=payload.cached_message.author)
#            else:
#                embed = discord.Embed(title=f'Es wurde eine Nachricht in BR-Clanmeldung gelöscht, die nicht im Cache zu finden ist.', description='No Message', colour=discord.Colour(0xFF0000))
#                embed.add_field(name='Msg. ID:', value=payload.message_id)
#            await channel.send('', embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is not None and message.guild.id == 398567824471097345:
            if await self.bot.is_automod_immune(message.author): # Check if user is immune to bot actions. in >autoimmune list
                return
            #Check if Llama post something in #shop
            if message.channel.id == 539903064077893632:
                await message.delete()
                botbefehle = message.guild.get_channel(439829671320748032)
                return await botbefehle.send(f'<@&398893939593052171>\n{message.author} hat versucht etwas in #shop zu posten.\nSeine Nachricht war: ```{message.content}```')
            #Slowmode für die BR-Clanverstärkung
            elif message.channel.id == 458371700166230016:
                utcNow = datetime.now(tz=timezone.utc).timestamp()
                lastPost = await self.settings.member(message.author).lastBRClanPost()
                if utcNow - lastPost >= 86400:
                    await self.settings.member(message.author).lastBRClanPost.set(utcNow)
                    embed = discord.Embed(description=f'Vielen Dank für deine Clanwerbung. Beachte bitte, dass du die nächsten 24h keine weitere Clanwerbung posten darfst.', colour=discord.Colour(0x00FF00), timestamp=(datetime.now(tz=timezone.utc)))
                    embed.set_footer(text='Letzte Nachricht im Kanal:')
                    await message.author.send('', embed=embed)
                else:
                    await message.delete()
                    self.bot.dispatch("filter_message_delete", message, [f'**versuchte Clanwerbung nach {int((utcNow - lastPost)/60/6)/10} Stunden**'])
                    embed = discord.Embed(description=f'Bitte halte dich an die 24 Stunden Wartezeit. Bei öfterem Missachten dieser, können dir die Clanrechte entzogen werden.', colour=discord.Colour(0xFF0000))
                    return await message.author.send('', embed=embed)
            #Slowmode für die RDW-Clanverstärkung
            elif message.channel.id == 481544946986254336:
                utcNow = datetime.now(tz=timezone.utc).timestamp()
                lastPost = await self.settings.member(message.author).lastRDWClanPost()
                if utcNow - lastPost >= 86400:
                    await self.settings.member(message.author).lastRDWClanPost.set(utcNow)
                    embed = discord.Embed(description=f'Vielen Dank für deine Clanwerbung. Beachte bitte, dass du die nächsten 24h keine weitere Clanwerbung posten darfst.', colour=discord.Colour(0x00FF00), timestamp=(datetime.now(tz=timezone.utc)))
                    embed.set_footer(text='Letzte Nachricht im Kanal:')
                    await message.author.send('', embed=embed)
                else:
                    await message.delete()
                    self.bot.dispatch("filter_message_delete", message, [f'**versuchte Clanwerbung nach {int((utcNow - lastPost)/60/6)/10} Stunden**'])
                    embed = discord.Embed(description=f'Bitte halte dich an die 24 Stunden Wartezeit. Bei öfterem Missachten dieser, können dir die Clanrechte entzogen werden.', colour=discord.Colour(0xFF0000))
                    return await message.author.send('', embed=embed)
            #auto deletion for #fanart when No image is attached
            elif message.channel.id == 551869571775332392:
                if len(message.attachments) == 0:
                    await message.delete()
                    return self.bot.dispatch("filter_message_delete", message, [f'**Nachricht besaß keine Bilddatei.**'])
                else:
                    for file in message.attachments:
                        if not self.is_file_image(file.filename):
                            await message.delete()
                            self.bot.dispatch("filter_message_delete", message, [f'**Datei hatte kein Bildformat.** ({file.filename})'])
                            return
            #auto deletion for #fortnite-bilder when a file isn't an image format
            elif message.channel.id == 398952761439289364:
                if len(message.attachments) > 0:
                    for file in message.attachments:
                        if not self.is_file_image(file.filename):
                            await message.delete()
                            self.bot.dispatch("filter_message_delete", message, [f'**Datei hatte kein Bildformat.** ({file.filename})'])
                            return
            #auto delete messages wich are not a comment in kanalmanagement channel
            elif message.channel.id == 587269140767834123:
                if message.content.lower().startswith('>name'.lower()) or message.content.lower().startswith('>kick'.lower()) or message.content.lower().startswith('>size'.lower()) or message.content.lower().startswith('>invite'.lower()) or message.content.lower().startswith('>close'.lower()) or message.content.lower().startswith('>open'.lower()):
                    pass
                else:
                    await message.delete()
                    self.bot.dispatch("filter_message_delete", message, [f'**Normale Nachricht in <#587269140767834123>.**'])
                    return
            #auto deletion for #stream-promo and #video-promo if no embed exists
            elif message.channel.id == 400211671848583168 or message.channel.id == 400035060171931648:
                await asyncio.sleep(3)
                if not message.embeds:
                    try:
                        await message.delete()
                        self.bot.dispatch("filter_message_delete", message, [f'**Keine Link Vorschau enthalten.**'])
                        return
                    except:
                        return
            #Zeilenlimitierer für die Gruppensuchkanäle
            channelListLineFilter = await self.settings.guild(message.guild).channelListForLineFilter()
            if message.channel.id in channelListLineFilter:
                numNewLines = message.content.count('\n')
                maxLines = await self.settings.guild(message.guild).maxLineLenth()
                if numNewLines > maxLines:
                    await message.delete()
                    self.bot.dispatch("filter_message_delete", message, [f'**Versuchter Text mit {numNewLines + 1} Zeilen in den Gruppensuchkanälen**'])
                    embed = discord.Embed(description=f'Bitte fasse deine Gruppensuche kürzer, die Länge deines Beitrags beeinträchtigt die Übersicht der Gruppensuchkanäle.', colour=discord.Colour(0xFF0000))
                    return await message.author.send('', embed=embed)
                    
    def is_file_image(self, filename):
        imageExtension = [".png", ".jpg", ".jpeg", ".gif"]
        for ext in imageExtension:
            if filename.lower().endswith(ext):
                return True
        return False
                    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, member):
        memberBan = await self.settings.guild(guild).member_ban() + 1
        await self.settings.guild(guild).member_ban.set(memberBan)
        if guild.id == 398567824471097345 and isinstance(member, discord.Member):
            botbefehle = guild.get_channel(439829671320748032)
            brClanRole = guild.get_role(519648803603873793)
            rdwClanRole = guild.get_role(519649021527195648)
            if (brClanRole is None) or (rdwClanRole is None) or (botbefehle is None):
                pass
            elif (brClanRole in member.roles) or (rdwClanRole in member.roles):
                await botbefehle.send('Der User hatte den Clan Rang. Liste: <https://goo.gl/eoQSZP>')
                await botbefehle.send(member.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        nowHour = str(datetime.now(tz=pytz.timezone('Europe/Berlin')).hour)
        statsArray = await self.settings.guild(member.guild).joinsLeftPerHour()
        statsArray[nowHour] = [statsArray[nowHour][0] + 1, statsArray[nowHour][1]]
        memberJoin = await self.settings.guild(member.guild).member_join() + 1
        await self.settings.guild(member.guild).joinsLeftPerHour.set(statsArray)
        await self.settings.guild(member.guild).member_join.set(memberJoin)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        nowHour = str(datetime.now(tz=pytz.timezone('Europe/Berlin')).hour)
        statsArray = await self.settings.guild(member.guild).joinsLeftPerHour()
        statsArray[nowHour] = [statsArray[nowHour][0], statsArray[nowHour][1] + 1]
        memberLeft = await self.settings.guild(member.guild).member_left() + 1
        await self.settings.guild(member.guild).joinsLeftPerHour.set(statsArray)
        await self.settings.guild(member.guild).member_left.set(memberLeft)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.guild.id == 398567824471097345 and isinstance(after, discord.Member):
            if before.display_name != after.nick:
                if await self.bot.is_automod_immune(after):
                    return
                allowedChars = 'abcdefghijklmnopqrstuvwxyzäöü1234567890ßêéèâáàûúùîíìôóò^°´`\'#+*~-_.:,;<>@€|"§$%&/()=?\\}][{³²' #https://discordapp.com/channels/322850917248663552/464137944815501312/562763958512254987
                nameFilterList = await self.settings.guild(before.guild).nameFilterList()
                if len(after.display_name) < 3 or not (set(after.display_name.lower()[:3]) <= set(allowedChars)) or after.display_name.lower()[:5].count(after.display_name.lower()[:5][0]) == len(after.display_name.lower()[:5]) or any(f in after.display_name.lower() for f in nameFilterList):
                    nickname = random.choice(tranlationList)
                    try:
                        await after.edit(reason='Nicht regelkonformer Nickname.', nick=nickname)
                    except:
                        return
                    try:
                        embed = discord.Embed(title=f'Hallo {after}', description=f'Dein Nickname (__*{after.display_name}*__) entspricht nicht unseren Regeln. Wir haben diesen für dich automatisch geändert. Du kannst ihn jedoch jederzeit anpassen.', colour=0x00ffff, timestamp=datetime.now(tz=timezone.utc))
                        embed.set_author(name='Dies sind unsere Namensregeln:')
                        embed.add_field(name='**1:**', value='Nur Mitarbeiter von Epic Games dürfen [EPIC] in ihrem Spitznamen haben! Fügt das bitte nicht an euren Spitznamen an, außer, ihr wurdet als Mitarbeiter von Epic Games bestätigt.', inline=False)
                        embed.add_field(name='**2:**', value='Wir bitten euch außerdem darum, keine Spitznamen zu wählen, die den Rollen (wie z.B. „Moderator) ähneln, und euch nicht als technischen Support auszugeben.', inline=False)
                        embed.add_field(name='**3:**', value='Wählt einen Namen, der gut lesbar ist und leicht abgetippt werden kann, dazu gehört auch, dass die ersten drei Zeichen keine Leerzeichen enthalten dürfen.', inline=False)
                        embed.add_field(name='**4:**', value='Unsichtbare Namen sind nicht erlaubt.', inline=False)
                        embed.add_field(name='**5:**', value='Abgesehen von Emojis sollten keine Symbole verwendet werden.', inline=False)
                        embed.add_field(name='**6:**', value='Emojis dürfen nicht über eine normale Zeile hinausragen.', inline=False)
                        embed.add_field(name='**7:**', value='Namen sollten nicht kürzer als 3 alphanumerische Zeichen lang sein.', inline=False)
                        embed.add_field(name='**8:**', value='Leerzeichen zwischen einzelnen Zeichen sind zu vermeiden. (zum Beispiel: „B A S E Kyle“ ist nicht gestattet, aber „BASE Kyle“ wäre in Ordnung)', inline=False)
                        await after.send('', embed=embed)
                    except:
                        pass

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def clearclan(self, ctx, member: discord.Member):
        await self.settings.member(member).lastBRClanPost.set(0)
        await self.settings.member(member).lastRDWClanPost.set(0)
        await ctx.message.add_reaction('✅')

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def joinleft(self, ctx, reset: bool=False):
        """Listet die Anzahl an Membern, die den Server betreten/verlassen/gebannt wurden auf."""
        now = datetime.now(tz=timezone.utc)
        memberJoin = await self.settings.guild(ctx.guild).member_join()
        memberLeft = await self.settings.guild(ctx.guild).member_left()
        memberBan = await self.settings.guild(ctx.guild).member_ban()
        lastReset = await self.settings.guild(ctx.guild).last_reset()
        lastReset = datetime.fromtimestamp(lastReset, tz=timezone.utc)
        if reset:
            await self.settings.guild(ctx.guild).member_join.set(0)
            await self.settings.guild(ctx.guild).member_left.set(0)
            await self.settings.guild(ctx.guild).member_ban.set(0)
            await self.settings.guild(ctx.guild).last_reset.set(now.timestamp())
        td = now-lastReset
        await ctx.send(f'In den letzten {td.days*24+td.seconds//3600} Stunden und {(td.seconds//60)%60} Minuten haben:\n📈 - {memberJoin} Member den Server betreten.\n📉 - {memberLeft} Member den Server verlassen.\n🔨 - {memberBan} Member wurden davon gebannt.')

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def joinleftGraph(self, ctx, reset: bool=False):
        """Postet einen Graphen mit den join/left Statistiken von aktuellen Tag."""
        stundenDict = await self.settings.guild(ctx.guild).joinsLeftPerHour()
        stundenDict = {int(k): [int(v[0]), int(v[1])] for k, v in stundenDict.items()} #Transformiert Strings in Ints, die durchs laden der json confing enstehen
        w = 0.33
        #erstellen vom Graphen
        plt.clf() #setzt aktuellen Graphen zurück
        lists = sorted(stundenDict.items())
        x, part = zip(*lists)
        joins, lefts = zip(*part)
        meanJoins = numpy.mean(joins)
        meanLefts = numpy.mean(lefts)
        x1 = []
        x2 = []
        for i in x:
            x1.append(i-w/2)
            x2.append(i+w/2)
        fig = plt.figure(figsize=(12, 5))
        ax = fig.add_subplot(111)
        ax.grid(b=True, which='both', axis='y', linestyle='dashed', linewidth=0.75)
        ax.set_axisbelow(True)
        ax.bar(x1, joins, w, edgecolor='#82e9de', color='#00695c', label=f"joins\nmax: {max(joins)}", lw=0)
        ax.bar(x2, lefts, w, edgecolor='#ffa4a2', color='#c62828', label=f"lefts\nmax: {max(lefts)}", lw=0)
        ax.plot(x, [meanJoins] * len(x), '--', color='#82e9de', label=f'joins Schnitt\ntotal: {sum(joins)}')
        ax.plot(x, [meanLefts] * len(x), '--', color='#ffa4a2', label=f'lefts Schnitt\ntotal: {sum(lefts)}')
        ax.set_xticks(x)
        ax.legend(bbox_to_anchor=(1, 1), loc='upper left')
        # translation Dics for Day and Month
        date = datetime.utcnow()
        weekDict = {'MONDAY': 'MONDAY', 'TUESDAY': 'DIENSTAG', 'WEDNESDAY': 'MITTWOCH', 'THURSDAY': 'DONNERSTAG', 'FRIDAY': 'FREITAG', 'SATURDAY': 'SAMSTAG', 'SUNDAY': 'SONNTAG'}
        monthDict = {'JANUARY': 'JANUAR', 'FEBRUARY': 'FEBRUAR', 'MARCH': 'MÄRZ', 'APRIL': 'APRIL', 'MAY': 'MAI', 'JUNE': 'JUNI', 'JULY': 'JULI', 'AUGUST': 'AUGUST', 'SEPTEMBER': 'SEPTEMBER', 'OCTOBER': 'OKTOBER',
                     'NOVEMBER': 'NOVEMBER', 'DECEMBER': 'DEZEMBER'}
        weekDay = date.strftime("%A").upper()
        monthName = date.strftime("%B").upper()
        if weekDay in weekDict and monthName in monthDict:
            text = '' + date.strftime(f"{weekDict[weekDay].capitalize()} - %d. {monthDict[monthName].capitalize()} %Y")
        else:
            text = '' + date.strftime("%A - %d. %B %Y")
        plt.title(text, loc='center')

        image_object = BytesIO()
        plt.savefig(image_object, format='PNG', bbox_inches='tight')
        image_object.seek(0)
        await ctx.send(file=discord.File(image_object, 'chart.png'))
        if reset:
            for i in range(0, 24):
                stundenDict[str(i)] = [0, 0]
            await self.settings.guild(ctx.guild).joinsLeftPerHour.set(stundenDict)
       


    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def namelist(self, ctx, *, param: str):
        """sucht nach einem bestimmten angegebenen Nick"""
        counter = 0
        names = ''
        nameList = []
        for member in ctx.guild.members:
            if param.lower() in member.display_name.lower() and not (member.guild.get_role(398851874037432321) in member.roles):
                if counter != 0:
                    names = names + ', '
                names = names + '[\'{0}\', {1}]'.format(member.display_name, member.id)
                counter += 1
                if counter > 30:
                    nameList.append(names)
                    names = ''
                    counter = 0
        if len(nameList) != 0 and len(names) != 0:
            nameList.append(names)
            names = ''
        if counter == 0 and len(names) == 0 and len(nameList) == 0:
            await ctx.send('Keine Namen gefunden. <:fnpeng:458611773189128192>')
        elif len(nameList) == 0:
            await ctx.send('```py\n' + names + '```')
        else:
            for idx in range(len(nameList)):
                nameList[idx] = '{1}/{2}```py\n{0}```'.format(nameList[idx], idx + 1, len(nameList))
            await menu(ctx, nameList, DEFAULT_CONTROLS)

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def accountsearch(self, ctx, *, param: str):
        """sucht nach einem bestimmten angegebenen Namen und gibt diesen als @mention aus."""
        counter = 0
        names = ''
        nameList = []
        for member in ctx.guild.members:
            if param.lower() in str(member).lower():
                if counter != 0:
                    names = names + ', '
                names = names + '[\'{0}\', {1}]'.format(str(member), member.id)
                counter += 1
                if counter > 30:
                    nameList.append(names)
                    names = ''
                    counter = 0
        if len(nameList) != 0 and len(names) != 0:
            nameList.append(names)
            names = ''
        if counter == 0 and len(names) == 0 and len(nameList) == 0:
            await ctx.send('Keine Namen gefunden. <:fnpeng:458611773189128192>')
        elif len(nameList) == 0:
            await ctx.send('```py\n' + names + '```')
        else:
            for idx in range(len(nameList)):
                nameList[idx] = '{1}/{2}```py\n{0}```'.format(nameList[idx], idx+1, len(nameList))
            await menu(ctx, nameList, DEFAULT_CONTROLS)

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def namefile(self, ctx, *, param: str):
        """sucht nach Nick und gibt sie in einer Liste als Datei aus."""
        counter = 0
        path = str(bundled_data_path(self)) + '/tempNames.txt'
        memberFile = open(path, 'w')
        for member in ctx.guild.members:
            if param.lower() in member.display_name.lower() and not (member.guild.get_role(398851874037432321) in member.roles):
                member = '\'{0}\' - {1}\n'.format(member.display_name, member.id)
                memberFile.write(member)
                counter += 1
        memberFile.close()
        if counter == 0:
            await ctx.send('Keine Namen gefunden. <:fnpeng:458611773189128192>')
        else:
            await ctx.send('Es wurden {0} Namen gefunden.'.format(counter), file=discord.File(path, 'names.txt'))
        os.remove(path)

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def namecheck(self, ctx):
        """Vergleicht Nicks mit bestimmten bedingungen."""
        counter = 0
        allowedChars = 'abcdefghijklmnopqrstuvwxyzäöü1234567890ßêéèâáàûúùîíìôóò^°´`\'#+*~-_.:,;<>@€|"§$%&/()=?\\}][{³²'
        nameFilterList = await self.settings.guild(ctx.guild).nameFilterList()
        path = str(bundled_data_path(self)) + '/tempNames.txt'
        memberFile = open(path, 'w')
        for member in ctx.guild.members:
            if len(member.display_name.lower()) < 3 or not (set(member.display_name.lower()[:3]) <= set(allowedChars)) or member.display_name.lower()[:5].count(member.display_name.lower()[:5][0]) == len(member.display_name.lower()[:5]) or any(f in member.display_name.lower() for f in nameFilterList):
                member = '\'{0}\' - {1}\n'.format(member.display_name, member.id)
                memberFile.write(member)
                counter += 1
        memberFile.close()
        if counter == 0:
            await ctx.send('Keine Namen gefunden. <:fnpeng:458611773189128192>')
        else:
            await ctx.send('Es wurden {0} Namen gefunden.'.format(counter), file=discord.File(path, 'names.txt'))
        os.remove(path)

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def namefix(self, ctx):
        """Kann benutzt werden, wenn [p]namecheck Namen findet. Dies passiert wenn der Bot mal offline ist, wenn ein Member sich umbennen."""
        counter = 0
        members = []
        allowedChars = 'abcdefghijklmnopqrstuvwxyzäöü1234567890ßêéèâáàûúùîíìôóò^°´`\'#+*~-_.:,;<>@€|"§$%&/()=?\\}][{³²'
        nameFilterList = await self.settings.guild(ctx.guild).nameFilterList()
        for member in ctx.guild.members:
            if len(member.display_name.lower()) < 3 or not (set(member.display_name.lower()[:3]) <= set(allowedChars)) or member.display_name.lower()[:5].count(member.display_name.lower()[:5][0]) == len(member.display_name.lower()[:5]) or any(f in member.display_name.lower() for f in nameFilterList):
                members.append(member)
                counter += 1
        imputMessage = await ctx.send(f'Es wurden 0/{counter} Namen umbennant.')
        counter2 = 0
        error = 0
        for i in members:
            nickname = random.choice(tranlationList)
            try:
                name = i.display_name
                await i.edit(reason='Nicht regelkonformer Nickname.', nick=nickname)
                embed = discord.Embed(title=f'Hallo {i}', description=f'Dein Nickname (__*{name}*__) entspricht nicht unseren Regeln. Wir haben diesen für dich automatisch geändert. Du kannst ihn jedoch jederzeit anpassen.', color=0x00ffff, timestamp=datetime.now(tz=timezone.utc))
                embed.set_author(name='Dies sind unsere Namensregeln:')
                embed.add_field(name='**1:**', value='Nur Mitarbeiter von Epic Games dürfen [EPIC] in ihrem Spitznamen haben! Fügt das bitte nicht an euren Spitznamen an, außer, ihr wurdet als Mitarbeiter von Epic Games bestätigt.', inline=False)
                embed.add_field(name='**2:**', value='Wir bitten euch außerdem darum, keine Spitznamen zu wählen, die den Rollen (wie z.B. „Moderator) ähneln, und euch nicht als technischen Support auszugeben.', inline=False)
                embed.add_field(name='**3:**', value='Wählt einen Namen, der gut lesbar ist und leicht abgetippt werden kann, dazu gehört auch, dass die ersten drei Zeichen keine Leerzeichen enthalten dürfen.', inline=False)
                embed.add_field(name='**4:**', value='Unsichtbare Namen sind nicht erlaubt.', inline=False)
                embed.add_field(name='**5:**', value='Abgesehen von Emojis sollten keine Symbole verwendet werden.', inline=False)
                embed.add_field(name='**6:**', value='Emojis dürfen nicht über eine normale Zeile hinausragen.', inline=False)
                embed.add_field(name='**7:**', value='Namen sollten nicht kürzer als 3 alphanumerische Zeichen lang sein.', inline=False)
                embed.add_field(name='**8:**', value='Leerzeichen zwischen einzelnen Zeichen sind zu vermeiden. (zum Beispiel: „B A S E Kyle“ ist nicht gestattet, aber „BASE Kyle“ wäre in Ordnung)', inline=False)
                await i.send('', embed=embed)
            except:
                error += 1
                pass
            counter2 += 1
            await imputMessage.edit(content=f'Es wurden {counter2}/{counter} Namen umbennant. Fehler: {error}.')
        await imputMessage.add_reaction('🍌')

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def nameFilterAdd(self, ctx, *, word):
        """Fügt ein Wort dem Namen-Filter hinzu."""
        word = word.lower()
        nameFilterList = await self.settings.guild(ctx.guild).nameFilterList()
        if word not in nameFilterList:
            nameFilterList.append(word)
            await self.settings.guild(ctx.guild).nameFilterList.set(nameFilterList)
            await ctx.send("Wort erfolgreich hinzugefügt.")
        else:
            await ctx.send("Das Wort ist bereits im Filter.")

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def nameFilterRemove(self, ctx, *, word):
        """Löscht ein Wort aus dem Namenfilter."""
        word = word.lower()
        nameFilterList = await self.settings.guild(ctx.guild).nameFilterList()
        if word in nameFilterList:
            nameFilterList.remove(word)
            await self.settings.guild(ctx.guild).nameFilterList.set(nameFilterList)
            await ctx.send("Wort erfolgreich gelöscht.")
        else:
            await ctx.send("Das Wort wurde nicht im Filter gefunden.")

    @checks.mod_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def nameFilterList(self, ctx):
        """Zeigt die Namen-Filter liste an."""
        nameFilterList = await self.settings.guild(ctx.guild).nameFilterList()
        if len(nameFilterList) > 0:
            await ctx.send(f"```{str(nameFilterList)}```")
        else:
            await ctx.send("Keine Einträge gefunden.")

    @commands.command(usage='<channel> <1=Vorgestellt/2=The Block/3=Empfohlen> <Inselcode> <"Name der Insel"> <Beschreibung der Insel>  *Bild im Anhang')
    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    async def postisland(self, ctx, channel: discord.TextChannel, type: int, islandcode, name, *, description):
        """Postet eine Insel mit einem festen Layout in den angegebenen Kanal."""
        if len(ctx.message.attachments) == 1:
            image = ctx.message.attachments[0].url
        else:
            embed = discord.Embed(description=f'Du hast kein Bild angehangen. Bitte hänge der Nachricht ein Bild an.', colour=discord.Colour(0x4B9443))
            return await ctx.send('', embed=embed)
        if type == 1:
            headding = "Vorgestellt"
            thumb = 'https://cdn.discordapp.com/attachments/558215081494708234/561261572597612547/fnchq-logo-large.png'
        elif type == 2:
            headding = "The Block"
            thumb = 'https://media.discordapp.net/attachments/558215081494708234/565622642242224188/theblock.png'
        elif type == 3:
            headding = "Empfohlen"
            thumb = 'https://cdn.discordapp.com/attachments/558215081494708234/565624628157087755/approved.png'
        else:
            embed = discord.Embed(description=f'Leg nach dem Kanal bitte fest, um welchen Typ von posting es sich handelt.\n**1 - Vorgestellt\n2 - The Block\n3 - Empfohlen**', colour=discord.Colour(0x4B9443))
            return await ctx.send('', embed=embed)
        if len(islandcode) != 14:
            if len(islandcode) == 12:
                islandcode = f'{islandcode[:4]}-{islandcode[4:8]}-{islandcode[8:12]}'
            else:
                embed = discord.Embed(description=f'Dies sieht nicht nach einem gültigen Inselcode aus: {islandcode}.', colour=discord.Colour(0x4B9443))
                return await ctx.send('', embed=embed)

        embed = discord.Embed(colour=discord.Colour(0x01E58E), title=f'{headding}:', description=f'**__{name}__**\n{description}\n\n**[Zu meiner Liste hinzufügen](https://epicgames.com/fn/{islandcode})**', timestamp=datetime.now(tz=timezone.utc))
        embed.set_image(url=image)
        embed.set_thumbnail(url=thumb)
        embed.add_field(name='Code:', value=f'**__{islandcode}__**', inline=False)
        embed.set_footer(text='#FortniteCreative', icon_url='https://cdn.discordapp.com/emojis/546801256115732480.png')
        await channel.send(content="", embed=embed)
        await ctx.message.add_reaction('✅')

    @commands.command(usage='<Hier beliebe Person eintragen>')  #Funcommand - Viel Spaß!
    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    async def bier(self, ctx, member: discord.Member = None, count = 1):
        author = ctx.message.author
        if member is None or member is author:
            bier = await self.settings.member(author).beer()
            embed = discord.Embed(description=f'Bisher hast du **{bier}** 🍺 getrunken.', colour=discord.Colour(0xFFD700))
            embed.set_author(name=f'Leider hast du kein Bier daheim, geh dir welches kaufen 🛒', icon_url=author.avatar_url)
            await ctx.send('', embed=embed)
        else:
            if count <= 0:
                await ctx.send('Nö!')
            elif count > 5:
                embed = discord.Embed(description=f'{author.display_name} versucht dir **{count}** 🍺 zu gegeben.\nLeider kann er so viel nicht tragen.\n\nNun hat er **{count}** 🍺 verschüttet und du bekommst **0** dazu.', colour=discord.Colour(0xFFD700))
                embed.set_author(name=f'{author.display_name} muss wischen! 🧹', icon_url=member.avatar_url)
                embed.set_footer(text='Pech!', icon_url=author.avatar_url)
                await ctx.send('', embed=embed)
            else:
                bier = await self.settings.member(member).beer()
                await self.settings.member(member).beer.set(count + bier)
                embed = discord.Embed(description=f'{author.display_name} hat dir **{count}** 🍺 gegeben.\nTrink aus! Prost 🍻.\n\nNun hast du **{count + bier}** 🍺 getrunken.', colour=discord.Colour(0xFFD700))
                embed.set_author(name=f'{member.display_name} muss trinken!', icon_url = member.avatar_url)
                embed.set_footer(text='Wohlbekomms!', icon_url=author.avatar_url)
                await ctx.send('', embed=embed)

    @commands.command()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    async def bierscore(self, ctx):
        bierListe = {}
        beer = await self.settings.all_members(ctx.guild)
        for i in beer:
            if 'beer' in beer[i] and beer[i]['beer'] > 0:
                bierListe[i] = beer[i]['beer']
        noUserTemp = []
        for i in bierListe:
            if ctx.guild.get_member(i) is None:
                noUserTemp.append(i)
        for i in noUserTemp:
            bierListe.pop(i)
        sortedBeer = sorted(bierListe.items(), key=lambda kv: kv[1])
        sortedBeer.reverse()
        bierListe = []
        while len(sortedBeer) > 0:
            bierListe.append(sortedBeer[:10])
            sortedBeer = sortedBeer[10:]
        for idx in range(len(bierListe)): #embed bauen!
            #bierListe[idx] = '{1}/{2}```py\n{0}```'.format('\n'.join(i for i in bierListe[idx]), idx + 1, len(bierListe))
            embed = discord.Embed(title=f'{idx+1}/{len(bierListe)}', description='Bierscore', colour=discord.Colour(0xFFD700))
            for i in bierListe[idx]:
                embed.add_field(name=ctx.guild.get_member(i[0]).display_name, value=f'{i[1]} 🍺', inline=True)
            bierListe[idx] = embed
        await menu(ctx, bierListe, DEFAULT_CONTROLS)
