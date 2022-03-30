def size_advantage_interleave(offender_size, opponents_size):
    # TODO: Use normal ditribution to reproduce function in `./notes/advanced-size-adv-interleave.png`
    # TODO: Or just use: `./notes/slightly-more-advanced-size-adv.png`
    return max(
        1,
        offender_size / opponents_size
    )

def step(game, time_delta):
    world = game['world']

    # Kill armies with negative strength
    for nation in world:
        nation['Armies'] = list(filter(
            lambda army: army['Strength'] > 0,
            nation['Armies']
        ))

        for army in nation['Armies']:
            army['Fighting'] = list(set(filter(
                lambda opp: opp in set(map(lambda x: x['Owner'], nation['Armies'])),
                army['Fighting']
            )))

    # Simulate war damage
    for nation in world:
        for army in nation['Armies']:
            # TODO: Edge cases (opp_name not found; more than one)
            opponents = list(map(
                lambda opp_name: next(filter(
                    lambda army: army['Owner'] == opp_name,
                    nation['Armies']
                )),
                army['Fighting']
            ))

            if len(opponents) == 0:
                continue

            opponents_power = sum([opp['Strength'] for opp in opponents])
            offender_power = army['Strength']

            # e.g. power_inter_func(100, 25 + 25) -> 2
            size_advantage = size_advantage_interleave(
                offender_power, opponents_power
            )

            for opp in opponents:
                damage = (size_advantage / len(opponents)) * time_delta
                game['log'](f'WAR: {army["Owner"]} hurts {opp["Owner"]} (-{damage})') # TODO
                opp['Strength'] -= damage

    # Native armies AI: attack EVERYONE
    for nation in world:
        natives = next(filter(
            # TODO: Use AI field instead
            lambda army: army['Owner'] == 'Natives',
            nation['Armies']
        ), None)

        if not natives:
            continue

        natives['Fighting'] = list(set(map(
            lambda army: army['Owner'],
            nation['Armies']
        )).difference({'Natives'}))

    return game

#########
# Tests #
#########

# from pathlib import Path
# import json

# world = json.loads(
#     (Path(__file__).parent / 'assets/test/2-vs-1.json').open(encoding='utf8').read()
# )

# print('before')
# print(json.dumps(
#     world,
#     sort_keys=True,
#     indent=4
# ))

# print('after')
# print(json.dumps(
#     step(world, 50),
#     sort_keys=True,
#     indent=4
# ))
