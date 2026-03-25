import discord
from discord.ext import commands
from discord import app_commands
import os
from supabase import create_client

# ---------- KEEP ALIVE (FOR RENDER) ----------
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ---------- SUPABASE SETUP ----------
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# ---------- DATABASE FUNCTIONS ----------
def add_swear_bulk(user_id, amount):
    data = supabase.table("swears").select("*").eq("user_id", user_id).execute()

    if data.data:
        supabase.table("swears").update({
            "count": data.data[0]["count"] + amount
        }).eq("user_id", user_id).execute()
    else:
        supabase.table("swears").insert({
            "user_id": user_id,
            "count": amount
        }).execute()


def get_swears(user_id):
    data = supabase.table("swears").select("*").eq("user_id", user_id).execute()
    return data.data[0]["count"] if data.data else 0


def get_leaderboard():
    data = supabase.table("swears").select("*").order("count", desc=True).limit(10).execute()
    return data.data

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------- SWEAR WORDS ----------
BAD_WORDS = [
    "gago",
    "gagu",
    "tarantado",
    "tangina",
    "pakyu",
    "puta",
    "pakshet",
    "pekpek",
    "tite",
    "pota",
    "potang",
    "putang",
    "shet",
    "hayop",
    "yawa",
    "milk",
    "tanga",
    "burat",
    "borat",
    "bobo",
    "obob",
    "nicdao",
    "niga",
    "nigga",
    "niger",
    "nigger"
]

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower().replace(" ", "").replace(".", "").replace("*", "")

    total_swears = 0
    for word in BAD_WORDS:
        total_swears += content.count(word)

    if total_swears > 0:
        user_id = str(message.author.id)

        add_swear_bulk(user_id, total_swears)
        count = get_swears(user_id)

        await message.channel.send(
            f"{message.author.mention} now has {count:,} swears 🤬 (+{total_swears})"
        )

    await bot.process_commands(message)

# ---------- SLASH COMMANDS ----------
@tree.command(name="swears", description="Check someone's swear count")
async def swears(interaction: discord.Interaction, user: discord.Member):
    count = get_swears(str(user.id))

    await interaction.response.send_message(
        f"{user.mention} has {count:,} total swears 🤬"
    )

@tree.command(name="leaderboard", description="Top swearers globally")
async def leaderboard(interaction: discord.Interaction):
    top = get_leaderboard()

    if not top:
        await interaction.response.send_message("No data yet.")
        return

    message = "**🌍 Global Swear Leaderboard**\n"

    for i, row in enumerate(top, start=1):
        user_id = row["user_id"]
        count = row["count"]

        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = f"User {user_id}"

        message += f"{i}. {name} - {count:,} swears\n"

    await interaction.response.send_message(message)

@tree.command(name="server_leaderboard", description="Top swearers in this server")
async def server_leaderboard(interaction: discord.Interaction):
    server_data = []

    for member in interaction.guild.members:
        count = get_swears(str(member.id))
        if count > 0:
            server_data.append((member, count))

    server_data.sort(key=lambda x: x[1], reverse=True)
    top = server_data[:10]

    if not top:
        await interaction.response.send_message("No swears recorded in this server yet.")
        return

    message = "**🏠 Server Swear Leaderboard**\n"

    for i, (member, count) in enumerate(top, start=1):
        message += f"{i}. {member.display_name} - {count:,} swears\n"

    await interaction.response.send_message(message)

# ---------- RUN ----------
keep_alive()
bot.run(os.getenv("TOKEN"))