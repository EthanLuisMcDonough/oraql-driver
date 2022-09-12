#!/usr/bin/python2
import sys

if len(sys.argv) < 2:
    sys.exit(1)

stats = {}
IsStats = -1
with open(sys.argv[1], 'r') as fd:
    for line in fd:
        # print(IsStats, line)
        if '... Statistics Collected ...' in line:
            IsStats = 3
            continue
        if IsStats == -1:
            continue
        line = line.strip()
        if IsStats == 2 and not line:
            IsStats = 0
            continue
        if IsStats > 0:
            IsStats -= 1
            continue
        if not line:
            IsStats = -1
            continue
        idx = line.index(' ')
        num = int(line[:idx])
        line = line[idx:].strip()
        opt = line[:line.index(' ')].strip()
        key = line[line.index(' '):].strip()
        key = (opt, key)
        # print(key)
        if key in stats:
            stats[key] += num
        else:
            stats[key] = num

keys = stats.keys()
keys.sort()
for key in keys:
    print('%10i %s %s' % (stats[key], key[0], key[1]))
