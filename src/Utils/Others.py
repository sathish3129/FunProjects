#!/usr/bin/env python3


def Yam(word):
    midway = 50 - (len(word) + 2)
    _miss_match = 0
    if midway % 2 != 0:
        _miss_match = 1
        midway -= 1
    midway = int(midway/2)
    word = '#{0}{1}{2}#'.format(' ' * midway,word,' ' * (midway+_miss_match))
    return word