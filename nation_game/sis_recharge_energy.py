from nation_game import flush_db


# NB. Recharges the energy of players
def step(game, time_delta):
    if (datetime.now() - game['day-begin-t']) > datetime.timedelta(days=1):
        game['day-begin-t'] = datetime.timedelta(days=1)
        game['players'] = bind(game['players']).Values()['solo_energy'].modify(lambda x: x/2)
        game['players'] = bind(game['players']).Values()['battle_energy'].modify(lambda x: x/2)
    # Save game
    print('Saving game...')
    flush_db()
    print('Game saved')

    return game
