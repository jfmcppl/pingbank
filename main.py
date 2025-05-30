import discord
from discord.ext import commands
import random
import json
import os
from flask import Flask
from threading import Thread
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Webserver für UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "Pingwinsche Staatsbank Bot läuft!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# --- Intents ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# --- Bot Setup ---
bot = commands.Bot(command_prefix='!', intents=intents)

BANK_FILE = 'bank.json'
bank_data = {}

def load_bank():
    global bank_data
    if not os.path.exists(BANK_FILE):
        with open(BANK_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    try:
        with open(BANK_FILE, 'r', encoding='utf-8') as f:
            bank_data = json.load(f)
            print(f"📊 Bank-Daten geladen: {len(bank_data)} Konten")
    except json.JSONDecodeError:
        print("❌ Fehler beim Lesen der bank.json - verwende leere Bank")
        bank_data = {}
    return bank_data

def save_bank(data):
    global bank_data
    bank_data = data
    with open(BANK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class BankFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('bank.json') and not event.is_directory:
            print("🔄 bank.json wurde geändert - lade Daten neu...")
            time.sleep(0.1)
            load_bank()
            print(f"✅ Neue Bank-Daten: {bank_data}")

def start_file_watcher():
    event_handler = BankFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    print("👀 Datei-Überwachung für bank.json gestartet")
    return observer

def get_user_gold(user_id):
    entries = bank_data.get(user_id, [])
    if isinstance(entries, list):
        return sum(entry.get("betrag", 0) for entry in entries)
    return 0

def update_user_gold(user_id, amount, reason):
    if user_id not in bank_data:
        bank_data[user_id] = []
    bank_data[user_id].append({"betrag": amount, "grund": reason})
    save_bank(bank_data)

# --- Events & Grund-Commands ---
@bot.event
async def on_ready():
    print(f'🤖 Die Pingwinsche Staatsbank ist online als {bot.user}')
    load_bank()
    start_file_watcher()

@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    load_bank()
    total_gold = get_user_gold(user_id)
    try:
        await ctx.author.send(f'{ctx.author.name}, dein Kontostand beträgt {total_gold} Gold.')
        await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, ich kann dir keine Direktnachricht schicken.")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# --- Nur Coinflip Command (Casino Light) ---
@bot.command()
async def coinflip(ctx, bet: int, choice: str = None):
    print("✅ Coinflip command wurde geladen")  # <- DEBUG LOG

    user_id = str(ctx.author.id)
    load_bank()
    gold = get_user_gold(user_id)

    if bet <= 0:
        await ctx.send("Bitte setze einen positiven Betrag!")
        return
    if bet > gold:
        await ctx.send("Du hast nicht genug Gold!")
        return
    
    if choice is None:
        await ctx.send("Bitte wähle Kopf oder Zahl! Beispiel: `!coinflip 100 Kopf`")
        return
    
    choice = choice.lower()
    if choice not in ["kopf", "zahl"]:
        await ctx.send("Bitte wähle 'Kopf' oder 'Zahl'!")
        return

    result = random.choice(["kopf", "zahl"])
    
    await ctx.send(f"🪙 Die Münze zeigt: **{result.capitalize()}**")

    if result == choice:
        update_user_gold(user_id, bet, "Gewinn beim Coinflip")
        await ctx.send(f"🎉 Du hast gewonnen! Dein Gewinn: {bet} Gold.")
    else:
        update_user_gold(user_id, -bet, "Verlust beim Coinflip")
        await ctx.send(f"😢 Du hast verloren und {bet} Gold verloren.")

# --- Bot starten ---
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("❌ DISCORD_TOKEN nicht gefunden!")
    exit(1)

bot.run(token)

bot.run(token)
