from discord.ext import commands
import random
import json
import os

BANK_FILE = 'bank.json'

def load_bank():
    if not os.path.exists(BANK_FILE):
        with open(BANK_FILE, 'w') as f:
            json.dump({}, f)
    with open(BANK_FILE, 'r') as f:
        return json.load(f)

def save_bank(data):
    with open(BANK_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_gold(self, user_id):
        bank_data = load_bank()
        entries = bank_data.get(user_id, [])
        return sum(entry.get("betrag", 0) for entry in entries)

    def update_user_gold(self, user_id, amount, reason):
        bank_data = load_bank()
        if user_id not in bank_data:
            bank_data[user_id] = []
        bank_data[user_id].append({"betrag": amount, "grund": reason})
        save_bank(bank_data)

    @commands.command()
    async def coinflip(self, ctx, bet: int):
        user_id = str(ctx.author.id)
        gold = self.get_user_gold(user_id)
        if bet <= 0:
            await ctx.send("Bitte setze einen positiven Betrag!")
            return
        if bet > gold:
            await ctx.send("Du hast nicht genug Gold!")
            return

        result = random.choice(["Kopf", "Zahl"])
        winner_side = random.choice(["Kopf", "Zahl"])  # Gewinnerseite simulieren

        if result == winner_side:
            self.update_user_gold(user_id, bet, "Gewinn beim Coinflip")
            await ctx.send(f"🎉 Du hast gewonnen! Dein Gewinn: {bet} Gold.")
        else:
            self.update_user_gold(user_id, -bet, "Verlust beim Coinflip")
            await ctx.send(f"😢 Du hast verloren und {bet} Gold verloren.")

    @commands.command()
    async def slotmachine(self, ctx, bet: int):
        user_id = str(ctx.author.id)
        gold = self.get_user_gold(user_id)
        if bet <= 0:
            await ctx.send("Bitte setze einen positiven Betrag!")
            return
        if bet > gold:
            await ctx.send("Du hast nicht genug Gold!")
            return

        slots = ['🍒', '🍋', '🍊', '🍉', '⭐', '💎']
        result = [random.choice(slots) for _ in range(3)]

        await ctx.send(f"🎰 Ergebnis: {' | '.join(result)}")

        # Gewinnregeln
        if result[0] == result[1] == result[2]:
            payout = bet * 5
            self.update_user_gold(user_id, payout, "Gewinn bei Slotmachine (Dreier)")
            await ctx.send(f"🎉 Jackpot! Du gewinnst {payout} Gold!")
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            payout = bet * 2
            self.update_user_gold(user_id, payout, "Gewinn bei Slotmachine (Zweier)")
            await ctx.send(f"🎉 Du hast zwei Symbole gleich! Gewinn: {payout} Gold.")
        else:
            self.update_user_gold(user_id, -bet, "Verlust bei Slotmachine")
            await ctx.send(f"Leider kein Gewinn. Du verlierst {bet} Gold.")

    @commands.command()
    async def blackjack(self, ctx, bet: int):
        user_id = str(ctx.author.id)
        gold = self.get_user_gold(user_id)
        if bet <= 0:
            await ctx.send("Bitte setze einen positiven Betrag!")
            return
        if bet > gold:
            await ctx.send("Du hast nicht genug Gold!")
            return

        def card_value(card):
            if card in ['J', 'Q', 'K']:
                return 10
            elif card == 'A':
                return 11
            else:
                return int(card)

        def hand_value(hand):
            value = sum(card_value(card) for card in hand)
            aces = hand.count('A')
            while value > 21 and aces:
                value -= 10
                aces -= 1
            return value

        deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(deck)

        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        def format_hand(hand):
            return ', '.join(hand)

        while hand_value(player_hand) < 17:
            player_hand.append(deck.pop())

        player_total = hand_value(player_hand)
        dealer_total = hand_value(dealer_hand)

        await ctx.send(f"🃏 Deine Karten: {format_hand(player_hand)} (Wert: {player_total})")
        await ctx.send(f"🃏 Dealer-Karten: {format_hand(dealer_hand)} (Wert: {dealer_total})")

        if player_total > 21:
            self.update_user_gold(user_id, -bet, "Verlust bei Blackjack (Bust)")
            await ctx.send(f"Du hast dich überkauft und verloren! {bet} Gold wurden abgezogen.")
        elif dealer_total > 21 or player_total > dealer_total:
            self.update_user_gold(user_id, bet, "Gewinn bei Blackjack")
            await ctx.send(f"Glückwunsch, du hast gewonnen! {bet} Gold gutgeschrieben.")
        elif player_total == dealer_total:
            await ctx.send("Unentschieden! Dein Einsatz wird zurückerstattet.")
        else:
            self.update_user_gold(user_id, -bet, "Verlust bei Blackjack")
            await ctx.send(f"Der Dealer gewinnt. Du verlierst {bet} Gold.")

def setup(bot):
    bot.add_cog(Casino(bot))
