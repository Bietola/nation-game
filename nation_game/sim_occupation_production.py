import operator as op
from lenses import lens

def size_advantage_interleave(offender_size, opponents_size):
    # TODO: Use normal ditribution to reproduce function in `./notes/advanced-size-adv-interleave.png`
    # TODO: Or just use: `./notes/slightly-more-advanced-size-adv.png`
    return max(
        1,
        offender_size / opponents_size
    )

def step(game, time_delta):
    world = game['world']

    # TODO
    for nat in game['world']:
        # NB. Chosen at random if two are the same (extremely rare anyway)
        # dom_pl = max(nat['Armies'], key=dict.get('Strength'))
        armies = nat['Armies']

        if len(armies) == 0:
            continue

        dom_pl = max(armies, key=lambda a: a['Strength'])

        if dom_pl['Owner'] == 'Natives':
            continue

        dom_perc = dom_pl['Strength'] / sum(map(lambda a: a['Strength'], nat['Armies']))
        if dom_perc >= 0.7:
            DAY = 60 * 60 * 24
            daily_occ_bonus = nat['Price'] / 20
            occ_bonus = (daily_occ_bonus / DAY) * time_delta
            factories_n = next(filter(
                    lambda a: a['Owner'] == '_factories',
                    armies
            ), {'Strength': 0})['Strength']
            ind_bonus = 1 + factories_n / nat['Price']
            ind_bonus *= 1.5 if dom_perc > 0.95 else 1
            tot_bonus = occ_bonus * ind_bonus

            # TODO: Add advanced logger with verbosity options
            if tot_bonus > 0.0001:
                print(f'DOM: {nat["Country Name"]}: {dom_pl["Owner"]}: {tot_bonus}')

            # game['players'][dom_pl["Owner"]]['points'] += bonus

    return game
