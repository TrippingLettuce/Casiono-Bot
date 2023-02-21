import random

def roulette_blackorred(bet_color):
    random_num = random.randint(0, 1)
    if bet_color == 'red' and random_num == 0:
        return True
    elif bet_color == 'black' and random_num == 1:
        return True
    else:
        return False

import random

def dice_game(chance_to_land:int):
    # Take user input for the chance to land    
    # Roll two dice
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    # Check if user guess is correct
    if total == chance_to_land:
        return True, total
    else:
        return False, total

