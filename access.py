#!/usr/bin/python3

import argparse
import requests
import sys
from datetime import datetime
from datetime import timedelta

parser = argparse.ArgumentParser()

parser.add_argument('command', help='units, posters, items, floor, last, holdings, inspect')
parser.add_argument('-a', type=str, help='Address to get holdings for')
parser.add_argument('-i', type=str, help="Filter for units containing items (samurai, astro, 'Black desk', etc)")
parser.add_argument('-t', type=int, help='Filter for units containing T number of items')
parser.add_argument('-m', type=str, help='Filter for units by Mikka position (pc, wine, pizza, fh, ft, by, bs, vr)')
parser.add_argument('-l', action='store_true', help='Show only results that have listings')
parser.add_argument('-g', action='store_true', help='Show only results that have known glitches')
parser.add_argument('-d', type=int, help='Sort by date minted 0 - ascending, or 1 - descending')
parser.add_argument('-p', type=int, help='Sort by price 0 - ascending, or 1 - descending')
parser.add_argument('-n', type=int, help='Sort by name 0 - ascending, or 1 - descending')
parser.add_argument('-o', type=int, help='Minted in the last O hours')
parser.add_argument('-r', type=int, help='Max number of results to return')
parser.add_argument('-b', action='store_true', help='Show only units with no boxes')
parser.add_argument('-x', type=str, help='Filter by poster number')
parser.add_argument('-f', type=int, help='Number of item floor prices to show (1 - 95)')
parser.add_argument('-u', type=str, help='Units to inspect, e.g. 50000,42069,etc')


args = parser.parse_args()

def get_units():
    print('  Getting units...', end='')
    res = requests.get('https://alphastaking.com/ccassets/units')
    if res.status_code == 200:
        print('done')
        return res.json()
    else:
        print('failed -', res.status_code, '\n')
        sys.exit(1)

def get_items():
    print('  Getting items...', end='')
    res = requests.get('https://alphastaking.com/ccassets/items')
    if res.status_code == 200:
        print('done')
        return res.json()
    else:
        print('failed -', res.status_code, '\n')
        sys.exit(1)

def get_posters():
    print('  Getting posters...', end='')
    res = requests.get('https://alphastaking.com/ccassets/posters')
    if res.status_code == 200:
        print('done')
        return res.json()
    else:
        print('failed -', res.status_code, '\n')
        sys.exit(1)

def get_holdings(addr):
    print(f'  Getting holdings for {addr}...', end='')
    res = requests.get(f'https://api.pool.pm/wallet/{addr}')
    if res.status_code == 200:
        print('done')
        return res.json()
    else:
        print('failed -', res.status_code, '\n')
        sys.exit(1)

def filter_l(results, reverse):
        print('\n  Filtering for listings only', end=' - ')
        results = [r for r in results if r['listing'] != None]
        results = [r for r in results if not r['listing']['sold']]
        print('found', len(results))
        if reverse != None:
            results = sorted(results, key=lambda k: k['listing']['price'], reverse=reverse)
        else:
            results = sorted(results, key=lambda k: k['listing']['price'])
        return results

def filter_o(results, hours):
        print(f"\n  Filtering for results minted in the last {hours} hours", end=' - ')
        key = 'unit'
        if 'poster' in results[0].keys():
            key = 'poster'
        results = [r for r in results if r[key]['minted'] != None] 
        results = [r for r in results if (datetime.utcnow() - datetime.strptime(r[key]['minted'], '%Y-%m-%dT%H:%M:%S') < timedelta(hours=hours))]
        results = sorted(results, key=lambda k: k[key]['minted'])
        print('found', len(results))
        return results

def print_results(results, results_n):
    print('')
    if len(results) == 0:
        sys.exit(0)
    if results_n == None:
        results_n = 0
    result_n = 0
    if results_n > 0:
        print(f'  Limiting to {results_n} reults\n')
    s = 21
    if [r for r in results if 'poster' in r.keys()] != []:
        s = 25
    print(f"  Name{' '*(s-2)}Minted{' '*16}Price{' '*11}Listing")
    for r in results:
        key = 'unit'
        if 'poster' in r.keys():
            key = 'poster'
        name = F"{r[key]['name']}"
        print(f"  {name}{' '*(s-len(name))}  {r[key]['minted'].replace('T',' ')}", end='')
        if r['listing'] != None:
            price = f"{r['listing']['price']/1000000:,}"
            print(f"   {price}{' '*(14-len(price))}  https://cnft.io/token.php?id={r['listing']['id']}")
        else:
            print('')
        result_n += 1
        if result_n == results_n:
            break

mikkas = {'vr': {'name': 'VR', 'key': 'vr'},
        'pizza': {'name': 'Pizza', 'key': 'pizza_sh_sp'}, 
        'fh': {'name': 'Floor Hoodie', 'key': 'floor_r_sh_hd'},
        'ft': {'name': 'Floor Tablet', 'key': 'floor_d_sh_sp'},
        'by': {'name': 'Bed Yukata', 'key': 'bed_lh_yk'},
        'bs': {'name': 'Bed Sport Outfit', 'key': 'bed_sh_sp'},
        'wine': {'name': 'Wine', 'key': 'wine_sh_sp'},
        'pc': {'name': 'PC', 'key': 'pc'}}

print('')

if args.command == 'units':
    units = get_units()
    items = get_items()
    units_n = units['total']
    units = [units['units'][u] for u in units['units']]
    items = [[i, items['items'][i]] for i in items['items']]

    print('\n  Total units:', units_n)

    results = []
    if args.i != None:
        args_i = args.i.split(',')
        items_s = []
        for arg in args_i:
            try:
                items_s.append([i for i in items if arg in i[1]['name']][0])
            except:
                print(f"\n  Failed to find item \"{arg}\", check spelling and try again.")
                print("  Run \"./access.py items\" for the complete item list\n")
                sys.exit(1)
        print('\n  Searching for units with:')
        for i in items_s:
            print('   ', i[1]['name'])
        for u in units:
            matches = 0
            for i in items_s:
                if i[0] in u['unit']['contents']:
                    matches += 1
                if matches == len(items_s):
                    results.append(u)
                    break
        print('\n  Found:', len(results))
    else:
        results = units

    results_m = []
    if args.m != None:
        print('\n  Filtering for Mikka:', mikkas[args.m]['name'], end=' - ')
        for r in results:
            if r['unit']['mikka'] != None:
                if r['unit']['mikka']['position'] == mikkas[args.m]['key']:
                    results_m.append(r)
        results = results_m
        print('found', len(results))
   
    if args.n != None:
        results = sorted(results, key=lambda k: k['unit']['name'], reverse=args.n)
    else:
        results = sorted(results, key=lambda k: k['unit']['name'])

    if args.t != None:
        print(f"\n  Filtering for units with {args.t} items", end=' - ')
        results = [r for r in results if len(r['unit']['contents']) + 2 > args.t]
        print('found', len(results))

    if args.o != None:
        results = filter_o(results, args.o)

    if args.l:
        results = filter_l(results, args.p)

    if args.g:
        print("\n  Filtering for results with known glitches", end=' - ')
        results = [r for r in results if r['unit']['glitch'] != None]
        print('found', len(results))

    if args.d != None:
        results = sorted(results, key=lambda k: k['unit']['minted'], reverse=args.d)

    if args.b:
        print('\n  Removing those pesky boxes', end=' - ')
        results = [r for r in results if '92' not in r['unit']['contents'] and '85' not in r['unit']['contents']]
        print('found', len(results))

    print_results(results, args.r)

elif args.command == 'posters':
    posters = get_posters()
    posters_n = posters['total']
    posters = [posters['posters'][p] for p in posters['posters']]
    
    print('\n  Total posters:', posters_n)

    results = []
    if args.x != None:
        args_x = args.x.split(',')
        print('\n  Searching for poster number:', ', '.join(args_x))
        for p in posters:
            for arg in args_x:
                if p['poster']['name'][17:18] == arg:
                    results.append(p)
        print('\n  Found:', len(results))
    else:
        results = posters

    if args.n != None:
        results = sorted(results, key=lambda k: k['poster']['name'], reverse=args.n)
    else:
        results = sorted(results, key=lambda k: k['poster']['name'])

    if args.o != None:
        results = filter_o(results, args.o)

    if args.l:
        results = filter_l(results, args.p)

    if args.d != None:
        results = sorted(results, key=lambda k: k['poster']['minted'], reverse=args.d)

    print_results(results, args.r)

elif args.command == 'items':
    items = get_items()
    items = [[i, items['items'][i]] for i in items['items']]
    items = sorted(items, key=lambda k: int(k[0]))

    if args.r != None:
        results_n = args.r
    else:
        results_n = 0

    print('')
    result_n = 0
    print(f"  No   Item{' '*31}Instances  Rarity")
    for i in items:
        n = f"{i[1]['name']}"
        s = i[1]['instances']
        print(f"  {i[0]}{' '*(3-len(i[0]))}  {n}{' '*(33-len(n))}  {s}{' '*(11-len(s))}{int(s)*100/50000:.2f}%")
        result_n += 1
        if result_n == results_n:
            break

elif args.command == 'last':
    units = get_units()
    posters = get_posters()
    results = [[units['units'][u]['unit']['minted'], units['units'][u]] for u in units['units']] + \
        [[posters['posters'][p]['poster']['minted'], posters['posters'][p]] for p in posters['posters']]

    print('\n  Total mints:', len(results))

    if args.o != None:
        args_o = args.o
    else:
        args_o = 24

    results = [r for r in results if (datetime.utcnow() - datetime.strptime(r[0], '%Y-%m-%dT%H:%M:%S') < timedelta(hours=args_o))]

    print(f'\n  Mints in the last {args_o} hours:', len(results))

    if args.n != None:
        results = sorted(results, key=lambda k: k[0], reverse=args.n)
    else:
        results = sorted(results, key=lambda k: k[0])

    if args.l:
        print('\n  Filtering for listings only', end=' - ')
        results = [r for r in results if r[1]['listing'] != None]
        results = [r for r in results if not r[1]['listing']['sold']]
        print('found', len(results))
        if args.p != None:
            results = sorted(results, key=lambda k: k[1]['listing']['price'], reverse=args.p)
        else:
            results = sorted(results, key=lambda k: k[1]['listing']['price'])
 
    if args.d != None:
        results = sorted(results, key=lambda k: k[0], reverse=args.d)
    else:
        results = sorted(results, key=lambda k: k[0], reverse=1)

    results = [r[1] for r in results]

    print_results(results, args.r)

elif args.command == 'floor':
    units = get_units()
    posters = get_posters()
    items = get_items()

    print('\n  Total units:', units['total'])
    print('\n  Total posters:', posters['total'])

    if args.f == None:
        args_f = 10
    elif args.f >= 1 and args.f <= 95:
        args_f = args.f
    else:
        args_f = 10

    units = [units['units'][u] for u in units['units']]
    posters = [posters['posters'][p] for p in posters['posters']]
    items = [[i, items['items'][i], []] for i in items['items']]
    items = sorted(items, key=lambda k: int(k[0]))[:args_f]

    print(f"\n  Item {' '*29}Minted       %        Price")
    for i in items:
        for u in units:
            if i[0] in u['unit']['contents']:
                i[2].append(u)
        n = len(i[2])
        floor = [u for u in i[2] if u['listing'] != None]
        if len(floor) > 0:
            floor = sorted(floor, key=lambda k: k['listing']['price'])
            floor = f"{floor[0]['listing']['price']/1000000:,}"
        else:
            floor = 'N/A'
        minted = f"{n}/{i[1]['instances']}"
        pct = f"{n*100/int(i[1]['instances']):.2f}%"
        print(f"  {i[1]['name']}{' '*(34-len(i[1]['name']))}{minted}{' '*(13-len(minted))}{pct}{' '*(9-len(pct))}{floor}")

    print(f"\n  Mikka {' '*11} Instances   Distribution   Price")
    units_m = [u for u in units if u['unit']['mikka'] != None]
    total_m = len(units_m)
    positions = {'vr': ['VR', []], 'pizza_sh_sp': ['Pizza', []], 'floor_r_sh_hd': ['Floor Hoodie', []],
            'floor_d_sh_sp': ['Floor Tablet', []], 'bed_lh_yk': ['Bed Yukata', []], 'bed_sh_sp': ['Bed Sport Outfit', []],
            'wine_sh_sp': ['Wine', []], 'pc': ['PC', []]}
    for p in positions:
        for m in units_m:
            if p == m['unit']['mikka']['position']:
                positions[p][1].append(m)
    positions = {k: v for k, v in sorted(positions.items(), key=lambda u: len(u[1][1]))}
    for p in positions:
        n = len(positions[p][1])
        d = f"{n*100/total_m:.2f}%"
        floor = [u for u in positions[p][1] if u['listing'] != None]
        if len(floor) > 0:
            floor = sorted(floor, key=lambda k: k['listing']['price'])
            floor = f"{floor[0]['listing']['price']/1000000:,}"
        else:
            floor = 'N/A'
        print(f"  {positions[p][0]}{' '*(18-len(positions[p][0]))}{n}{' '*(12-len(str(n)))}{d}{' '*(15-len(d))}{floor}")

    print(f"\n  Poster {' '*14}Minted   %        Price")
    posters_s = {'CardanoCityPoster1': [], 'CardanoCityPoster2': [], 'CardanoCityPoster3': [],
            'CardanoCityPoster4': [], 'CardanoCityPoster5': [], 'CardanoCityPoster6': []}
    for s in posters_s:
        for p in posters:
            if s in p['poster']['name']:
                posters_s[s].append(p)
        n = len(posters_s[s])
        floor = [x for x in posters_s[s] if x['listing'] != None]
        if len(floor) > 0:
            floor = sorted(floor, key=lambda k: k['listing']['price'])
            floor = f"{floor[0]['listing']['price']/1000000:,}"
        else:
            floor = 'N/A'
        if s == 'CardanoCityPoster6':
            pct = f"{n*100/5:.2f}%"
            print(f"  {s}    {n}/5     {pct}{' '*(9-len(pct))}{floor}")
        else:
            pct = f"{n*100/50:.2f}%"
            print(f"  {s}   {n}/50    {pct}   {floor}")

elif args.command == 'holdings':
    if args.a == None:
        print('  Please specify an address with "-a"\n')
        sys.exit(1)

    units = get_units()
    posters = get_posters()
    items = get_items()
    holdings = get_holdings(args.a)

    assets = [t['metadata']['name'] for t in holdings['tokens'] if t['policy'] == 'a5425bd7bc4182325188af2340415827a73f845846c165d9e14c5aed']
    units = [units['units'][u] for u in units['units'] if units['units'][u]['unit']['name'] in assets]
    posters = [posters['posters'][p] for p in posters['posters'] if posters['posters'][p]['poster']['name'] in assets]

    print(f"\n  Found {len(assets)} CardanoCity assets")

    if args.g:
        print("\n  Filtering for results with known glitches", end=' - ')
        units = [u for u in units if u['unit']['glitch'] != None]
        print('found', len(units))

    if len(posters) > 0:
        print('')
        for p in posters:
            print(f"  {p['poster']['name']}")

    if len(units) > 0:
        print('')
        for u in units:
            print(f"  {u['unit']['name']}", end='  ')
            for i in sorted(u['unit']['contents'], key=lambda k: int(k))[:3]:
                item = items['items'][i]['name']
                print(f"{item}", end=f"{' '*(34-len(item))}")
            print('')

elif args.command == 'inspect':
    if args.u == None:
        print('  Please specify units with "-u"\n')
        sys.exit(1)

    args_u = args.u.split(',')
    units = get_units()
    items = get_items()

    units = [units['units'][u] for u in units['units'] if units['units'][u]['unit']['name'][-5:] in args_u]
    mikkas = {v['key']: v['name'] for v in mikkas.values()}

    for u in units:
        if u['listing'] != None:
            listing = f"{u['listing']['price']/1000000:,} - https://cnft.io/token.php?id={u['listing']['id']}"
        else:
            listing = 'N/A'
        u = u['unit']
        if u['glitch'] != None:
            glitch = u['glitch']['item']
        else:
            glitch = 'N/A'
        print(f"\n  Name:    {u['name']}\
                \n  Minted:  {u['minted']}\
                \n  Base:    {u['base']}\
                \n  Poster:  {u['poster']}\
                \n  Value:   {int(u['value']):,}\
                \n  Mikka:   {mikkas[u['mikka']['position']]}\
                \n  Glitch:  {glitch}\
                \n  Listing: {listing}\
                \n  Items:   {len(u['contents'])+2}\
                \n\
                \n  Item{' '*30}Rarity")
        for i in sorted(u['contents'], key=lambda k: int(k)):
            item = items['items'][i]
            print(f"  {item['name']}{' '*(34-len(item['name']))}{int(item['instances'])*100/50000:.2f}%")

else:
    parser.print_help()

print('')
