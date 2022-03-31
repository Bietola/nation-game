import operator as op
from lenses import lens
from collections import defaultdict

from world import *

def step(game, time_delta):
    world = game['world']

    # TODO
    tot_production = defaultdict(lambda: 0)
    for nat in game['world']:
        # NB. Chosen at random if two are the same (extremely rare anyway)
        # dom_pl = max(nat['Armies'], key=dict.get('Strength'))
        armies = nat['Armies']

        if len(armies) == 0:
            continue

        dom_pl = max(
            list(filter(
                lambda a: a['Owner'] != '_factories',
                armies,
            )),
            key=lambda a: a['Strength']
        )

        # TODO: Use unity properties
        if dom_pl['Owner'] in ['Natives', '_factories']:
            continue

        # TODO: Handle as error of `nation_occupation_perc` below
        tot_strength = sum(map(lambda a: a['Strength'], nat['Armies']))
        if tot_strength == 0:
            continue

        dom_perc = nation_occupation_perc(world, nat['Country Code'], dom_pl['Owner']).value
        if dom_perc >= 0.7:
            DAY = 60 * 60 * 24
            daily_occ_bonus = 85 * nat['Price'] / 20
            occ_bonus = (daily_occ_bonus / DAY) * time_delta
            factories_n = next(filter(
                    lambda a: a['Owner'] == '_factories',
                    armies
            ), {'Strength': 0})['Strength']
            tot_bonus = occ_bonus + ((factories_n * 0.1) / DAY)

            # TODO: Add advanced logger with verbosity options
            if tot_bonus > 0.0001:
                game['log'](f'DOM: {nat["Country Name"]}: {dom_pl["Owner"]}: {tot_bonus}')

            game['players'][dom_pl['Owner']]['points'] += tot_bonus
            tot_production[dom_pl['Owner']] += tot_bonus

    # Log total productions
    for pl, prod in tot_production.items():
        game['players'][pl]['production'] = prod
        game['log'](f'DOM: TOT: {pl}: {prod}')

    return game
