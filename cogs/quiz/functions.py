import nextcord
import datetime

from nextcord.ext.commands import Context
from nextcord.ext import commands

from .ui import QuizSelector, QuizQuestionStarter, QuizQuestion, GiveAward
from checkers import check_editor_permission

from dataclasses import dataclass


@dataclass
class QuizMember:
    name: str
    points: int


class Quiz(nextcord.ext.commands.Cog, name="Викторины"):
    """Организация викторин. Quiz Creator - <https://clck.ru/py75f>"""

    COG_EMOJI = "🎲"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_content=True, brief="Запуск викторины")
    @commands.check(check_editor_permission)
    @commands.guild_only()
    async def викторина(self, ctx):
        view = QuizSelector(ctx.author)

        message = await ctx.send(view=view)
        await view.wait()

        try:
            view.response
        except:
            await message.edit("Старт отменён", view=None)
            return

        if not view.response["status"]:
            await message.edit("Старт отменён", view=None)
            return
        else:
            await message.edit("Подготовка вопросов", view=None)

            root = view.response["data"]
            questions = []
            for field in root.findall("question"):
                if field.find("text") is not None:
                    questions.append(field)

            if len(questions) == 0:
                return await message.edit("Ошибка чтения файла")

            await self.manual_quiz_process(ctx, questions, root)

    async def manual_quiz_process(self, ctx: Context, questions: list, root):
        quiz_members = {}

        starter_view = QuizQuestionStarter(ctx.author)
        await ctx.send(f"Количество вопросов: {len(questions)}\nВедущий: {ctx.author}", view=starter_view)

        await starter_view.wait()

        for number, question in enumerate(questions):
            embed: nextcord.Embed = nextcord.Embed(
                timestamp=datetime.datetime.now(),
                title=f"Вопрос №{number+1}/{len(questions)}",
                description=question.find("text").text,
                colour=nextcord.Colour.random(),
            )

            if question.find("img") is not None:
                embed.set_image(url=question.find("img").text)

            if ctx.author.avatar:
                embed.set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.avatar.url
                )
            else:
                embed.set_author(
                    name=ctx.author.display_name,
                    icon_url=f"https://cdn.discordapp.com/embed/avatars/{int(ctx.author.discriminator) % 5}.png",
                )

            quiz_view = QuizQuestion(
                ctx.author, starter_view.author_interaction, question
            )

            message = await ctx.send(embed=embed, view=quiz_view)

            await quiz_view.wait()

            await message.edit(view=None)

            embed: nextcord.Embed = nextcord.Embed(
                title="Ответы пользователей в порядке фиксации",
                colour=nextcord.Colour.brand_green(),
                description="",
            )

            for pos in range(len(quiz_view.answers.values())):
                embed.description += (
                        f"{pos+1}. **{list(quiz_view.answers.keys())[pos]}** - {list(quiz_view.answers.values())[pos]}"
                        + "\n"
                )

            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            await ctx.send(embed=embed)

            for user in list(quiz_view.answers.keys()):
                if user not in list(quiz_members.keys()):
                    quiz_members[user] = QuizMember(name=user, points=0)

            if list(quiz_view.answers.values()):
                await ctx.send("Пожалуйста, подождите окончания выдачи баллов")

                award_view = GiveAward(quiz_members, quiz_view.answers, ctx)

                await starter_view.author_interaction.followup.send(
                    view=award_view, ephemeral=True
                )
                await award_view.wait()
        embed: nextcord.Embed = nextcord.Embed(
            title="Результаты викторины",
            colour=nextcord.Colour.brand_green(),
            description="",
        )

        quiz_members_list = list(quiz_members.values())
        quiz_members_list.sort(key=lambda member: member.points, reverse=True)

        quiz_members_points = list({member.points for member in quiz_members_list})
        quiz_members_points.sort(reverse=True)

        quiz_winner_points = -1
        quiz_prize_i_points = -1
        quiz_prize_ii_points = -1

        try:
            quiz_winner_points = quiz_members_points[0]
            quiz_prize_i_points = quiz_members_points[1]
            quiz_prize_ii_points = quiz_members_points[2]
        except:
            pass

        for pos, member in enumerate(quiz_members_list):
            embed.description += (
                f"{pos+1}. **{member.name}** - {member.points}"
                + (" Победитель" if member.points == quiz_winner_points and member.points != 0 else "")
                + (" Призёр I" if member.points == quiz_prize_i_points and member.points != 0 else "")
                + (" Призёр II" if member.points == quiz_prize_ii_points and member.points != 0 else "")
                + "\n"
            )

        embed.set_footer(text="Спасибо всем участникам!")

        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Quiz(bot))
