import discord
from discord.ext import commands
import os
import json
import random
from flask import Flask
from threading import Thread

# --- Webserver für Uptime (Railway / Replit kompatibel) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot läuft!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- Intents & Bot-Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

print("🚀 Starte Bot Initialisierung")

# --- Bank-Datei ---
BANK_FILE = "bank.json"

def load_bank():
    if not os.path.exists(BANK_FILE):
        with open(BANK_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_bank(data):
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_user_gold(user_id):
    bank = load_bank()
    entries = bank.get(user_id, [])
    return sum(entry.get("betrag", 0) for entry in entries)

def update_user_gold(user_id, amount, reason):
    bank = load_bank()
    if user_id not in bank:
        bank[user_id] = []
    bank[user_id].append({"betrag": amount, "grund": reason})
    save_bank(bank)

# --- Events ---
@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")

# --- Kommandos ---
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    gold = get_user_gold(user_id)
    await ctx.send(f"{ctx.author.mention}, dein Kontostand beträgt {gold} Gold.")

@bot.command()
async def coinflip(ctx, bet: int, choice: str = None):
    print("🎲 Coinflip wurde aufgerufen")
    user_id = str(ctx.author.id)
    gold = get_user_gold(user_id)

    if bet <= 0:
        await ctx.send("Bitte setze einen positiven Betrag.")
        return
    if bet > gold:
        await ctx.send("Du hast nicht genug Gold.")
        return
    if choice is None:
        await ctx.send("Bitte wähle Kopf oder Zahl. Beispiel: `!coinflip 100 Kopf`")
        return

    choice = choice.lower()
    if choice not in ["kopf", "zahl"]:
        await ctx.send("Nur 'Kopf' oder 'Zahl' sind gültige Optionen.")
        return

    result = random.choice(["kopf", "zahl"])
    await ctx.send(f"🪙 Die Münze zeigt: **{result.capitalize()}**")

    if result == choice:
        update_user_gold(user_id, bet, "Coinflip Gewinn")
        await ctx.send(f"🎉 Du hast gewonnen! Gewinn: {bet} Gold.")
    else:
        update_user_gold(user_id, -bet, "Coinflip Verlust")
        await ctx.send(f"😢 Du hast verloren und {bet} Gold verloren.")

# --- Bot starten ---
token = os.getenv("DISCORD_TOKEN")
if not token:
    print("❌ Kein DISCORD_TOKEN gefunden. Bitte in den Railway Secrets setzen.")
    exit(1)

bot.run(token)
