import logging
import time
from log import setupLogging
import discord
import os
from discord.ext import commands, tasks
import json


class MemberData:
    def __init__(self):
        self.gems = 0
        self.xp = 0
        self.level = 0
        self.cooldown_ends = 0

    def set_cooldown(self, secs):
        self.cooldown_ends = time.time() + secs

    def get_cooldown(self):
        return self.cooldown_ends > time.time()

    def to_json(self):
        return self.__dict__

    def from_json(self, d):
        self.__dict__.update(d)
        return self


# globals
cogPath = "cogs."
debug = False


def getCogs():
    cogList = []
    for file in os.listdir(cogPath.replace(".", "/")):
        if file.endswith(".py") and not file.startswith("DISABLED_") and file != "log.py":
            cogList.append(file.split(".")[0])

    return cogList


class Client(commands.Bot):
    global debug

    def __init__(self):
        global debug
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        with open("./db.json") as db:
            self.db = json.loads(db.read())

            # the following goes trhough every guild and fixes the DB data
            for guild in self.db["guilds"]:
                for mid in self.db["guilds"][guild]:
                    print(mid)
                    print(guild)
                    print(self.db["guilds"][guild][mid])
                    self.db["guilds"][guild][mid] = MemberData().from_json(self.db["guilds"][guild][mid])
        if not debug:
            prefix = "."
        else:
            prefix = "cd.."
        super().__init__(
            command_prefix=prefix,
            intents=intents
        )

    # the method to override in order to run whatever you need before your bot starts
    async def setup_hook(self):
        # to avoid cog getting in this list, end it with something other than .py or make it start with "DISABLED_"
        self.saveDB.start()
        for cog in getCogs():
            await self.load_extension(f"{cogPath}{cog}")

    @tasks.loop(seconds=30)
    async def saveDB(self):
        with open("./db.json", "w+") as db:
            db.write(json.dumps(self.db, default=lambda o: o.__dict__))
            db.truncate()


client = Client()


# makes life easier when changing cogs
@client.command(name="reloadCogs")
async def reloadCogs(ctx):
    if ctx.author.id == 680116696819957810:
        logger.debug("Reloading all cogs!")
        for cog in getCogs():
            await client.reload_extension(f"{cogPath}{cog}")
        await ctx.reply("Reloaded all Cogs!")
    else:
        await ctx.reply(f"{ctx.author.mention} :gun:")


@client.event
async def on_ready():
    logger.info(
        f"I have successfully logged in as:\n\t{client.user.name}#{client.user.discriminator}\n\tID: {client.user.id}")


@client.event
async def on_member_join(member: discord.Member):
    client.db["guilds"][str(member.guild.id)][str(member.id)] = MemberData()


@client.event
async def on_guild_join(guild: discord.Guild):
    client.db["guilds"][str(guild.id)] = {}

    for member in guild.members:
        client.db["guilds"][str(guild.id)][str(member.id)] = MemberData()


@client.command("force_first_load")
async def force_first_load(ctx: commands.Context):
    if ctx.author.id != 680116696819957810:
        return

    await ctx.reply("Forcing event 'on_guild_join' to occur within this guild!")
    await on_guild_join(ctx.guild)
    await ctx.reply("Completed event!")



def main():
    global debug
    try:
        with open("token.secret") as tf:
            r = tf.read()
            if len(r.split("\n")) == 2:
                TOKEN = r.split("\n")[1]
                debug = True
            else:
                TOKEN = r.split("\n")[0]
    except FileNotFoundError:
        logger.error("Failed to find token inside of token.secret! Exiting...")
        return
    client.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    # setup
    logger = setupLogging("main", level=logging.DEBUG)
    setupLogging("discord", level=logging.INFO)
    setupLogging("discord.http", level=logging.INFO)
    try:
        # startup
        main()
    finally:
        # cleanup
        with open("./db.json", "w") as db:
            db.write(json.dumps(client.db, default=lambda o: o.__dict__))
