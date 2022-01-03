def size_advantage_interleave(offender_size, opponents_size):
    # TODO: Use normal ditribution to reproduce function in `./notes/advanced-size-adv-interleave.png`
    # TODO: Or just use: `./notes/slightly-more-advanced-size-adv.png`
    return min(
        1,
        offender_size / opponents_size
    )

def step(world, time_delta):
    world1 = world

    # DB
    for nation in world1:
        for army in nation.get('Armies', []):
            # TODO: Edge cases (opp_name not found; more than one)
            opponents = list(map(
                lambda opp_name: next(filter(
                    lambda army: army['Owner'] == opp_name,
                    nation['Armies']
                )),
                army['Fighting']
            ))

            opponents_power = sum([opp['Strength'] for opp in opponents])
            offender_power = army['Strength']

            # e.g. power_inter_func(100, 25 + 25) -> 2
            size_advantage = size_advantage_interleave(
                offender_power, opponents_power
            )

            for opp in opponents:
                opp['Strength'] -= (size_advantage / len(opponents)) * time_delta

    return world1

#########
# Tests #
#########

# from pathlib import Path
# import json

# world = json.loads(
#     (Path(__file__).parent / 'assets/test/2-vs-1.json').open().read()
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
