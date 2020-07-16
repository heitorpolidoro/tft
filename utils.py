from champions import champions
from synergies import synergies


def calc_synergy(comp):
    synergy = {}
    for ch in comp:
        for syn in champions[ch]:
            synergy[syn] = synergy.get(syn, 0) + 1
    return synergy


def validate_synergy(synergy):
    remaining = 0
    for syn, count in synergy.items():
        if count not in synergies[syn]:
            for s in synergies[syn]:
                diff = count - s
                # print(diff, count, s, syn)
                if diff < 0:
                    remaining += -diff
                    break
        # print('syn', syn, count, count in synergies[syn])
        # if count not in synergies[syn]:
        #     return False
    return remaining / 2


def get_comp(comp):
    champions_list = sorted(champions.keys())
    return [champions_list[c - 1] for c in comp if c > 0]


def next_comp(comp, i=0):
    comp = comp[:]
    if i == len(comp):
        return None
    comp[i] = comp[i] + 1
    clean_comp = [c for c in comp if c > 0]
    while (comp.count(comp[i]) > 1 or clean_comp != sorted(clean_comp)) and comp[i] <= len(champions):
        comp[i] = comp[i] + 1
        clean_comp = [c for c in comp if c > 0]

    if comp[i] > len(champions):
        comp[i] = 1
        while comp.count(comp[i]) > 1 and comp[i] <= len(champions):
            comp[i] = comp[i] + 1
        return next_comp(comp, i + 1)

    return comp


def comp_size(comp):
    return len(comp) - comp.count(0)
