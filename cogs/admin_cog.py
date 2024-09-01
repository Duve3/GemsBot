import json

from discord.ext import commands
import discord
from log import setupLogging


async def admin_check(ctx, uid):
    with open("./admins.json", 'r') as af:
        ad = json.loads(af.read())

    if int(uid) not in ad["admins"]:
        return await ctx.reply("You unfortunately are unable to use this command (duh?)")


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = setupLogging(f"{self.__class__.__name__}")

    @commands.hybrid_command(name="set_gems")
    async def set_gems(self, ctx: commands.Context, member: discord.Member, value: int):
        await admin_check(ctx, ctx.author.id)

        gmember = self.bot.db["guilds"][str(ctx.guild.id)][str(member.id)]

        gmember.gems = value
        await ctx.reply(f"{member.mention}'s gems are now set to: {value}")


    @commands.command(name="set_config_text")
    async def set_config_txt(self, ctx: commands.Context, *args):
        await admin_check(ctx, ctx.author.id)

        with open("./special-words.json", 'w+') as swf:
            data = ' '.join(args).replace("'", '"').replace("\n", '').replace("\r", '')
            print(data)
            jdata = json.loads(data)
            swf.write(json.dumps(jdata))

        await ctx.reply("Successfully set `special-words.json` to what was provided.")

    @commands.command(name="set_config_file")
    async def set_config_file(self, ctx: commands.Context, file: discord.Attachment):
        await admin_check(ctx, ctx.author.id)

        with open('./special-words.json', 'w+') as swf:
            data = await file.read()
            jdata = json.loads(data)
            swf.write(json.dumps(jdata))

    # doing something when the cog gets loaded
    async def cog_load(self):
        self.logger.debug(f"{self.__class__.__name__} loaded!")

    # doing something when the cog gets unloaded
    async def cog_unload(self):
        self.logger.debug(f"{self.__class__.__name__} unloaded!")


# usually you would use cogs in extensions,
# you would then define a global async function named 'setup', and it would take 'bot' as its only parameter
async def setup(bot):
    # finally, adding the cog to the bot
    await bot.add_cog(AdminCog(bot=bot))
