from nation_game.bot import flush_db


# NB. Not really a simulation... just saves the game state to disk
def step(game, time_delta):
    # Save game
    print('Saving game...')
    flush_db()
    print('Game saved')

    return game
