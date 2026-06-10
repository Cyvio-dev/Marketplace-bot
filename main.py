import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

Token = os.getenv("DISCORD_TOKEN")
db = os.getenv("DATABASE")

class Main(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        self.db = await asyncpg.create_pool(db, min_size=6, max_size=10)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS reviews(
                username BIGINT NOT NULL,
                review TEXT NOT NULL
            );
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS set_approval(
                guild_id BIGINT PRIMARY KEY,
                channel_id BIGINT NOT NULL  
            );                                     
        """)
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    print(f"Not loaded: {filename} - {e}")

        print("Extension loaded!")

    async def on_ready(self):
        await self.tree.sync()
        print("Bot is ready and tree synced!")


bot = Main()
bot.run(Token)