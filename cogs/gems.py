from discord.ext import commands
import discord
import json
import time
from log import setupLogging


class LeaderboardEmbed(discord.Embed):
    def __init__(self, bot: discord.Client, leaderboard: list[str], guild: discord.Guild):
        title = f"Guild Leaderboard (for {guild.name})"

        self.data_leaderboard = {bot.get_user(int(i)): bot.db["guilds"][str(guild.id)][i] for i in leaderboard}

        description = ""

        pos = 0
        for user, data in self.data_leaderboard.items():
            pos += 1
            emoji = ":question:"
            if pos < 4:
                if pos == 1:
                    emoji = "## :first_place:"
                elif pos == 2:
                    emoji = "### :second_place:"
                elif pos == 3:
                    emoji = "### :third_place:"
            else:
                emoji = ":diamond_shape_with_a_dot_inside:"

            if pos == 1:
                description += f"{emoji} {data.gems} Gems - {user.mention}\n"
            else:
                description += f"{emoji} {data.gems} Gems - {user.mention}\n"


        self.set_footer(text="Ties are broken based on whose userid is a lower number than the others! (don't ask why). Made by @duve3")

        super().__init__(color=discord.Color.from_rgb(0, 0, 255), description=description, title=title)


class GemsCog(commands.Cog):
    def __init__(self, bot):  # : GemsBot.main.Client
        self.bot = bot
        self.logger = setupLogging(f"{self.__class__.__name__}")

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot is True:
            return

        member_data = self.bot.db["guilds"][str(message.guild.id)][str(message.author.id)]  # : GemsBot.main.MemberData

        if member_data.get_cooldown():
            return self.logger.debug(
                f"Skipping message due to cooldown... {time.time()} vs {member_data.cooldown_ends}")

        with open("./special-words.json") as swf:
            special: dict = json.loads(swf.read())
            special_words: dict = special["words"]

        for word, data in list(special_words.items()):
            if data["limit"] == 0:
                # removes the word if limit = 0 meaning that its maxed
                special_words.pop(word)

        for w in special_words.keys():
            if message.content.lower().find(w) > -1:
                worth = special_words[w]["worth"]
                member_data.gems += worth
                member_data.set_cooldown(special_words[w]["cooldown"])
                special_words[w]["limit"] -= 1
                await message.reply(f"Lucky! You just gained: {worth} gems! (balance: {member_data.gems})")
                break

        with open('./special-words.json', 'w') as swf:
            swf.write(json.dumps(special))

    @commands.hybrid_command("leaderboard")
    async def leaderboard(self, ctx: commands.Context):
        guild_members: dict = self.bot.db["guilds"][str(ctx.guild.id)]

        def get_gems(i):
            return guild_members[i].gems

        leaderboard = [i for i in sorted(guild_members.keys(), key=get_gems, reverse=True)]

        await ctx.reply(embeds=[LeaderboardEmbed(self.bot, leaderboard, ctx.guild)])

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you’d use cogs in extensions
# you would then define a global async function named 'setup', and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(GemsCog(bot=bot))
