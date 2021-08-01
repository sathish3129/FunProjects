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

running_builder = []

if os.path.exists(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json') and os.path.isfile(
        Constant.APP_PATH.RESOURCE + '/coc_game_builder.json'):
    with open(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json') as builder_filehandler:
        # running_builder = json.load(builder_filehandler)
        pass
else:
    log.error(f'COC Builder DB {Constant.APP_PATH.RESOURCE}/coc_game_builder.json is missing')
    sys.exit(1)

for x in range(0,5):
    running_builder.append(
        {
            "Name": 'Builder ' + str(x+1),
            'Status': Constant.Builders.INACTIVE,
            "Item": "None",
            "Duration": "0:00:00",
            "start_time": datetime.now(tz=timezone.utc),
            "from_level": 0,
            "end_time": datetime.now(tz=timezone.utc),
            "Time_to_complete": datetime.now(tz=timezone.utc),

        }
    )



print(running_builder)

with open(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json', 'w') as json_filehandler:
    json.dump(running_builder, json_filehandler, default=datetime_serilizer, indent=4)

log.info('#' * 50)
log.info(yam('Done'))
log.info('#' * 50)
