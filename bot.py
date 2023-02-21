import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import app_commands 
import pymongo
import generation
import tok
import itertools
import random

# 2.0
# Add more emojis when win 
# More ways to bet in black jack and roullet
# Card images


MONGO = tok.mongo
TOKEN = tok.token
COIN_COLLECTION = tok.coin_collection
CHANNEL_ID = tok.channel_ID
CLIENT = tok.client

client = pymongo.MongoClient(MONGO)
db = client[CLIENT]

#------ Bot ------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)
#--- Bot Startup
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}') #Bot Name



# "_id":int , "coins":int
@bot.tree.command()
async def db(interaction: discord.Interaction,coins:int):
    db = client[CLIENT]
    collection = db[COIN_COLLECTION]
    collection.insert_one({"_id": interaction.user.id,"user_name":interaction.user.name,"coins":coins})
    await interaction.response.send_message("TRUE")

#------ Slash Commands ------
#------ Status ------
@bot.tree.command()
async def status(interaction: discord.Interaction):
    """Button Test"""
    embed = discord.Embed(title=f"{interaction.user.name} Status",description=f"Name: {interaction.user.name}\nID: {interaction.user.id}\nCoins: DB ENTER", color=0x11806A)
    await interaction.response.send_message(embed = embed,ephemeral=True)

#------ Roulette ------
@bot.tree.command()
async def roulette(interaction: discord.Interaction, bet:int):
    #Bet ammount first
    """Play Roulette ⬛🟥⬛🟥"""
    bet = bet
    db = client[CLIENT]
    collection = db[COIN_COLLECTION]
    userData = collection.find_one({"_id": interaction.user.id})
    total = userData["coins"]
    if bet > total:
        embed = discord.Embed(title=f"Bet Canceled",description=f"Your total coins of {total} is less then bet amount {bet}", color=0xFF0000)
        log(interaction.user.name,interaction.user.id,f"Bet amount:{bet} but was over total {total} (Canceled)")
        await interaction.response.send_message(embed = embed,ephemeral=True)
    elif bet <= total:
        log(interaction.user.name,interaction.user.id,f"Bet amount:{bet} with a of {total} (Confirmed) (Coins Held intill bet completed)")
        view = roulette_check()
        userData["coins"] = userData["coins"] - bet
        collection.replace_one({"_id":interaction.user.id}, userData)
        db = client[CLIENT]
        collection = db["LiveBets"]
        collection.insert_one({"_id": interaction.user.id,"bet":bet})   
        embed = discord.Embed(title=f"Roulette ⬛🟥⬛🟥",description=f"Confirm your bet amount of {bet}", color=0x11806A)
        await interaction.response.send_message(embed = embed,view=view,ephemeral=True)

#Delete after its been sent
class roulette_check(discord.ui.View):
    @discord.ui.button(label = "Confirm", style = discord.ButtonStyle.success)
    async def confirmed(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            des = "Please pick a Color"
            view = roulette_pick()
            embed = discord.Embed(title="Welcome to Roulette", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed,view=view,ephemeral=True)


    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "❌" )
    async def exit(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            #But bets back into wallet and cancel live bet
            db = client[CLIENT]
            collection = db["LiveBets"]
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + bet
            collection.replace_one({"_id":interaction.user.id}, userData)
            embed = discord.Embed(title="Canceled", description=f"Your bet of {bet} has been returned", color=0x2D9922)
            await interaction.response.send_message(embed= embed,ephemeral=True)

#ONly user can push button
class roulette_pick(discord.ui.View):
    @discord.ui.button(label = "Red", style = discord.ButtonStyle.danger)
    async def red(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            win = generation.roulette_blackorred('red')
            if win == True:
                betData = collection.find_one({"_id": interaction.user.id})
                bet = betData["bet"]
                collection.delete_one({"_id": interaction.user.id})

                des = f"You Win {bet}\nReturn: {bet*2}"
                embed = discord.Embed(title="🟥🟥 Red Was Hit 🟥🟥 ", description=des, color=0x2D9922)
                embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet} in roulette 🔔", color=0x2D9922)

                win_ammount = bet * 2
                collection = db[COIN_COLLECTION]
                userData = collection.find_one({"_id": interaction.user.id})
                userData["coins"] = userData["coins"] + win_ammount
                collection.replace_one({"_id":interaction.user.id}, userData)

                await interaction.response.send_message(embed= embed, ephemeral=True)
                await bot.get_channel(CHANNEL_ID).send(embed=embed2)

            if win == False:
                #Pull bet from mongo Return
                des = "You Lose"
                collection.delete_one({"_id": interaction.user.id})
                embed = discord.Embed(title="⬛⬛ Black Was Hit ⬛⬛", description=des, color=0x2D9922)
                await interaction.response.send_message(embed= embed, ephemeral=True)    

            #Sent into Generation
    @discord.ui.button(label = "Black", style = discord.ButtonStyle.secondary)
    async def black(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            win = generation.roulette_blackorred('black')
            if win == True:
                betData = collection.find_one({"_id": interaction.user.id})
                bet = betData["bet"]
                collection.delete_one({"_id": interaction.user.id})

                des = f"You Win {bet}\nReturn: {bet*2}"
                embed = discord.Embed(title="⬛⬛ Black Was Hit ⬛⬛", description=des, color=0x2D9922)
                embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet} in roulette 🔔", color=0x2D9922)
                
                win_ammount = bet * 2
                collection = db[COIN_COLLECTION]
                userData = collection.find_one({"_id": interaction.user.id})
                userData["coins"] = userData["coins"] + win_ammount
                collection.replace_one({"_id":interaction.user.id}, userData)

                await interaction.response.send_message(embed= embed, ephemeral=True)
                await bot.get_channel(CHANNEL_ID).send(embed=embed2)

            if win == False:
                #Pull bet from mongo Return
                des = "You Lose"
                collection.delete_one({"_id": interaction.user.id})
                embed = discord.Embed(title="🟥🟥 Red Was Hit 🟥🟥 ", description=des, color=0x2D9922)
                await interaction.response.send_message(embed= embed, ephemeral=True)  
        
            #Sent into Generation
    #@discord.ui.button(label = "Numbers", style = discord.ButtonStyle.secondary)
        #async def start1(self,interaction:discord.Interaction, button: discord.ui.Button):
#class roulette_numbers(discord.ui.View):
    #Itteration of all 0-36 numbers :(


#------ BlackJack ------
@bot.tree.command()
async def blackjack(interaction: discord.Interaction, bet:int):
    #Bet ammount first
    """Play Black Jack ♠️♥️♣️♦️"""
    bet = bet

    db = client[CLIENT]
    collection = db[COIN_COLLECTION]
    userData = collection["coins"]
    userData = collection.find_one({"_id": interaction.user.id})
    total = userData["coins"]
    if total >= bet:
        db = client[CLIENT]
        collection = db[COIN_COLLECTION]
        userData["coins"] = userData["coins"] - bet
        collection.replace_one({"_id":interaction.user.id}, userData)
        collection = db["LiveBets"]
        collection.insert_one({"_id":interaction.user.id,"bet":bet,"ingame":False})
        view = blackjack_check()
        embed = discord.Embed(title=f"Black Jack ♠️♥️♣️♦️",description=f"Confirm your bet amount of {bet}", color=0x11806A)
        await interaction.response.send_message(embed = embed,view=view,ephemeral=True)
    elif total < bet:
        embed = discord.Embed(title=f"Bet Canceled",description=f"Your total coins of {total} is less then bet amount {bet}", color=0xFF0000)
        log(interaction.user.name,interaction.user.id,f"Bet amount:{bet} but was over total {total} (Canceled)")
        await interaction.response.send_message(embed = embed,ephemeral=True)

#Delete after its been sent
class blackjack_check(discord.ui.View):
    @discord.ui.button(label = "Confirm", style = discord.ButtonStyle.success )
    async def confirmed(self,interaction:discord.Interaction, button: discord.ui.Button):
        ####
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        userData = collection.find_one({"_id":interaction.user.id})
        live = userData["ingame"]
        if live == True:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)


        vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        suits = ['spades', 'clubs', 'hearts', 'diamonds']
        deck = list(itertools.product(vals, suits))
        random.shuffle(deck)
        player_score = face(deck[0][0]) + face(deck[2][0])
        dealer_score = face(deck[1][0]) + face(deck[3][0])


        player_cards = []
        dealer_cards = []
        player_cards.append(deck[0][0])
        player_cards.append(deck[2][0])
        dealer_cards.append(deck[1][0])
        dealer_cards.append(deck[3][0])
        db = client[CLIENT]
        collection = db["LiveBets"]
        userData = collection.find_one({"_id":interaction.user.id})
        userData["player_cards"] = player_cards
        userData["dealer_cards"] = dealer_cards
        userData["ingame"] = True
        collection.replace_one({"_id":interaction.user.id}, userData)
        player_cards.clear()
        dealer_cards.clear()
        #PUSH 21==21
        if player_score == 21 & dealer_score == 21:
            embed = discord.Embed(title="Dealer and House hit 21", description="Push", color=0x2D9922)
            collection.delete_one({"_id": interaction.user.id})
            await interaction.response.send_message(embed= embed, ephemeral=True)
        #BLAKCJACK
        elif player_score  == 21:
            des = f"You Win! \nReturn: 3/2"
            bet = userData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id":interaction.user.id})
            bet = round(bet * (1.5))
            userData["coins"] = bet + userData["coins"]
            collection.replace_one({"_id":interaction.user.id}, userData)
            embed2 = discord.Embed(title=f"🔔🔔 {interaction.user.name} has just hit BlackJack winning {bet}🔔🔔", color=0x2D9922)
            embed = discord.Embed(title="♠️♥️♣️♦️ BlackJack ♠️♥️♣️♦️", description=des, color=0x2D9922)
            collection.delete_one({"_id": interaction.user.id})
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        #HOUSE WIN
        elif dealer_score == 21:
            embed = discord.Embed(title="House Hits BlackJack", description="You Lose", color=0x2D9922)
            collection.delete_one({"_id": interaction.user.id})
            await interaction.response.send_message(embed= embed, ephemeral=True)
        else:
            des = f"Dealer Hand:\n\t{get_emoji(deck[1][0])} | 🔲 \n\nYour Hand:\n\t {get_emoji(deck[0][0])} | {get_emoji(deck[2][0])} \n\n"
            #PUT CARDS IN DB
            view = hitormiss()
            embed = discord.Embed(title="Welcome to Black Jack ♠️♥️♣️♦️", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed,ephemeral=True,view=view)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "❌" )
    async def exit(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            betData = collection.find_one({"_id": interaction.user.id})
            live = betData["ingame"]
            betData = collection.find_one({"_id": interaction.user.id})
            if live == True:
                button.disabled = True
                await interaction.response.edit_message(view = self)
            else:
            #But bets back into wallet and cancel live bet
                db = client[CLIENT]
                collection = db["LiveBets"]
                betData = collection.find_one({"_id": interaction.user.id})
                bet = betData["bet"]
                collection.delete_one({"_id": interaction.user.id})
                collection = db[COIN_COLLECTION]
                userData = collection.find_one({"_id": interaction.user.id})
                userData["coins"] = userData["coins"] + bet
                collection.replace_one({"_id":interaction.user.id}, userData)
                embed = discord.Embed(title="Canceled", description=f"Your bet of {bet} has been returned", color=0x2D9922)
                await interaction.response.send_message(embed= embed,ephemeral=True)

class hitormiss(discord.ui.View):
    @discord.ui.button(label = "Hit", style = discord.ButtonStyle.success)
    async def hit(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            betData = collection.find_one({"_id": interaction.user.id})
            live = betData["ingame"]
            betData = collection.find_one({"_id": interaction.user.id})
            if live == False:
                button.disabled = True
                await interaction.response.edit_message(view = self)

        player_draw(interaction.user.id)

        userData = collection.find_one({"_id":interaction.user.id})
        player_cards = userData["player_cards"]
        dealer_cards = userData["dealer_cards"]

        print(player_cards)
        player_total = 0
        player_size = len(player_cards) 
        dealer_size = len(dealer_cards)
        for x in range(player_size):
            temp_num = player_cards[x]
            temp_num = face(temp_num)
            player_total = temp_num + player_total

        if player_total > 21:
            dealer_cards = userData["dealer_cards"]
            player_cards = userData["player_cards"]
            display_list = []
            display_list2 = []
            for x in range(dealer_size):
                temp_num = dealer_cards[x]
                display_list.append(get_emoji(temp_num))
            for x in range(player_size):
                temp_num = player_cards[x]
                display_list2.append(get_emoji(temp_num))
            des = f"Dealer Hand:\n{display_list}\n\nYour Hand:\n{display_list2}"
            embed = discord.Embed(title="(Bust) House Wins", description=des, color=0x2D9922)
            collection.delete_one({"_id": interaction.user.id})
            display_list.clear()
            display_list2.clear()
            await interaction.response.send_message(embed= embed, ephemeral=True)

        elif player_total < 21:
            view = self
            dealer_cards = userData["dealer_cards"]
            player_cards = userData["player_cards"]
            display_list = []
            display_list2 = []
            temp_num = dealer_cards[0]
            display_list.append(get_emoji(temp_num))
            for x in range(player_size):
                temp_num = player_cards[x]
                display_list2.append(get_emoji(temp_num))
            des = f"Dealer Hand:\n{display_list}| 🔲\n\nYour Hand:\n{display_list2}"
            embed = discord.Embed(title="Welcome to Black Jack ♠️♥️♣️♦️", description=des, color=0x2D9922)
            display_list.clear()
            display_list2.clear()
            await interaction.response.edit_message(embed = embed,view = view)


    @discord.ui.button(label = "Stay", style = discord.ButtonStyle.grey)
    async def stay(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            betData = collection.find_one({"_id": interaction.user.id})
            live = betData["ingame"]
            betData = collection.find_one({"_id": interaction.user.id})
            if live == False:
                button.disabled = True
                await interaction.response.edit_message(view = self)

        userData = collection.find_one({"_id":interaction.user.id})
        player_cards = userData["player_cards"]
        dealer_cards = userData["dealer_cards"]
        player_total = 0
        dealer_total = 0
        player_size = len(player_cards)
        dealer_size = len(dealer_cards)
        for x in range(player_size):
            temp_num = player_cards[x]
            temp_num = face(temp_num)
            player_total = temp_num + player_total
        for x in range(dealer_size):
            temp_num = dealer_cards[x]
            temp_num = face(temp_num)
            dealer_total = temp_num + dealer_total

        dealer_draw(interaction.user.id,dealer_total)

        #Recheck after draw
        userData = collection.find_one({"_id":interaction.user.id})
        dealer_cards = userData["dealer_cards"]

        dealer_total = 0
        dealer_size = len(dealer_cards)
        for x in range(dealer_size):
            temp_num = dealer_cards[x]
            temp_num = face(temp_num)
            dealer_total = temp_num + dealer_total

        print(dealer_total)

        if dealer_total == player_total:
            dealer_cards = userData["dealer_cards"]
            player_cards = userData["player_cards"]
            display_list = []
            display_list2 = []
            for x in range(dealer_size):
                temp_num = dealer_cards[x]
                display_list.append(get_emoji(temp_num))
            for x in range(player_size):
                temp_num = player_cards[x]
                display_list2.append(get_emoji(temp_num))
            des = f"Dealer Hand:\n{display_list}\n\nYour Hand:\n{display_list2}"
            display_list.clear()
            display_list2.clear()
            embed = discord.Embed(title="House and Dealer Have Same Score", description="Push", color=0x2D9922)
            bet = userData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id":interaction.user.id})
            userData["coins"] = bet + userData["coins"]
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
        elif dealer_total > player_total and dealer_total<21:
            dealer_cards = userData["dealer_cards"]
            player_cards = userData["player_cards"]
            display_list = []
            display_list2 = []
            for x in range(dealer_size):
                temp_num = dealer_cards[x]
                display_list.append(get_emoji(temp_num))
            for x in range(player_size):
                temp_num = player_cards[x]
                display_list2.append(get_emoji(temp_num))
            des = f"Dealer Hand:\n{display_list}\n\nYour Hand:\n{display_list2}"
            embed = discord.Embed(title="House Wins", description=des, color=0x2D9922)
            collection.delete_one({"_id": interaction.user.id})
            display_list.clear()
            display_list2.clear()
            await interaction.response.send_message(embed= embed, ephemeral=True)
        elif player_total > dealer_total or dealer_total > 21:
            dealer_cards = userData["dealer_cards"]
            player_cards = userData["player_cards"]
            display_list = []
            display_list2 = []
            for x in range(dealer_size):
                temp_num = dealer_cards[x]
                display_list.append(get_emoji(temp_num))
            for x in range(player_size):
                temp_num = player_cards[x]
                display_list2.append(get_emoji(temp_num))
            des = f"Dealer Hand:\n{display_list}\n\nYour Hand:\n{display_list2}"
            display_list.clear()
            display_list2.clear()
            embed = discord.Embed(title="♠️♥️♣️♦️ Player Win ♠️♥️♣️♦️", description=des, color=0x2D9922)
            bet = userData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id":interaction.user.id})
            bet = round(bet * (1.5))
            userData["coins"] = bet + userData["coins"]
            collection.replace_one({"_id":interaction.user.id}, userData)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet} in BlackJack 🔔", color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)

#------ Dice ------
@bot.tree.command()
async def dice(interaction: discord.Interaction, bet:int):
    #Bet ammount first
    """Play Roulette 🎲🎲🎲🎲"""
    bet = bet
    db = client[CLIENT]
    collection = db[COIN_COLLECTION]
    userData = collection.find_one({"_id": interaction.user.id})
    total = userData["coins"]
    if bet > total:
        embed = discord.Embed(title=f"Bet Canceled",description=f"Your total coins of {total} is less then bet amount {bet}", color=0xFF0000)
        log(interaction.user.name,interaction.user.id,f"Bet amount:{bet} but was over total {total} (Canceled)")
        await interaction.response.send_message(embed = embed,ephemeral=True)
    elif bet <= total:
        log(interaction.user.name,interaction.user.id,f"Bet amount:{bet} with a of {total} (Confirmed) (Coins Held intill bet completed)")
        view = dice_check()
        userData["coins"] = userData["coins"] - bet
        collection.replace_one({"_id":interaction.user.id}, userData)
        db = client[CLIENT]
        collection = db["LiveBets"]
        collection.insert_one({"_id": interaction.user.id,"bet":bet})   
        embed = discord.Embed(title=f"Dice 🎲🎲🎲🎲",description=f"Confirm your bet amount of {bet}", color=0x11806A)
        await interaction.response.send_message(embed = embed,view=view,ephemeral=True)

#Delete after its been sent
class dice_check(discord.ui.View):
    @discord.ui.button(label = "Confirm", style = discord.ButtonStyle.success)
    async def confirmed(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            des = "Please pick Number"
            view = dice_game()
            embed = discord.Embed(title="Welcome to Dice", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed,view=view,ephemeral=True)

    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "❌" )
    async def exit(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        elif collection.count_documents(query) == 1:
            #But bets back into wallet and cancel live bet
            db = client[CLIENT]
            collection = db["LiveBets"]
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + bet
            collection.replace_one({"_id":interaction.user.id}, userData)
            embed = discord.Embed(title="Canceled", description=f"Your bet of {bet} has been returned", color=0x2D9922)
            await interaction.response.send_message(embed= embed,ephemeral=True)


class dice_game(discord.ui.View):

    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "2️⃣" )
    async def two(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(2)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*34}\nReturn: {bet*35}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*34} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 34
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)

    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "3️⃣" )
    async def three(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(3)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*17}\nReturn: {bet*18}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*17} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 18
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)

    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "4️⃣" )
    async def four(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(4)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*11}\nReturn: {bet*12}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*11} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 12
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "5️⃣" )
    async def five(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(5)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*8}\nReturn: {bet*9}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*8} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 9
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "6️⃣" )
    async def six(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(6)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {(bet*6)}\nReturn: {bet*7}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*6} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 7
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "7️⃣" )
    async def seven(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(7)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*5}\nReturn: {bet*6}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*5} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 6
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "8️⃣" )
    async def eight(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(8)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*6}\nReturn: {bet*7}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*6} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 7
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "9️⃣" )
    async def nine(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(9)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*8}\nReturn: {bet*9}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*8} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 9
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "", style = discord.ButtonStyle.grey, 
    emoji = "🔟" )
    async def ten(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(10)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*11}\nReturn: {bet*12}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*11} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 12
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "11", style = discord.ButtonStyle.grey )
    async def eleven(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(11)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*17}\nReturn: {bet*18}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*17} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 18
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)
    @discord.ui.button(label = "12", style = discord.ButtonStyle.grey)
    async def twelve(self,interaction:discord.Interaction, button: discord.ui.Button):
        db = client[CLIENT]
        collection = db["LiveBets"]
        query = {"_id":interaction.user.id}
        if collection.count_documents(query) == 0:
            #If button is hit with no live bets disable button
            button.disabled = True
            await interaction.response.edit_message(view = self)
        win,hit = generation.dice_game(12)
        if win == True:
            betData = collection.find_one({"_id": interaction.user.id})
            bet = betData["bet"]
            collection.delete_one({"_id": interaction.user.id})
            des = f"You Win {bet*34}\nReturn: {bet*35}"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            embed2 = discord.Embed(title=f"🔔 {interaction.user.name} has just won {bet*34} in dice 🔔", color=0x2D9922)
            win_ammount = bet * 34
            collection = db[COIN_COLLECTION]
            userData = collection.find_one({"_id": interaction.user.id})
            userData["coins"] = userData["coins"] + win_ammount
            collection.replace_one({"_id":interaction.user.id}, userData)
            await interaction.response.send_message(embed= embed, ephemeral=True)
            await bot.get_channel(CHANNEL_ID).send(embed=embed2)
        else:
            collection.delete_one({"_id": interaction.user.id})
            des = "You Lose"
            embed = discord.Embed(title=f" {hit} Was Hit ", description=des, color=0x2D9922)
            await interaction.response.send_message(embed= embed, ephemeral=True)


#------ LeaderBoard ------
@bot.tree.command()
async def leaderboard(interaction: discord.Interaction):
    db = client[CLIENT]
    collection = db[COIN_COLLECTION]
    query_result = collection.find().sort('coins', pymongo.DESCENDING).limit(10)
    result_list = [(doc['user_name'], doc['coins']) for doc in query_result]

    leaderBlist = ""
    # Print the IDs on separate lines
    for user_name,coins in result_list:
        coins = str(coins)
        leaderBlist = leaderBlist + user_name +":" + coins +"\n"
    des = f"{leaderBlist}"
    embed = discord.Embed(title=f"Leaderboard",description=des, color=0x2D9922)
    await interaction.response.send_message(embed= embed)



#
def face(card_value:str):
    if card_value == 'Jack':
        card_value = '10'
    elif card_value == 'Queen':
        card_value = '10'
    elif card_value == 'King':
        card_value = '10'
    elif card_value == 'Ace':
        card_value = '11'
    card_value = int(card_value)
    return card_value

def get_emoji(card_num:str):
    if card_num == 'Ace':
        return "🅰️"
    elif card_num == '2':
        return "2️⃣"
    elif card_num == '3':
        return "3️⃣"
    elif card_num == '4':
        return "4️⃣"
    elif card_num == '5':
        return "5️⃣"
    elif card_num == '6':
        return "6️⃣"
    elif card_num == '7':
        return "7️⃣"
    elif card_num == '8':
        return "8️⃣"
    elif card_num == '9':
        return "9️⃣"
    elif card_num == '10':
        return "🔟"
    elif card_num == 'Jack':
        return "🇯"
    elif card_num == 'Queen':
        return "🇶"
    elif card_num == 'King':
        return "🇰"

def dealer_draw(user_id:int,dealer_total:int):
    if dealer_total > 16:
        return
    elif dealer_total < 17:
        vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        suits = ['spades', 'clubs', 'hearts', 'diamonds']
        deck = list(itertools.product(vals, suits))
        random.shuffle(deck)
        db = client[CLIENT]
        collection = db["LiveBets"]
        userData = collection.find_one({"_id":user_id})
        dealer_cards = userData["dealer_cards"]
        dealer_cards.append(deck[0][0])
        print(dealer_cards)
        userData["dealer_cards"] = dealer_cards
        collection.replace_one({"_id":user_id}, userData)
        dealer_total = face(deck[0][0]) + dealer_total
        dealer_draw(user_id, dealer_total)

def player_draw (user_id:int):
    vals = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    suits = ['spades', 'clubs', 'hearts', 'diamonds']
    deck = list(itertools.product(vals, suits))
    random.shuffle(deck)
    db = client[CLIENT]
    collection = db["LiveBets"]
    userData = collection.find_one({"_id":user_id})
    player_cards = userData["player_cards"]
    player_cards.append(deck[0][0])
    userData["player_cards"] = player_cards
    collection.replace_one({"_id":user_id}, userData)

#------ Sync Command ------
#Global Sync CMD to load slash commands
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: Context):
	synced = await ctx.bot.tree.sync()
	await ctx.send(f"Synced {len(synced)} commands {'globally'}")


def log(user_name:str,user_id:int,msg:str):
    with open("log.txt", "w") as f:
    # Write some text to the file
        f.write(f"{user_name}:<{user_id}>: \n\t{msg}")

bot.run(TOKEN)
