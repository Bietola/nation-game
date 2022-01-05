#!/usr/bin/env python3

import json
import sys

world = json.loads(sys.stdin.read())

for nation in world:
    if not nation.get('Armies', None):
        nation['Armies'] = []
    nation['Armies'].append({
        'Owner': 'Natives',
        'Strength': nation['Price'],
        'Fighting': []
    })

print(json.dumps(world, indent=2))
