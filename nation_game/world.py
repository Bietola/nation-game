from result import Err, Ok
import nation_game

def find_nation(world, nation_code):
    nation = filter(
        lambda nat: nat['Country Code'] == nation_code,
        world
    )
    nation = next(nation, None)

    if nation:
        return Ok(nation)

    nation = filter(
        lambda nat: nat['Country Name'].lower() == nation_code.replace('_', ' ').lower(),
        world
    )
    nation = next(nation, None)

    if not nation:
        return Err(f'{nation_code} is not a valid nation code')

    return Ok(nation)

def find_army(world, nation, owner):
    nation = find_nation(world, nation)
    if isinstance(nation, Err):
        return nation
    nation = nation.value
    
    armies = nation.get('Armies', [])

    army = filter(
        lambda army: army['Owner'] == owner,
        armies
    )
    army = next(army, None)
    if not army:
        armies.append({'Owner': owner, 'Strength': 0, 'Fighting': []})
        army = armies[-1]

    return Ok(army)

def nation_occupation_perc(world, nation_code, deploy_from):
    res = find_nation(world, nation_code)
    if isinstance(res, Err):
        return res
    nation = res.value

    res = find_army(world, nation_code, deploy_from)
    if isinstance(res, Err):
        return res
    army = res.value

    tot_strength = sum(map(
        lambda a: a['Strength'],
        filter(
            lambda a: a['Owner'] != '_factories',
            nation['Armies']
        )
    ))
    nation_game.g_db['log'](f'DB: {nation["Country Name"]}: {tot_strength}')

    if tot_strength == 0:
        return Ok(0)

    return Ok(army['Strength'] / tot_strength)
