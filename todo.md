1. Separate bot in two branches so that one can be kept going at all time
2. Make token for test bot so that [...]
3. Think about decoupling game from telegram?

4. Think about format to save nation data
5. Make simulation of 1 day war between two native nations
    - Use it to tweak war duration
6. Add simple `deploy` mechanics
7. ...

## Scratch

### Armies Example

Armies [
    {'Owner': 'Natives', 'Strength': 1000, 'Fighting': ['Davide', 'Daniele']},
    {'Owner': 'Davide', 'Strength': 100, 'Fighting': ['Natives']},
    {'Owner': 'Daniele', 'Strength': 75, 'Fighting': ['Natives']}
]

(armies, delta) ->
fighters = armies.map([Owner, Strength])
for fgt in fighters:
    opponents = fgt[Fighting]
    opps_power = opponents.map([Strength]).sum()
    fgt_power = fgt[Strength]
    death_factor = power_inter_func(fgt_power, opps_power)
        e.g. power_inter_func(100, 25 + 25) -> 2
    deaths = death_factor * delta
    fgt[Strength] -= deaths