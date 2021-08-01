#!/usr/bin/env python3

from logging.handlers import TimedRotatingFileHandler

import re
import os
import sys
import json
import logging

from datetime import datetime, timezone, timedelta
from dateutil.parser import parse

import Constant

# Initiate application
Constant.APP_PATH.BASEPATH = '/'.join((os.path.realpath(sys.argv[0]).split('\\')[0:-2]))
Constant.APP_PATH.NAME = os.path.realpath(sys.argv[0]).split('\\')[-1].split('.')[0]
log = logging.getLogger(Constant.APP_PATH.NAME)

for _dir in ('logs', 'resource'):
    _tmp_path = '/'.join((Constant.APP_PATH.BASEPATH, _dir))
    exec(f'Constant.APP_PATH.{_dir.upper()} = r\'{_tmp_path}\'')
    if not os.path.exists(_tmp_path):
        os.mkdir(_tmp_path)

handler = TimedRotatingFileHandler(
    '/'.join((Constant.APP_PATH.LOGS, Constant.APP_PATH.NAME + '.log')),
    when='midnight', backupCount=2)
formatter = logging.Formatter('%(asctime)s %(levelname)s : %(lineno)d : %(message)s')
handler.setFormatter(formatter)
handler.suffix = '%Y%m%d'
handler.extMatch = re.compile(r'^\d{8}$')
log.addHandler(handler)
log.setLevel(logging.INFO)


def datetime_serilizer(o):
    if isinstance(o, datetime):
        return o.__str__()


def yam(word):
    midway = 50 - (len(word) + 2)
    _miss_match = 0
    if midway % 2 != 0:
        _miss_match = 1
        midway -= 1
    midway = int(midway / 2)
    word = '#{0}{1}{2}#'.format(' ' * midway, word, ' ' * (midway + _miss_match))
    return word


log.info('#' * 50)
log.info(yam('Start'))
log.info('#' * 50)
itm = 0

hash_key = {
    'One': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five three': 5,
    'six four': 6
}
print('Chose the running item from above(1..n):')

l = list(enumerate(hash_key.keys()))
i = 0
print(l)
print(len(l))
print(min(6+2, len(l)))
while itm <= 0:
    print(l[i])
    for x in range(i, min(i+2, len(l))):
        print(l[x][0])
    i += 2
    if i < len(l) and i % 2 == 0:
        itm = int(input('chose:'))
    if i > len(l):
        break




log.info('#' * 50)
log.info(yam('Done'))
log.info('#' * 50)
