# for discord
import nextcord
from nextcord.ext import commands
from settings import settings
from nextcord.ext import tasks
from nextcord.utils import get

# for logs
import asyncio
from time import time
from datetime import datetime

# data base
import database.stat as stat
import database.serversettings as serversetting

connected = False
session = None
uri = settings["StatUri"]

# for card
from card.stat import *
import unicodedata

# for multipage embed
from nextcord_paginator import paginator as Paginator

# for cards
from settings import banners  # name of cards
from settings import colors  # name of colors from Pillow


def massive_split(mas):
    masx = []
    l10 = len(mas) // 10
    for i in range(l10 + 1):
        masx.append(mas[i * 10 : (i + 1) * 10])
    return masx


@tasks.loop(seconds=60)  # repeat after every 60 seconds
async def reconnect():
    global session
    global connected

    connected = False
    session = stat.connectToDatabase(uri, session)
    connected = True


class Stats(commands.Cog, name="Статистика"):
    """Статистика пользователей сервера"""

    COG_EMOJI = "📓"

    def __init__(self, bot):
        self.bot = bot
        reconnect.start()

    @commands.command(pass_context=True, brief="Статистика пользователя")
    @commands.guild_only()
    async def ранг(self, ctx, *пользователь):
        global session
        global connected

        usr = пользователь

        # check user input
        if usr == ():
            user = ctx.author
        else:
            usr = usr[0]
            if usr.startswith("<"):
                usr = usr[3:-1]
            try:
                user = await ctx.guild.fetch_member(usr)
                pass
            except:
                await ctx.send("Неверный ввод!")

        # if not connected to database
        if connected != True:
            await asyncio.sleep(1)

        x = stat.getInfo(session, ctx.guild.id, user.id)

        statcard = newstat()

        if user.avatar != None:
            statcard.avatar = user.avatar.url
        else:
            statcard.avatar = f"https://cdn.discordapp.com/embed/avatars/{str(int(user.discriminator)%5)}.png"

        statcard.name = unicodedata.normalize("NFKC", str(user.display_name))

        statcard.color = x.color

        statcard.path = x.background

        statcard.coin = x.coin

        statcard.quote = x.quotex

        if x.allvoicetime == None:
            statcard.voicetime = 0
        else:
            statcard.voicetime = x.allvoicetime

        if x.cookie == None:
            statcard.cookie = 0
        else:
            statcard.cookie = x.cookie

        if x.xp == None:
            statcard.xp = 0
        else:
            statcard.xp = x.xp

        if x.lvl == None:
            statcard.lvl = 0
        else:
            statcard.lvl = x.lvl

        # sending image to discord channel
        await ctx.send(file=await statcard.create())

    @commands.command(brief="Топ пользователей сервера")
    @commands.guild_only()
    async def лидеры(self, ctx):
        global session

        peoples = massive_split(list(stat.getAllInfoSorted(session, ctx.guild.id)))
        s = 0
        embs = []
        for people_list in peoples:
            emb = nextcord.Embed(title=f"Топ пользователей | {ctx.guild.name}")
            emb.color = nextcord.Colour.green()
            emb.set_thumbnail(url=ctx.guild.icon.url)

            for idx, items in enumerate(people_list):
                strx = ""
                if items.lvl != None:
                    strx = f"**Уровень:** {items.lvl}|"
                else:
                    strx = f"**Уровень:** 0|"

                if items.xp != None:
                    strx = strx + f"**Опыт:** {items.xp}|"
                else:
                    strx = strx + f"**Опыт:** 0|"

                if items.cookie != None:
                    if items.cookie != 0:
                        strx = strx + f":cookie: {items.cookie}|"

                if items.coin != None:
                    if items.coin != 0:
                        strx = strx + f":coin: {items.coin}|"

                if items.allvoicetime != None:
                    if items.allvoicetime != 0:
                        hours = items.allvoicetime // 3600
                        minutes = (items.allvoicetime % 3600) // 60
                        if minutes < 10:
                            minutes = "0" + str(minutes)
                        seconds = (items.allvoicetime % 3600) % 60
                        if seconds < 10:
                            seconds = "0" + str(seconds)

                        strx = strx + f":microphone: {hours}:{minutes}:{seconds}"

                member = get(ctx.guild.members, id=items.uid)
                if member != None:
                    name = get(ctx.guild.members, id=items.uid).display_name
                else:
                    name = "Пользователь покинул сервер"

                emb.add_field(
                    name=f"{s*10 + idx + 1}. {name}",
                    value=strx,
                    inline=False,
                )

            embs.append(emb)
            s += 1

        try:
            await ctx.message.delete()
            pass
        except nextcord.errors.Forbidden:
            pass

        message = await ctx.send(embed=embs[0])

        page = Paginator(
            message,
            embs,
            ctx.author,
            self.bot,
            footerpage=True,
            footerdatetime=False,
            footerboticon=True,
        )
        try:
            await page.start()
        except nextcord.errors.NotFound:
            pass

    @commands.command(pass_context=True, brief="Выбор цвета для статистики")
    @commands.guild_only()
    async def цвет(self, ctx, *цвет):
        global session
        global connected
        global colors

        args = цвет

        # if user input blank > send colors magazine
        if args == ():
            embs = []

            for i in range(1, 5):
                emb = nextcord.Embed(title=f"Варианты цветов")
                emb.color = nextcord.Colour.random()
                emb.set_image(
                    url=f"https://raw.githubusercontent.com/I-dan-mi-I/images/main/color/{i}.png"
                )
                embs.append(emb)

            try:
                await ctx.message.delete()
                pass
            except nextcord.errors.Forbidden:
                pass

            message = await ctx.send(embed=embs[0], delete_after=60)

            page = Paginator(
                message,
                embs,
                ctx.author,
                self.bot,
                footerpage=True,
                footerdatetime=False,
                footerboticon=True,
            )
            try:
                await page.start()
            except nextcord.errors.NotFound:
                pass

        # else set color to database
        else:
            e = (" ").join(args).lower()
            if e in colors:

                # if not connected to database
                if not connected:
                    await asyncio.sleep(1)

                stat.setColor(session, ctx.guild.id, ctx.author.id, e)
                await ctx.send(f"{ctx.author.mention} успешно заменено!")
            else:
                await ctx.send(
                    f"{ctx.author.mention} такого цвета нет в списке! Попробуйте снова"
                )

    @commands.command(pass_context=True, brief="Выбор фона для статистики")
    @commands.guild_only()
    async def фон(self, ctx, *фон):
        global session
        global connected
        global banners

        args = фон

        # if user input blank > send banners magazine
        if args == ():
            embs = []

            for i in range(1, 15):
                emb = nextcord.Embed(title=f"Варианты фонов")
                emb.color = nextcord.Colour.random()
                emb.set_image(
                    url=f"https://raw.githubusercontent.com/I-dan-mi-I/images/main/list/{i}.png"
                )
                embs.append(emb)

            try:
                await ctx.message.delete()
                pass
            except nextcord.errors.Forbidden:
                pass

            message = await ctx.send(embed=embs[0], delete_after=60)

            page = Paginator(
                message,
                embs,
                ctx.author,
                self.bot,
                footerpage=True,
                footerdatetime=False,
                footerboticon=True,
            )
            try:
                await page.start()
            except nextcord.errors.NotFound:
                pass

        # else set banner to database
        else:
            e = (" ").join(args).lower()
            if e in banners:
                e = f"https://raw.githubusercontent.com/I-dan-mi-I/images/main/cards/{e}.png"

                # if not connected to database
                if connected != True:
                    await asyncio.sleep(1)

                stat.setBackground(session, ctx.guild.id, ctx.author.id, e)
                await ctx.send(f"{ctx.author.mention} успешно заменено!")
            else:
                await ctx.send(
                    f"{ctx.author.mention} такого баннера нет в списке! Попробуйте снова"
                )

    @commands.command(
        pass_context=True,
        aliases=[f"coin"],
        brief="Редактирование количества монет пользователя",
    )
    async def шар(self, ctx, *количество):
        global session
        global connected

        args = количество

        if args == ():
            await ctx.send(
                f"{ctx.author.mention}, укажите uid (отметьте пользователя) и кол-во шаров, которые вы ему добавите!"
            )
        else:
            usr = args[0]
            if usr.startswith("<"):
                usr = usr[3:-1]

            if connected != True:
                await asyncio.sleep(1)

            try:
                user = await self.bot.fetch_user(usr)
                pass
            except:
                await ctx.send("Неверный ввод UID!")

            try:
                ball = int(args[1])
                pass
            except:
                await ctx.send("Неверный ввод числа шаров!")

            stat.addBalls(session, ctx.guild.id, user.id, ball)
            await ctx.send(f"{ctx.author.mention}, добавлено!")

    @commands.command(pass_context=True, brief="Установка цитаты для статистики")
    @commands.guild_only()
    async def цитата(self, ctx, *цитата):
        global session
        global connected

        args = цитатаы

        if args == ():
            await ctx.send(
                f"{ctx.author.mention}, напишите цитату после команды. Максимальная длина: 33 символа, включая пробелы."
            )
        else:
            e = (" ").join(args)
            if len(e) <= 33:
                if not connected:
                    await asyncio.sleep(1)

                stat.setQuote(session, ctx.guild.id, ctx.author.id, e)
                await ctx.send(f"{ctx.author.mention}, успешно заменено!")
            else:
                await ctx.send(
                    f"{ctx.author.mention}, Максимальная длина: 33 символа, включая пробелы! Попробуйте снова"
                )


def setup(bot):
    bot.add_cog(Stats(bot))
